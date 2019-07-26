import bs

def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4

def bsGetGames():
    return [KeepAwayGame]

class KeepAwayGame(bs.TeamGameActivity):

    FLAG_NEW = 0
    FLAG_UNCONTESTED = 1
    FLAG_CONTESTED = 2
    FLAG_HELD = 3

    @classmethod
    def getName(cls):
        return 'Keep Away'

    @classmethod
    def getDescription(cls,sessionType):
        return 'Carry the flag for a set length of time.'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreName':'Time Held'}

    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if (issubclass(sessionType,bs.TeamsSession)
                        or issubclass(sessionType,bs.FreeForAllSession)) else False

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return bs.getMapsSupportingPlayType("keepAway")

    @classmethod
    def getSettings(cls,sessionType):
        return [("Hold Time",{'minValue':10,'default':30,'increment':10}),
                ("Time Limit",{'choices':[('None',0),('1 Minute',60),
                                        ('2 Minutes',120),('5 Minutes',300),
                                        ('10 Minutes',600),('20 Minutes',1200)],'default':0}),
                ("Respawn Times",{'choices':[('Shorter',0.25),('Short',0.5),('Normal',1.0),('Long',2.0),('Longer',4.0)],'default':1.0})]

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        self._scoreBoard = bs.ScoreBoard()
        self._swipSound = bs.getSound("swip")
        self._tickSound = bs.getSound('tick')
        self._countDownSounds = {10:bs.getSound('announceTen'),
                                 9:bs.getSound('announceNine'),
                                 8:bs.getSound('announceEight'),
                                 7:bs.getSound('announceSeven'),
                                 6:bs.getSound('announceSix'),
                                 5:bs.getSound('announceFive'),
                                 4:bs.getSound('announceFour'),
                                 3:bs.getSound('announceThree'),
                                 2:bs.getSound('announceTwo'),
                                 1:bs.getSound('announceOne')}

    def getInstanceDescription(self):
        return ('Carry the flag for ${ARG1} seconds.',self.settings['Hold Time'])

    def getInstanceScoreBoardDescription(self):
        return ('carry the flag for ${ARG1} seconds',self.settings['Hold Time'])

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Keep Away')

    def onTeamJoin(self,team):
        team.gameData['timeRemaining'] = self.settings["Hold Time"]
        self._updateScoreBoard()

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        self.setupStandardPowerupDrops()
        self._flagSpawnPos = self.getMap().getFlagPosition(None)
        self._spawnFlag()
        self._updateTimer = bs.Timer(1000,call=self._tick,repeat=True)
        self._updateFlagState()
        self.projectFlagStand(self._flagSpawnPos)

    def _tick(self):
        self._updateFlagState()

        # award points to all living players holding the flag
        for player in self._holdingPlayers:
            if player.exists():
                self.scoreSet.playerScored(player,3,screenMessage=False,display=False)

        scoringTeam = self._scoringTeam
        
        if scoringTeam is not None:

            if scoringTeam.gameData['timeRemaining'] > 0: bs.playSound(self._tickSound)

            scoringTeam.gameData['timeRemaining'] = max(0,scoringTeam.gameData['timeRemaining']-1)
            self._updateScoreBoard()
            if scoringTeam.gameData['timeRemaining'] > 0:
                self._flag.setScoreText(str(scoringTeam.gameData['timeRemaining']))

            # announce numbers we have sounds for
            try: bs.playSound(self._countDownSounds[scoringTeam.gameData['timeRemaining']])
            except Exception: pass

            # winner
            if scoringTeam.gameData['timeRemaining'] <= 0:
                self.endGame()

    def endGame(self):
        results = bs.TeamGameResults()
        for team in self.teams: results.setTeamScore(team,self.settings['Hold Time'] - team.gameData['timeRemaining'])
        self.end(results=results,announceDelay=0)
        
    def _updateFlagState(self):
        for team in self.teams:
            team.gameData['holdingFlag'] = False
        self._holdingPlayers = []
        for player in self.players:
            try:
                if player.actor.isAlive() and player.actor.node.holdNode.exists():
                    holdingFlag = (player.actor.node.holdNode.getNodeType() == 'flag')
                else: holdingFlag = False
            except Exception:
                bs.printException("exception checking hold flag")
            if holdingFlag:
                self._holdingPlayers.append(player)
                player.getTeam().gameData['holdingFlag'] = True

        holdingTeams = set(t for t in self.teams if t.gameData['holdingFlag'])
        prevState = self._flagState
        if len(holdingTeams) > 1:
            self._flagState = self.FLAG_CONTESTED
            self._scoringTeam = None
            self._flag.light.color = (0.6,0.6,0.1)
            self._flag.node.color = (1.0,1.0,0.4)
        elif len(holdingTeams) == 1:
            holdingTeam = list(holdingTeams)[0]
            self._flagState = self.FLAG_HELD
            self._scoringTeam = holdingTeam
            self._flag.light.color = bs.getNormalizedColor(holdingTeam.color)
            self._flag.node.color = holdingTeam.color
        else:
            self._flagState = self.FLAG_UNCONTESTED
            self._scoringTeam = None
            self._flag.light.color = (0.2,0.2,0.2)
            self._flag.node.color = (1,1,1)
        
        if self._flagState != prevState:
            bs.playSound(self._swipSound)

    def _spawnFlag(self):
        bs.playSound(self._swipSound)
        self._flashFlagSpawn()
        self._flag = bs.Flag(droppedTimeout=20,
                             position=self._flagSpawnPos)
        self._flagState = self.FLAG_NEW
        self._flag.light = bs.newNode('light',
                                      owner=self._flag.node,
                                      attrs={'intensity':0.2,
                                             'radius':0.3,
                                             'color': (0.2,0.2,0.2)})
        self._flag.node.connectAttr('position',self._flag.light,'position')
        self._updateFlagState()

    def _flashFlagSpawn(self):
        light = bs.newNode('light',
                           attrs={'position':self._flagSpawnPos,'color':(1,1,1),
                                  'radius':0.3,'heightAttenuated':False})
        bs.animate(light,'intensity',{0:0,250:0.5,500:0},loop=True)
        bs.gameTimer(1000,light.delete)

    def _updateScoreBoard(self):
        for team in self.teams:
            self._scoreBoard.setTeamValue(team,team.gameData['timeRemaining'],self.settings['Hold Time'],countdown=True)

    def handleMessage(self,m):
        if isinstance(m,bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m) # augment default
            self.respawnPlayer(m.spaz.getPlayer())
        elif isinstance(m,bs.FlagDeathMessage):
            self._spawnFlag()
        elif isinstance(m,bs.FlagDroppedMessage) or isinstance(m,bs.FlagPickedUpMessage):
            self._updateFlagState()
        else: bs.TeamGameActivity.handleMessage(self,m)
