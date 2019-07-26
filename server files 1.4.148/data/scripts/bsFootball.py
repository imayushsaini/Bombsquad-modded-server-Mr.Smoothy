import bs
import random

def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4

def bsGetGames():
    return [FootballTeamGame]

class FootballTeamGame(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Football'

    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if issubclass(sessionType,bs.TeamsSession) else False
    
    @classmethod
    def getDescription(cls,sessionType):
        return 'Get the flag to the enemy end zone.'

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return bs.getMapsSupportingPlayType('football')

    @classmethod
    def getSettings(cls, sessionType):
        return [("Score to Win", {'minValue':7, 'default':21, 'increment':7}),
                ("Time Limit", {'choices':[
                    ('None', 0), ('1 Minute', 60),
                    ('2 Minutes', 120), ('5 Minutes', 300),
                    ('10 Minutes', 600), ('20 Minutes', 1200)], 'default':0}),
                ("Respawn Times", {'choices':[
                    ('Shorter', 0.25), ('Short', 0.5), ('Normal', 1.0),
                    ('Long', 2.0), ('Longer', 4.0)], 'default':1.0})]

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        self._scoreBoard = bs.ScoreBoard()

        # load some media we need
        self._cheerSound = bs.getSound("cheer")
        self._chantSound = bs.getSound("crowdChant")
        self._scoreSound = bs.getSound("score")
        self._swipSound = bs.getSound("swip")
        self._whistleSound = bs.getSound("refWhistle")

        self.scoreRegionMaterial = bs.Material()
        self.scoreRegionMaterial.addActions(
            conditions=("theyHaveMaterial",bs.Flag.getFactory().flagMaterial),
            actions=(("modifyPartCollision","collide",True),
                     ("modifyPartCollision","physical",False),
                     ("call","atConnect",self._handleScore)))

    def getInstanceDescription(self):
        tds = self.settings['Score to Win']/7
        if tds > 1: return ('Score ${ARG1} touchdowns.',tds)
        else: return ('Score a touchdown.')

    def getInstanceScoreBoardDescription(self):
        tds = self.settings['Score to Win']/7
        if tds > 1: return ('score ${ARG1} touchdowns',tds)
        else: return ('score a touchdown')

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Football')

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        self.setupStandardPowerupDrops()
        self._flagSpawnPos = self.getMap().getFlagPosition(None)
        self._spawnFlag()
        self._scoreRegions = []
        defs = self.getMap().defs
        self._scoreRegions.append(bs.NodeActor(bs.newNode('region', attrs={
            'position':defs.boxes['goal1'][0:3],
            'scale':defs.boxes['goal1'][6:9],
            'type': 'box',
            'materials':(self.scoreRegionMaterial,)})))
        self._scoreRegions.append(bs.NodeActor(bs.newNode('region', attrs={
            'position':defs.boxes['goal2'][0:3],
            'scale':defs.boxes['goal2'][6:9],
            'type': 'box',
            'materials':(self.scoreRegionMaterial,)})))
        self._updateScoreBoard()
        bs.playSound(self._chantSound)

    def onTeamJoin(self,team):
        team.gameData['score'] = 0
        self._updateScoreBoard()

    def _killFlag(self):
        self._flag = None

    def _handleScore(self):
        """ a point has been scored """

        # our flag might stick around for a second or two
        # make sure it doesn't score again
        if self._flag.scored: return
        region = bs.getCollisionInfo("sourceNode")
        for i in range(len(self._scoreRegions)):
            if region == self._scoreRegions[i].node:
                break;
        for team in self.teams:
            if team.getID() == i:
                team.gameData['score'] += 7

                # tell all players to celebrate
                for player in team.players:
                    try: player.actor.node.handleMessage('celebrate',2000)
                    except Exception: pass

                # if someone on this team was last to touch it, give them points
                if (self._flag.lastHoldingPlayer is not None
                    and self._flag.lastHoldingPlayer.exists()
                    and team == self._flag.lastHoldingPlayer.getTeam()):
                    self.scoreSet.playerScored(self._flag.lastHoldingPlayer,
                                               50, bigMessage=True)
                # end game if we won
                if team.gameData['score'] >= self.settings['Score to Win']:
                    self.endGame()
        bs.playSound(self._scoreSound)
        bs.playSound(self._cheerSound)
        self._flag.scored = True

        # kill the flag (it'll respawn shortly)
        bs.gameTimer(1000,self._killFlag)
        light = bs.newNode('light', attrs={
            'position': bs.getCollisionInfo('position'),
            'heightAttenuated':False,
            'color': (1,0,0)})
        bs.animate(light,'intensity',{0:0,500:1,1000:0},loop=True)
        bs.gameTimer(1000,light.delete)
        self.cameraFlash(duration=10)
        self._updateScoreBoard()

    def endGame(self):
        results = bs.TeamGameResults()
        for t in self.teams: results.setTeamScore(t,t.gameData['score'])
        self.end(results=results,announceDelay=800)

    def _updateScoreBoard(self):
        winScore = self.settings['Score to Win']
        for team in self.teams:
            self._scoreBoard.setTeamValue(team,team.gameData['score'],winScore)

    def handleMessage(self,m):

        if isinstance(m,bs.FlagPickedUpMessage):
            try:
                player = m.node.getDelegate().getPlayer()
                if player.exists(): m.flag.lastHoldingPlayer = player
            except Exception:
                bs.printException('exception in Football FlagPickedUpMessage;'
                                  ' this shoudln\'t happen')
            m.flag.heldCount += 1

        elif isinstance(m,bs.FlagDroppedMessage):
            m.flag.heldCount -= 1

        # respawn dead players if they're still in the game
        elif isinstance(m,bs.PlayerSpazDeathMessage):
            # augment standard behavior
            bs.TeamGameActivity.handleMessage(self, m)
            self.respawnPlayer(m.spaz.getPlayer())

        # respawn dead flags
        elif isinstance(m,bs.FlagDeathMessage):
            if not self.hasEnded():
                self._flagRespawnTimer = bs.Timer(3000,self._spawnFlag)
                self._flagRespawnLight = bs.NodeActor(
                    bs.newNode('light', attrs={
                        'position': self._flagSpawnPos,
                        'heightAttenuated':False,
                        'radius':0.15,
                        'color': (1.0,1.0,0.3)}))
                bs.animate(self._flagRespawnLight.node, "intensity",
                           {0:0,250:0.15,500:0},loop=True)
                bs.gameTimer(3000,self._flagRespawnLight.node.delete)

        else:
            # augment standard behavior
            bs.TeamGameActivity.handleMessage(self,m)

    def _flashFlagSpawn(self):
        light = bs.newNode('light', attrs={
            'position': self._flagSpawnPos,
            'heightAttenuated': False,
            'color': (1,1,0)})
        bs.animate(light,'intensity',{0:0,250:0.25,500:0},loop=True)
        bs.gameTimer(1000,light.delete)

    def _spawnFlag(self):
        bs.playSound(self._swipSound)
        bs.playSound(self._whistleSound)
        self._flashFlagSpawn()
        self._flag = bs.Flag(position=self._flagSpawnPos,
                             droppedTimeout=20,
                             color=(1,1,0.3))
        self._flag.scored = False
        self._flag.heldCount = 0
        self._flag.lastHoldingPlayer = None
        self._flag.light = bs.newNode("light", owner=self._flag.node, attrs={
            "intensity":0.25,
            "heightAttenuated":False,
            "radius":0.2,
            "color": (0.9,0.7,0.0)})
        self._flag.node.connectAttr('position',self._flag.light,'position')


class FootballCoopGame(bs.CoopGameActivity):

    tips = ['Use the pick-up button to grab the flag < ${PICKUP} >']

    @classmethod
    def getName(cls):
        return 'Football'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreType':'milliseconds',
                'scoreVersion':'B'}

    # FIXME need to combine this call with getScoreInfo...
    def _getScoreType(self):
        return 'time'
    
    def getInstanceDescription(self):
        tds = self._scoreToWin/7
        if tds > 1: return ('Score ${ARG1} touchdowns.',tds)
        else: return ('Score a touchdown.')

    def getInstanceScoreBoardDescription(self):
        tds = self._scoreToWin/7
        if tds > 1: return ('score ${ARG1} touchdowns',tds)
        else: return ('score a touchdown')

    def __init__(self,settings={}):

        settings['map'] = 'Football Stadium'
        bs.CoopGameActivity.__init__(self,settings)
        try: self._preset = self.settings['preset']
        except Exception: self._preset = 'rookie'

        # load some media we need
        self._cheerSound = bs.getSound("cheer")
        self._booSound = bs.getSound("boo")
        self._chantSound = bs.getSound("crowdChant")
        self._scoreSound = bs.getSound("score")
        self._swipSound = bs.getSound("swip")
        self._whistleSound = bs.getSound("refWhistle")
        self._scoreToWin = 21
        self._scoreRegionMaterial = bs.Material()
        self._scoreRegionMaterial.addActions(
            conditions=("theyHaveMaterial",bs.Flag.getFactory().flagMaterial),
            actions=(("modifyPartCollision","collide",True),
                     ("modifyPartCollision","physical",False),
                     ("call","atConnect",self._handleScore)))
        self._powerupCenter = (0,2,0)
        self._powerupSpread = (10,5.5)
        self._playerHasDroppedBomb = False
        self._playerHasPunched = False

    def onTransitionIn(self):
        bs.CoopGameActivity.onTransitionIn(self,music='Football')
        self._scoreBoard = bs.ScoreBoard()
        self._flagSpawnPos = self.getMap().getFlagPosition(None)
        self._spawnFlag()

        # set up the two score regions
        self.scoreRegions = []
        defs = self.getMap().defs
        self.scoreRegions.append(bs.NodeActor(bs.newNode('region', attrs={
            'position':defs.boxes['goal1'][0:3],
            'scale':defs.boxes['goal1'][6:9],
            'type': 'box',
            'materials':[self._scoreRegionMaterial]})))
        self.scoreRegions.append(bs.NodeActor(bs.newNode('region', attrs={
            'position':defs.boxes['goal2'][0:3],
            'scale':defs.boxes['goal2'][6:9],
            'type': 'box',
            'materials':[self._scoreRegionMaterial]})))
        bs.playSound(self._chantSound)

    def onBegin(self):
        bs.CoopGameActivity.onBegin(self)

        # show controls help in kiosk mode
        if bs.getEnvironment()['kioskMode']:
            import bsUtils
            bsUtils.ControlsHelpOverlay(delay=3000, lifespan=10000,
                                        bright=True).autoRetain()
        if self._preset in ['rookie','rookieEasy']:
            self._excludePowerups = ['curse']
            self._haveTnt = False
            tgb = (bs.ToughGuyBotLame if self._preset == 'rookieEasy'
                   else bs.ToughGuyBot)
            self._botTypesInitial = [tgb]*len(self.initialPlayerInfo)
            bb = (bs.BomberBotLame if self._preset == 'rookieEasy'
                  else bs.BomberBot)
            self._botTypes7 = [bb]*(1 if len(self.initialPlayerInfo) < 3 else 2)
            cb = bs.BomberBot if self._preset == 'rookieEasy' else bs.ChickBot
            self._botTypes14 = \
                [cb]*(1 if len(self.initialPlayerInfo) < 3 else 2)
        elif self._preset == 'tournament':
            self._excludePowerups = []
            self._haveTnt = True
            self._botTypesInitial = \
                [bs.ToughGuyBot]*(1 if len(self.initialPlayerInfo) < 2 else 2)
            self._botTypes7 = \
                [bs.ChickBot]*(1 if len(self.initialPlayerInfo) < 3 else 2)
            self._botTypes14 = \
                [bs.NinjaBot]*(1 if len(self.initialPlayerInfo) < 4 else 2)
        elif self._preset in ['pro','proEasy','tournamentPro']:
            self._excludePowerups = ['curse']
            self._haveTnt = True
            self._botTypesInitial = [bs.NinjaBot]*len(self.initialPlayerInfo)
            tgb = \
                bs.ToughGuyBot if self._preset == 'pro' else bs.ToughGuyBotLame
            self._botTypes7 = [tgb]+[bs.BomberBot] \
                * (1 if len(self.initialPlayerInfo) < 3 else 2)
            cb = bs.ChickBotPro if self._preset == 'pro' else bs.ChickBot
            self._botTypes14 = [cb] \
                * (1 if len(self.initialPlayerInfo) < 3 else 2)
        elif self._preset in ['uber','uberEasy']:
            self._excludePowerups = []
            self._haveTnt = True
            tgb = (bs.ToughGuyBotPro if self._preset == 'uber'
                   else bs.ToughGuyBot)
            cb = bs.ChickBotPro if self._preset == 'uber' else bs.ChickBot
            self._botTypesInitial = \
                [bs.MelBot] + [tgb]*len(self.initialPlayerInfo)
            self._botTypes7 = [cb]*(1 if len(self.initialPlayerInfo) < 3 else 2)
            self._botTypes14 = \
                [bs.PirateBot]*(1 if len(self.initialPlayerInfo) < 3 else 2)
        else: raise Exception()

        self.setupLowLifeWarningSound()

        self._dropPowerups(standardPoints=True)
        bs.gameTimer(4000,self._startPowerupDrops)

        # make a bogus team for our bots
        badTeamName = self.getTeamDisplayString('Bad Guys')
        self._botTeam = bs.Team(1,badTeamName,(0.5,0.4,0.4))

        for team in [self.teams[0],self._botTeam]:
            team.gameData['score'] = 0

        self.updateScores()

        # time display
        self._startTime = bs.getGameTime()
        self._timeText = bs.NodeActor(bs.newNode('text', attrs={
            'vAttach':'top',
            'hAttach':'center',
            'hAlign':'center',
            'color':(1,1,0.5,1),
            'flatness':0.5,
            'shadow':0.5,
            'position':(0,-50),
            'scale':1.3,
            'text':''}))
        self._timeTextInput = bs.NodeActor(bs.newNode('timeDisplay', attrs={
            'showSubSeconds':True}))
        bs.getSharedObject('globals').connectAttr(
            'gameTime', self._timeTextInput.node, 'time2')
        self._timeTextInput.node.connectAttr(
            'output', self._timeText.node, 'text')
        
        # our TNT spawner (if applicable)
        if self._haveTnt:
            self._tntSpawner = bs.TNTSpawner(position=(0,1,-1))

        self._bots = bs.BotSet()
        self._botSpawnTimer = bs.Timer(1000,self._updateBots,repeat=True)

        for b in self._botTypesInitial: self._spawnBot(b)

    def _onGotScoresToBeat(self,scores):
        self._showStandardScoresToBeatUI(scores)

    def _onBotSpawn(self,spaz):
        # we want to move to the left by default
        spaz.targetPointDefault = bs.Vector(0,0,0)
        
    def _spawnBot(self,spazType,immediate=False):
        pos = self.getMap().getStartPosition(self._botTeam.getID())
        self._bots.spawnBot(spazType, pos=pos,
                            spawnTime=1 if immediate else 3000,
                            onSpawnCall=self._onBotSpawn)

    def _updateBots(self):
        bots = self._bots.getLivingBots()
        for bot in bots:
            bot.targetFlag = None

        # if we're waiting on a continue, stop here so they don't keep scoring
        if self.isWaitingForContinue():
            self._bots.stopMoving()
            return
            
        # if we've got a flag and no player are holding it, find the closest
        # bot to it, and make them the designated flag-bearer
        if self._flag.node.exists():
            for p in self.players:
                try:
                    if (p.actor.isAlive()
                        and p.actor.node.holdNode == self._flag.node):
                        return
                except Exception:
                    bs.printException("exception checking hold node")

            fp = bs.Vector(*self._flag.node.position)
            closestBot = None
            for bot in bots:
                # if a bot is picked up he should forget about the flag
                if bot.heldCount > 0: continue
                bp = bs.Vector(*bot.node.position)
                l = (bp-fp).length()
                if (closestBot is None or l < closestLen):
                    closestLen = l
                    closestBot = bot
            if closestBot is not None:
                closestBot.targetFlag = self._flag

    def _dropPowerup(self,index,powerupType=None):
        if powerupType is None:
            powerupType = bs.Powerup.getFactory().getRandomPowerupType(
                excludeTypes=self._excludePowerups)
        bs.Powerup(position=self.getMap().powerupSpawnPoints[index],
                   powerupType=powerupType).autoRetain()

    def _startPowerupDrops(self):
        self._powerupDropTimer = bs.Timer(3000,self._dropPowerups,repeat=True)

    def _dropPowerups(self,standardPoints=False,powerupType=None):
        """ Generic powerup drop """

        if standardPoints:
            pts = self.getMap().powerupSpawnPoints
            for i,pt in enumerate(pts):
                bs.gameTimer(1000+i*500,
                             bs.Call(self._dropPowerup,i,powerupType))
        else:
            pt = (self._powerupCenter[0]
                  + random.uniform(-1.0*self._powerupSpread[0],
                                   1.0*self._powerupSpread[0]),
                  self._powerupCenter[1],
                  self._powerupCenter[2]
                  + random.uniform(-self._powerupSpread[1],
                                   self._powerupSpread[1]))

            # drop one random one somewhere..
            bs.Powerup(position=pt,
                       powerupType=bs.Powerup.getFactory()\
                       .getRandomPowerupType(
                           excludeTypes=self._excludePowerups)).autoRetain()

    def _killFlag(self):
        try: self._flag.handleMessage(bs.DieMessage())
        except Exception,e: print "FIXME; Exception on killFlag:",e

    def _handleScore(self):
        """ a point has been scored """

        # our flag might stick around for a second or two
        # we dont want it to be able to score again
        if self._flag.scored:
            return

        # see which score region it was..
        region = bs.getCollisionInfo("sourceNode")
        for i in range(len(self.scoreRegions)):
            if region == self.scoreRegions[i].node:
                break;

        for team in [self.teams[0],self._botTeam]:
            if team.getID() == i:
                team.gameData['score'] += 7

                # tell all players (or bots) to celebrate
                if i == 0:
                    for player in team.players:
                        try: player.actor.node.handleMessage('celebrate',2000)
                        except Exception: pass
                else:
                    self._bots.celebrate(2000)

        # if the good guys scored, add more enemies
        if i == 0:
            if self.teams[0].gameData['score'] == 7:
                for t in self._botTypes7:
                    self._spawnBot(t)
            elif self.teams[0].gameData['score'] == 14:
                for t in self._botTypes14:
                    self._spawnBot(t)

        bs.playSound(self._scoreSound)
        if i == 0: bs.playSound(self._cheerSound)
        else: bs.playSound(self._booSound)

        #kill the flag (it'll respawn shortly)
        self._flag.scored = True

        bs.gameTimer(200,self._killFlag)

        self.updateScores()
        light = bs.newNode('light', attrs={
            'position': bs.getCollisionInfo('position'),
            'heightAttenuated':False,
            'color': (1,0,0)})
        bs.animate(light, 'intensity', {0:0,500:1,1000:0},loop=True)
        bs.gameTimer(1000,light.delete)
        if i == 0: self.cameraFlash(duration=10)

    def endGame(self):
        bs.playMusic(None)
        self._bots.finalCelebrate()
        bs.gameTimer(1,bs.Call(self.doEnd,'defeat'))

    def onContinue(self):
        # subtract one touchdown from the bots and get them moving again
        self._botTeam.gameData['score'] -= 7
        self._bots.startMoving()
        self.updateScores()
        
    def updateScores(self):
        """ update scoreboard and check for winners """
        haveScoringTeam = False
        winScore = self._scoreToWin
        for team in [self.teams[0],self._botTeam]:
            self._scoreBoard.setTeamValue(team,team.gameData['score'],winScore)
            if team.gameData['score'] >= winScore:
                if not haveScoringTeam:
                    self.scoringTeam = team
                    if team is self._botTeam:
                        self.continueOrEndGame()
                    else:
                        bs.playMusic('Victory')

                        # completion achievements
                        if self._preset in ['rookie','rookieEasy']:
                            self._awardAchievement('Rookie Football Victory',
                                                   sound=False)
                            if self._botTeam.gameData['score'] == 0:
                                self._awardAchievement(
                                    'Rookie Football Shutout',sound=False)
                        elif self._preset in ['pro','proEasy']:
                            self._awardAchievement(
                                'Pro Football Victory',sound=False)
                            if self._botTeam.gameData['score'] == 0:
                                self._awardAchievement(
                                    'Pro Football Shutout',sound=False)
                        elif self._preset in ['uber','uberEasy']:
                            self._awardAchievement(
                                'Uber Football Victory',sound=False)
                            if self._botTeam.gameData['score'] == 0:
                                self._awardAchievement(
                                    'Uber Football Shutout',sound=False)
                            if (not self._playerHasDroppedBomb
                                and not self._playerHasPunched):
                                self._awardAchievement(
                                    'Got the Moves',sound=False)
                        self._bots.stopMoving()
                        self.showZoomMessage(bs.Lstr(resource='victoryText'),
                                             scale=1.0,duration=4000)
                        self.celebrate(10000)
                        self._finalTime = (bs.getGameTime() - self._startTime)
                        self._timeTextTimer = None
                        self._timeTextInput.node.timeMax = self._finalTime
                        bs.gameTimer(1,bs.Call(self.doEnd,'victory'))

    def doEnd(self,outcome):
        if outcome == 'defeat': self.fadeToRed()
        self.end(delay=3000,results={
            'outcome':outcome,
            'score':None if outcome == 'defeat' else int(self._finalTime/10),
            'scoreOrder':'decreasing',
            'playerInfo':self.initialPlayerInfo})

    def handleMessage(self,m):
        """ handle high-level game messages """
        if isinstance(m,bs.PlayerSpazDeathMessage):
            # respawn dead players
            player = m.spaz.getPlayer()
            self.scoreSet.playerLostSpaz(player)
            respawnTime = 2000+len(self.initialPlayerInfo)*1000

            # respawn them shortly
            player.gameData['respawnTimer'] = bs.Timer(
                respawnTime, bs.Call(self.spawnPlayerIfExists,player))
            player.gameData['respawnIcon'] = bs.RespawnIcon(player, respawnTime)

            # augment standard behavior
            bs.CoopGameActivity.handleMessage(self,m)

        elif isinstance(m,bs.SpazBotDeathMessage):
            # every time a bad guy dies, spawn a new one
            bs.gameTimer(3000,bs.Call(self._spawnBot,(type(m.badGuy))))

        elif isinstance(m,bs.SpazBotPunchedMessage):
            if self._preset in ['rookie','rookieEasy']:
                if m.damage >= 500:
                    self._awardAchievement('Super Punch')
            elif self._preset in ['pro','proEasy']:
                if m.damage >= 1000:
                    self._awardAchievement('Super Mega Punch')

        # respawn dead flags
        elif isinstance(m,bs.FlagDeathMessage):
            m.flag.respawnTimer = bs.Timer(3000,self._spawnFlag)
            self._flagRespawnLight = bs.NodeActor(bs.newNode('light', attrs={
                'position': self._flagSpawnPos,
                'heightAttenuated':False,
                'radius':0.15,
                'color': (1.0,1.0,0.3)}))
            bs.animate(self._flagRespawnLight.node,"intensity",
                       {0:0,250:0.15,500:0},loop=True)
            bs.gameTimer(3000,self._flagRespawnLight.node.delete)
        else:
            bs.CoopGameActivity.handleMessage(self,m)
            
    def _handlePlayerDroppedBomb(self,player,bomb):
        self._playerHasDroppedBomb = True

    def _handlePlayerPunched(self,player):
        self._playerHasPunched = True

    def spawnPlayer(self,player):
        s = self.spawnPlayerSpaz(
            player,
            position=self.getMap().getStartPosition(player.getTeam().getID()))
        if self._preset in ['rookieEasy','proEasy','uberEasy']:
            s._impactScale = 0.25
        s.addDroppedBombCallback(self._handlePlayerDroppedBomb)
        s.punchCallback = self._handlePlayerPunched

    def _flashFlagSpawn(self):
        light = bs.newNode('light',
                           attrs={'position': self._flagSpawnPos,
                                  'heightAttenuated':False,
                                  'color': (1,1,0)})
        bs.animate(light,'intensity',{0:0,250:0.25,500:0},loop=True)
        bs.gameTimer(1000,light.delete)

    def _spawnFlag(self):
        bs.playSound(self._swipSound)
        bs.playSound(self._whistleSound)
        self._flashFlagSpawn()
        self._flag = bs.Flag(position=self._flagSpawnPos,
                             droppedTimeout=20,
                             color=(1,1,0.3))
        self._flag.node.isAreaOfInterest = True
        self._flag.respawnTimer = None
        self._flag.scored = False
        self._flag.heldCount = 0
        self._flag.light = bs.newNode('light', owner=self._flag.node, attrs={
            'intensity':0.25,
            'heightAttenuated':False,
            'radius':0.1,
            'color': (0.9,0.7,0.0)})
        self._flag.node.connectAttr('position',self._flag.light,'position')

