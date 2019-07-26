#Musical Flags

import bs
import random
import math
import bsVector
import bsUtils
from math import sin, cos, degrees

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [MusicalFlags]

def bsGetLevels():
    return [bs.Level('Musical Flags Beta',
                     displayName='${GAME}',
                     gameType=MusicalFlags,
                     settings={},
                     previewTexName='courtyardPreview')]

class MusicalFlags(bs.TeamGameActivity):

    tips = ['Though it seems that the flags to the sides are closer,\nthey are all the same distance from you.',
            'You can always pick up your opponent to keep them from scoring.',
            'If a player leaves, there would be enough flags for everyone\nso the next round starts automatically.',
            'RUN!',
            'If you accidentally run off a cliff, no worries.\nYou respawn!']
    
    @classmethod
    def getName(cls):
        return "Musical Flags"

    @classmethod
    def getDescription(cls, sessionType):
        return "Don't be the one stuck without a flag!"

    @classmethod
    def getScoreInfo(cls):
        return{'scoreType':'points'}

    @classmethod
    def getSettings(cls, sessionType):
        return [("Epic Mode", {'default': False}),
                ("Enable Running", {'default': True}),
                ("Enable Punching", {'default': False}),
                ("Time Limit", {
                    'choices': [
                        ("30 Seconds", 30),
                        ("1 Minute", 60),
                        ("2 Minutes", 120),
                        ("3 Minutes", 180)
                        ],
                    'default': 60})]
    
    @classmethod
    def getSupportedMaps(cls, sessionType):
        return ['Doom Shroom']

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.FreeForAllSession) else False

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        self.nodes = []
        if self.settings['Epic Mode']: self._isSlowMotion = True
        self.info = bs.NodeActor(bs.newNode('text',
                                                   attrs={'vAttach': 'bottom',
                                                          'hAlign': 'center',
                                                          'vrDepth': 0,
                                                          'color': (0,.2,0),
                                                          'shadow': 1.0,
                                                          'flatness': 1.0,
                                                          'position': (0,0),
                                                          'scale': 0.8,
                                                          'text': "Created by MattZ45986 on Github",
                                                          }))

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self,music='FlagCatcher')

    def onBegin(self):
        self.timer = bs.OnScreenCountdown(self.settings['Time Limit'], endCall=self.endGame)
        self.timer.start()
        self.ended = False
        self.roundNum = 0
        self.numPickedUp = 0
        self.nodes = []
        self.flags = []
        bs.screenMessage(str(len(self.flags)))
        self.spawned = []
        self.leftPlayers = 0
        self.scores = {}
        for player in self.players:
            self.scores[player] = 0
            player.gameData['survived'] = True
            player.gameData['done'] = False
            player.gameData['score'] = 0
        bs.TeamGameActivity.onBegin(self)
        self.makeRound()
        
    def onPlayerJoin(self,player):
        if self.hasBegun():
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText',subs=[('${PLAYER}',player.getName(full=True))]),color=(0,1,0))
            self.player.gameData['survived'] = False
            self.checkEnd()

    def onPlayerLeave(self,player):
        bs.screenMessage(str(len(self.flags)))
        message = str(player.getName(icon=False)) + " has chickened out!"
        bs.screenMessage(message, color=player.color)
        player.actor.handleMessage(bs.DieMessage())
        if len(self.players) == 1: self.endGame()
        self.checkEnd()

    def makeRound(self):
        for player in self.players:
            if player.gameData['survived']: player.gameData['score'] += 10
        self.roundNum += 1
        self.flags = []
        self.spawned = []
        angle = random.randint(0,359)
        c=0
        for player in self.players:
            if player.gameData['survived']: c+=1
        spacing = 10
        for player in self.players:
            player.gameData['done'] = False
            if player.gameData['survived']:
                self.spawnPlayerSpaz(player,(.5,5,-4))
                self.spawned.append(player)
        try: spacing = 360 // (c)
        except: self.checkEnd()
        colors = [(1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1),(0,1,1),(0,0,0)]
        
        for i in range(c-1):
            angle += spacing
            angle %= 360
            x=6 * sin(degrees(angle))
            z=6 * cos(degrees(angle))
            flag = bs.Flag(position=(x+.5,5,z-4), color=colors[i]).autoRetain()
            self.flags.append(flag)
        
    def killRound(self):
        self.numPickedUp = 0
        for player in self.players:
            if player.isAlive(): player.actor.handleMessage(bs.DieMessage())
        for flag in self.flags: flag.node.delete()
        for light in self.nodes: light.delete()
        bs.screenMessage(str(len(self.flags)))
            
    def spawnPlayerSpaz(self,player,position=(.5,5,-4),angle=0):
        s = self.settings
        name = player.getName()
        color = player.color
        highlight = player.highlight
        players = self.players
        num = len(players)
        i = 0
        position = (-.5+random.random()*2,3+random.random()*2,-5+random.random()*2)
        angle = 0
        spaz = bs.PlayerSpaz(color=color,
                             highlight=highlight,
                             character=player.character,
                             player=player)
        player.setActor(spaz)
        spaz.connectControlsToPlayer(enableBomb=False, enableRun=s["Enable Running"], enablePunch=s["Enable Punching"])
        spaz.handleMessage(bs.StandMessage(position,angle))
        spaz.node.name = name
        spaz.node.nameColor = color
        self.scoreSet.playerGotNewSpaz(player,spaz)

        # move to the stand position and add a flash of light
        spaz.handleMessage(bs.StandMessage(position,angle if angle is not None else random.uniform(0,360)))
        t = bs.getGameTime()
        bs.playSound(self._spawnSound,1,position=spaz.node.position)
        light = bs.newNode('light',attrs={'color':color})
        spaz.node.connectAttr('position',light,'position')
        bsUtils.animate(light,'intensity',{0:0,250:1,500:0})
        bs.gameTimer(500,light.delete)
        return spaz
        
    def handleMessage(self, m):
        if isinstance(m, bs.FlagPickedUpMessage):
            bs.screenMessage(str(len(self.flags)))
            self.numPickedUp += 1
            m.node.getDelegate().getPlayer().gameData['done'] = True
            l = bs.newNode('light',
                                 owner=None,
                                 attrs={'color':m.node.color,
                                        'position':(m.node.positionCenter),
                                        'intensity':1})
            self.nodes.append(l)
            m.flag.handleMessage(bs.DieMessage())
            m.node.handleMessage(bs.DieMessage())
            m.node.delete()
            if self.numPickedUp == len(self.flags):
                for player in self.spawned:
                    if not player.gameData['done']:
                        bs.screenMessage(player.getName())
                        player.gameData['survived'] = False
                        spaz = player.actor.node.getDelegate()
                        spaz.handleMessage(bs.StandMessage((0,3,-2)))
                        bs.gameTimer(100,bs.Call(spaz.handleMessage, bs.FreezeMessage()))
                        bs.gameTimer(2500,bs.Call(spaz.handleMessage, bs.ShouldShatterMessage()))
                bs.gameTimer(3000,self.killRound)
                bs.gameTimer(3050,self.makeRound)
            bs.screenMessage(str(len(self.flags)))
                        
        if isinstance(m, bs.PlayerSpazDeathMessage):
            if m.how == 'fall': self.spawnPlayerSpaz(m.spaz.getPlayer())
            self.checkEnd()
            
    def checkEnd(self):
        bs.screenMessage(str(len(self.flags)))
        i = 0
        for player in self.players:
            if player.gameData['survived']:
                i+=1
        if i <= 1:
            self.endGame()
        
        
    def endGame(self):
        self.ended = True
        if isinstance(self.getSession(), bs.FreeForAllSession):
            results = bs.TeamGameResults()
            for team in self.teams:
                score = 0
                for player in team.players:
                    score += player.gameData['score']
                results.setTeamScore(team, score)
        self.end(results=results)
        for i in self.nodes:
            i.delete()
        for flag in self.flags:
            flag.handleMessage(bs.DieMessage())
