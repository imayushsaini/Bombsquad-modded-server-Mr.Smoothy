import bs
import random


class TheLastStandGame(bs.CoopGameActivity):

    tips = ['This level never ends, but a high score here\n'
            'will earn you eternal respect throughout the world.']

    @classmethod
    def getName(cls):
        return 'The Last Stand'

    @classmethod
    def getDescription(cls, sessionType):
        return "Final glorious epic slow motion battle to the death."

    def __init__(self, settings={}):

        settings['map'] = 'Rampage'
        bs.CoopGameActivity.__init__(self, settings)

        # show messages when players die since it matters here..
        self.announcePlayerDeaths = True

        self._isSlowMotion = True

        self._newWaveSound = bs.getSound('scoreHit01')
        self._winSound = bs.getSound("score")
        self._cashRegisterSound = bs.getSound('cashRegister')

        self._spawnCenter = (0, 5.5, -4.14)
        self._tntSpawnPosition = (0, 5.5, -6)
        self._powerupCenter = (0, 7, -4.14)
        self._powerupSpread = (7, 2)

        try:
            self._preset = self.settings['preset']
        except Exception:
            self._preset = 'default'

        self._excludePowerups = []

        # for each bot type: spawn rate, increase, dIncrease
        self._botSpawnTypes = {bs.BomberBot:               [1.0,  0.0,  0.0],
                               bs.BomberBotPro:            [0.0,  0.05, 0.001],
                               bs.BomberBotProShielded:    [0.0,  0.02, 0.002],
                               bs.ToughGuyBot:             [1.0,  0.0,  0.0],
                               bs.ToughGuyBotPro:          [0.0,  0.05, 0.001],
                               bs.ToughGuyBotProShielded:  [0.0,  0.02, 0.002],
                               bs.ChickBot:                [0.3,  0.0,  0.0],
                               bs.ChickBotPro:             [0.0,  0.05, 0.001],
                               bs.ChickBotProShielded:     [0.0,  0.02, 0.002],
                               bs.NinjaBot:                [0.3,  0.05, 0.0],
                               bs.MelBot:                  [0.1,  0.03, 0.001],
                               bs.PirateBot:               [0.05, 0.02, 0.002]
                               }

    def onTransitionIn(self):
        bs.CoopGameActivity.onTransitionIn(self, music='Epic')
        bs.gameTimer(1300, bs.Call(bs.playSound, self._newWaveSound))
        self._scoreBoard = bs.ScoreBoard(
            label=bs.Lstr(resource='scoreText'),
            scoreSplit=0.5)
        # we use this in place of a regular int to make it harder to hack scores
        self._score = bs.SecureInt(0)

    def onBegin(self):

        bs.CoopGameActivity.onBegin(self)

        # spit out a few powerups and start dropping more shortly
        self._dropPowerups(standardPoints=True)
        bs.gameTimer(2000, bs.WeakCall(self._startPowerupDrops))
        bs.gameTimer(1, bs.WeakCall(self._startBotUpdates))
        self.setupLowLifeWarningSound()
        self._updateScores()
        self._bots = bs.BotSet()
        self._dingSound = bs.getSound('dingSmall')
        self._dingSoundHigh = bs.getSound('dingSmallHigh')

        # our TNT spawner (if applicable)
        self._tntSpawner = bs.TNTSpawner(
            position=self._tntSpawnPosition, respawnTime=10000)

    def spawnPlayer(self, player):
        pos = (
            self._spawnCenter[0] + random.uniform(-1.5, 1.5),
            self._spawnCenter[1],
            self._spawnCenter[2] + random.uniform(-1.5, 1.5))
        self.spawnPlayerSpaz(player, position=pos)

    def _startBotUpdates(self):
        self._botUpdateInterval = 3300 - 300*(len(self.players))
        self._updateBots()
        self._updateBots()
        if len(self.players) > 2:
            self._updateBots()
        if len(self.players) > 3:
            self._updateBots()
        self._botUpdateTimer = bs.Timer(
            int(self._botUpdateInterval),
            bs.WeakCall(self._updateBots))

    def _dropPowerup(self, index, powerupType=None):
        if powerupType is None:
            powerupType = bs.Powerup.getFactory().getRandomPowerupType(
                excludeTypes=self._excludePowerups)
        bs.Powerup(
            position=self.getMap().powerupSpawnPoints[index],
            powerupType=powerupType).autoRetain()

    def _startPowerupDrops(self):
        self._powerupDropTimer = bs.Timer(
            3000, bs.WeakCall(self._dropPowerups), repeat=True)

    def _dropPowerups(self, standardPoints=False, forceFirst=None):
        """ Generic powerup drop """

        if standardPoints:
            pts = self.getMap().powerupSpawnPoints
            for i, pt in enumerate(pts):
                bs.gameTimer(1000+i*500, bs.WeakCall(
                    self._dropPowerup, i, forceFirst if i == 0 else None))
        else:
            pt = (self._powerupCenter[0]
                  + random.uniform(-1.0*self._powerupSpread[0],
                                   1.0*self._powerupSpread[0]),
                  self._powerupCenter[1],
                  self._powerupCenter[2]
                  + random.uniform(-self._powerupSpread[1],
                                   self._powerupSpread[1]))

            # drop one random one somewhere..
            bs.Powerup(
                position=pt,
                powerupType=bs.Powerup.getFactory().getRandomPowerupType(
                    excludeTypes=self._excludePowerups)).autoRetain()

    def doEnd(self, outcome):
        if outcome == 'defeat':
            self.fadeToRed()
        self.end(
            delay=2000,
            results={'outcome': outcome, 'score': self._score.get(),
                     'playerInfo': self.initialPlayerInfo})

    def _updateBots(self):
        self._botUpdateInterval = max(500, self._botUpdateInterval * 0.98)
        self._botUpdateTimer = bs.Timer(
            int(self._botUpdateInterval),
            bs.WeakCall(self._updateBots))

        botSpawnPoints = [[-5, 5.5, -4.14], [0, 5.5, -4.14], [5, 5.5, -4.14]]
        dists = [0, 0, 0]
        playerPts = []
        for player in self.players:
            try:
                if player.isAlive():
                    playerPts.append(player.actor.node.position)
            except Exception as e:
                print 'EXC in _updateBots', e
        for i in range(3):
            for p in playerPts:
                dists[i] += abs(p[0]-botSpawnPoints[i][0])
            # little random variation
            dists[i] += random.random() * 5.0
        if dists[0] > dists[1] and dists[0] > dists[2]:
            pt = botSpawnPoints[0]
        elif dists[1] > dists[2]:
            pt = botSpawnPoints[1]
        else:
            pt = botSpawnPoints[2]

        pt = (pt[0]+3.0*(random.random()-0.5),
              pt[1], 2.0*(random.random()-0.5)+pt[2])

        # normalize our bot type total and find a random number within that
        total = 0.0
        for t in self._botSpawnTypes.items():
            total += t[1][0]
        r = random.random()*total

        # now go back through and see where this value falls
        total = 0
        for t in self._botSpawnTypes.items():
            total += t[1][0]
            if r <= total:
                spazType = t[0]
                break

        spawnTime = 1000
        self._bots.spawnBot(spazType, pos=pt, spawnTime=spawnTime)

        # after every spawn we adjust our ratios slightly to get more
        # difficult..
        for t in self._botSpawnTypes.items():
            t[1][0] += t[1][1]  # increase spawn rate
            t[1][1] += t[1][2]  # increase spawn rate increase rate

    def _updateScores(self):

        # achievements in default only..
        score = self._score.get()
        if self._preset == 'default':
            if score >= 250:
                self._awardAchievement('Last Stand Master')
            if score >= 500:
                self._awardAchievement('Last Stand Wizard')
            if score >= 1000:
                self._awardAchievement('Last Stand God')
        self._scoreBoard.setTeamValue(self.teams[0], score, maxScore=None)

    def handleMessage(self, m):

        if isinstance(m, bs.PlayerSpazDeathMessage):
            player = m.spaz.getPlayer()
            if player is None:
                bs.printError('FIXME: getPlayer() should no longer '
                              'ever be returning None')
                return
            if not player.exists():
                return
            self.scoreSet.playerLostSpaz(player)
            bs.gameTimer(100, self._checkRoundOver)

        elif isinstance(m, bs.PlayerScoredMessage):
            self._score.add(m.score)
            self._updateScores()

        elif isinstance(m, bs.SpazBotDeathMessage):
            pts, importance = m.badGuy.getDeathPoints(m.how)
            if m.killerPlayer is not None and m.killerPlayer.exists():
                try:
                    target = m.badGuy.node.position
                except Exception:
                    target = None
                try:
                    self.scoreSet.playerScored(
                        m.killerPlayer, pts, target=target, kill=True,
                        screenMessage=False, importance=importance)
                    bs.playSound(self._dingSound if importance ==
                                 1 else self._dingSoundHigh, volume=0.6)
                except Exception as e:
                    print 'EXC on last-stand SpazBotDeathMessage', e
            # normally we pull scores from the score-set, but if there's no
            # player lets be explicit..
            else:
                self._score.add(pts)
            self._updateScores()
        else:
            self.__superHandleMessage(m)

    def __superHandleMessage(self, m):
        super(TheLastStandGame, self).handleMessage(m)

    def _onGotScoresToBeat(self, scores):
        self._showStandardScoresToBeatUI(scores)

    def endGame(self):
        # tell our bots to celebrate just to rub it in
        self._bots.finalCelebrate()
        bs.gameTimer(1, bs.WeakCall(self.doEnd, 'defeat'))
        bs.playMusic(None)

    def _checkRoundOver(self):
        """
        see if the round is over in response to an event (player died, etc)
        """

        if not any(player.isAlive() for player in self.teams[0].players):
            self.endGame()
