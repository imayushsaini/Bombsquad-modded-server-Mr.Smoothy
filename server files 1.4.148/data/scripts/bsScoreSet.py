import bs
import bsUtils
import bsSpaz
import weakref
import math
import random
import bsInternal

class PlayerScoredMessage(object):
    """
    category: Message Classes

    Informs a bs.Activity that a player scored.

    Attributes:

       score
          The score value.
    """
    def __init__(self,score):
        'Instantiate with the given values'
        self.score = score

class ScoreSet(object):
    """ Manages individual score keeping for players; provides persistant scores and some other goodies.
    Players are indexed here by name so that if a player leaves and comes back he'll keep the same score """

    class _Player(object):
        def __init__(self, name, nameFull, player, scoreSet):
            self.name = name
            self.nameFull = nameFull
            self.score = 0
            self.accumScore = 0
            self.killCount = 0
            self.accumKillCount = 0
            self.killedCount = 0
            self.accumKilledCount = 0
            self._multiKillTimer = None
            self._multiKillCount = 0
            self._scoreSet = weakref.ref(scoreSet)
            self._associateWithPlayer(player)

        def getTeam(self):
            return self.team()

        def getPlayer(self):
            return self._player

        def getName(self, full=False):
            return self.nameFull if full else self.name

        def getIcon(self):
            return self.lastPlayer.getIcon()

        def getSpaz(self):
            if self._spaz is None: return None
            return self._spaz()

        def cancelMultiKillTimer(self):
            self._multiKillTimer = None

        def getActivity(self):
            try: return self._scoreSet()._activity()
            except Exception: return None

        def _associateWithPlayer(self, player):
            self.lastPlayer = player
            self._player = player
            self.team = weakref.ref(player.getTeam())
            self.character = player.character
            self._spaz = None
            self.streak = 0
            
        def _endMultiKill(self):

            self._multiKillTimer = None
            self._multiKillCount = 0

        def submitKill(self,showPoints=True):
            self._multiKillCount += 1

            if self._multiKillCount == 1:
                score = 0
                name = None
            elif self._multiKillCount == 2:
                score = 20
                name = bs.Lstr(resource='twoKillText')
                color=(0.1,1.0,0.0,1)
                scale = 1.0
                delay = 0
                sound = self._scoreSet()._orchestraHitSound
            elif self._multiKillCount == 3:
                score = 40
                name = bs.Lstr(resource='threeKillText')
                color=(1.0,0.7,0.0,1)
                scale = 1.1
                delay = 300
                sound = self._scoreSet()._orchestraHitSound2
            elif self._multiKillCount == 4:
                score = 60
                name = bs.Lstr(resource='fourKillText')
                color=(1.0,1.0,0.0,1)
                scale = 1.2
                delay = 600
                sound = self._scoreSet()._orchestraHitSound3
            elif self._multiKillCount == 5:
                score = 80
                name = bs.Lstr(resource='fiveKillText')
                color=(1.0,0.5,0.0,1)
                scale = 1.3
                delay = 900
                sound = self._scoreSet()._orchestraHitSound4
            else:
                score = 100
                name = bs.Lstr(resource='multiKillText',subs=[('${COUNT}',str(self._multiKillCount))])
                color=(1.0,0.5,0.0,1)
                scale = 1.3
                delay = 1000
                sound = self._scoreSet()._orchestraHitSound4

            def _apply(name,score,showPoints,color,scale,sound):

                # only award this if they're still alive and we can get their pos
                try: ourPos = self.getSpaz().node.position
                except Exception: return

                # jitter position a bit since these often come in clusters
                ourPos = (ourPos[0]+(random.random()-0.5)*2.0,
                          ourPos[1]+(random.random()-0.5)*2.0,
                          ourPos[2]+(random.random()-0.5)*2.0)
                activity = self.getActivity()
                if activity is not None:
                    bsUtils.PopupText(
                        # (('+'+str(score)+' ') if showPoints else '')+name,
                        bs.Lstr(value=(('+'+str(score)+' ') if showPoints else '')+'${N}',subs=[('${N}',name)]),
                        color=color,
                        scale=scale,
                        position=ourPos).autoRetain()
                bs.playSound(sound)

                self.score += score
                self.accumScore += score

                # inform a running game of the score
                if score != 0 and activity is not None:
                    activity.handleMessage(PlayerScoredMessage(score=score))

            if name is not None:
                bs.gameTimer(300+delay,bs.Call(_apply,name,score,showPoints,color,scale,sound))

            # keep the tally rollin'...
            # set a timer for a bit in the future
            self._multiKillTimer = bs.Timer(1000,self._endMultiKill)

        
    def __init__(self):
        self._activity = None
        self._players = {}

    def setActivity(self,activity):
        self._activity = None if activity is None else weakref.ref(activity)

        # load our media into this activity's context
        if activity is not None:
            if activity.isFinalized():
                bs.printError('unexpected finalized activity')
            with bs.Context(activity): self._loadMedia()
        
    def _loadMedia(self):
        self._orchestraHitSound = bs.getSound('orchestraHit')
        self._orchestraHitSound2 = bs.getSound('orchestraHit2')
        self._orchestraHitSound3 = bs.getSound('orchestraHit3')
        self._orchestraHitSound4 = bs.getSound('orchestraHit4')
        
    def reset(self):
        # just to be safe, lets make sure no multi-kill timers are gonna go off
        # for no-longer-on-the-list players
        for p in self._players.values(): p.cancelMultiKillTimer()
        self._players = {} # our dict of players indexed by name

    # for things like per-round sub-scores..
    def resetAccum(self):
        for p in self._players.values():
            p.cancelMultiKillTimer()
            p.accumScore = 0
            p.accumKillCount = 0
            p.accumKilledCount = 0
            p.streak = 0

    def registerPlayer(self,player):
        name = player.getName()
        nameFull = player.getName(full=True)
        try:
            # if the player already exists, update his character and such as it may have changed
            self._players[name]._associateWithPlayer(player)
        except Exception: p = self._players[name] = self._Player(name,nameFull,player,self)

    def getValidPlayers(self):
        validPlayers = {}

        # go through our player records and return ones whose player id still corresponds to a player with that name
        for pName,p in self._players.items():
            try: exists = (p.lastPlayer.exists() and p.lastPlayer.getName() == pName)
            except Exception: exists = False
            if exists:
                validPlayers[pName] = p
        return validPlayers

    def _getSpaz(self,player):
        p = self._players[player.getName()]
        # this is a weak-ref
        if p._spaz is None: return None
        return p._spaz()

    def playerGotNewSpaz(self,player,spaz):
        p = self._players[player.getName()]
        if p.getSpaz() is not None: raise Exception("got 2 playerGotNewSpaz() messages in a row without a lost-spaz message")
        p._spaz = weakref.ref(spaz)

    def playerGotHit(self,player):
        p = self._players[player.getName()]
        p.streak = 0

    def playerScored(self,player,basePoints=1,target=None, kill=False, victimPlayer=None,scale=1.0,color=None,title=None,screenMessage=True,display=True,importance=1,showPoints=True,bigMessage=False):
        """ register a score for the player; return value is actual score with multipliers and such factored in """

        name = player.getName()
        p = self._players[name]

        # if title is None: title = ''

        if kill: p.submitKill(showPoints=showPoints)

        displayColor = (1,1,1,1)

        if color is not None: displayColor = color
        elif importance != 1:
            displayColor = (1.0,1.0,0.4,1)
        points = basePoints
        exc = ''

        # if they want a big announcement, throw a zoom-text up there
        if display and bigMessage:
            try:
                activity = self._activity()
                if activity:
                    nameFull = player.getName(full=True,icon=False)
                    activity.showZoomMessage(bs.Lstr(resource='nameScoresText',subs=[('${NAME}',nameFull)]),color=bsUtils.getNormalizedColor(player.getTeam().color))
            except Exception,e:
                print 'Exception showing bigMessage',e

        # if we currently have a spaz, pop up a score over it
        if display and showPoints:
            try: ourPos = p.getSpaz().node.position
            except Exception: ourPos = None
            if ourPos is not None:
                if target is None: target = ourPos

                # if display-pos is *way* lower than us, raise it up
                # (so we can still see scores from dudes that fell off cliffs)
                displayPos = (target[0], max(target[1], ourPos[1]-2.0), min(target[2], ourPos[2]+2.0))

                    # bs.printError('ignoring title arg in playerScored:',title)
                # if type(title) != str or title != '': title = ' '+title
                    
                activity = self._activity()
                if activity is not None:
                    if title is not None:
                        s = bs.Lstr(value='+${A} ${B}',subs=[('${A}',str(points)),('${B}',title)])
                    else:
                        s = bs.Lstr(value='+${A}',subs=[('${A}',str(points))])
                    # bsUtils.PopupText('+'+str(points)+title,
                    bsUtils.PopupText(s,
                                      color=displayColor,
                                      scale=1.2*scale,
                                      position=displayPos).autoRetain()
                    
        # tally kills
        if kill:
            p.accumKillCount += 1
            p.killCount += 1

        # report non-kill scorings
        try:
            if screenMessage and not kill:
                bs.screenMessage(bs.Lstr(resource='nameScoresText',subs=[('${NAME}',name)]),
                                 top=True,color=player.color,
                                 image=player.getIcon())
        except Exception,e: print 'Error announcing score:',e
            
        p.score += points
        p.accumScore += points

        # inform a running game of the score
        if points != 0:
            activity = self._activity() if self._activity is not None else None
            if activity is not None:
                activity.handleMessage(PlayerScoredMessage(score=points))

        return points
        
    def playerLostSpaz(self, player, killed=False, killer=None):
        name = player.getName()
        p = self._players[name]
        p._spaz = None
        p.streak = 0

        if killed:
            p.accumKilledCount += 1
            p.killedCount += 1
        try:
            if killed and bs.getActivity().announcePlayerDeaths:

                if killer == player:
                    bs.screenMessage(bs.Lstr(resource='nameSuicideKidFriendlyText' if bsInternal._getSetting('Kid Friendly Mode') else 'nameSuicideText',subs=[('${NAME}',name)]),
                                     top=True,color=player.color,image=player.getIcon())
                elif killer is not None:
                    if killer.getTeam() == player.getTeam():
                        bs.screenMessage(bs.Lstr(resource='nameBetrayedText',subs=[('${NAME}',killer.getName()),('${VICTIM}',name)]),
                                         top=True,color=killer.color,image=killer.getIcon())
                    else:
                        bs.screenMessage(bs.Lstr(resource='nameKilledText',subs=[('${NAME}',killer.getName()),('${VICTIM}',name)]),
                                         top=True,color=killer.color,image=killer.getIcon())
                else:
                    bs.screenMessage(bs.Lstr(resource='nameDiedText',subs=[('${NAME}',name)]),
                                     top=True,color=player.color,image=player.getIcon())
        except Exception,e:
            bs.printException('Error announcing kill')
