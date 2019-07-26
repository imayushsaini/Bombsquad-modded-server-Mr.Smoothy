import bs
import random
import math


class RunaroundGame(bs.CoopGameActivity):

    tips = [
        'Jump just as you\'re throwing to get bombs up to the highest levels.',
        'No, you can\'t get up on the ledge. You have to throw bombs.',
        'Whip back and forth to get more distance on your throws..']

    @classmethod
    def getName(cls):
        return 'Runaround'

    @classmethod
    def getDescription(cls, sessionType):
        return "Prevent enemies from reaching the exit."

    def __init__(self, settings={}):

        settings['map'] = 'Tower D'
        bs.CoopGameActivity.__init__(self, settings)

        try:
            self._preset = self.settings['preset']
        except Exception:
            self._preset = 'pro'

        self._playerDeathSound = bs.getSound('playerDeath')

        self._newWaveSound = bs.getSound('scoreHit01')
        self._winSound = bs.getSound("score")
        self._cashRegisterSound = bs.getSound('cashRegister')
        self._badGuyScoreSound = bs.getSound("shieldDown")

        self._heartTex = bs.getTexture('heart')
        self._heartModelOpaque = bs.getModel('heartOpaque')
        self._heartModelTransparent = bs.getModel('heartTransparent')

        self._aPlayerHasBeenKilled = False

        self._spawnCenter = self._mapType.defs.points['spawn1'][0:3]
        self._tntSpawnPosition = self._mapType.defs.points['tntLoc'][0:3]
        self._powerupCenter = self._mapType.defs.boxes['powerupRegion'][0:3]
        self._powerupSpread = (
            self._mapType.defs.boxes['powerupRegion'][6]*0.5,
            self._mapType.defs.boxes['powerupRegion'][8]*0.5)

        self._scoreRegionMaterial = bs.Material()
        self._scoreRegionMaterial.addActions(
            conditions=("theyHaveMaterial",
                        bs.getSharedObject('playerMaterial')),
            actions=(("modifyPartCollision", "collide", True),
                     ("modifyPartCollision", "physical", False),
                     ("call", "atConnect", self._handleReachedEnd)))

        self._lastWaveEndTime = bs.getGameTime()
        self._playerHasPickedUpPowerup = False

    def onTransitionIn(self):

        bs.CoopGameActivity.onTransitionIn(self, music='Marching')

        self._scoreBoard = bs.ScoreBoard(
            label=bs.Lstr(resource='scoreText'),
            scoreSplit=0.5)
        self._gameOver = False
        self._wave = 0
        self._canEndWave = True
        # we use this in place of a regular int to make it harder to hack scores
        self._score = bs.SecureInt(0)
        self._timeBonus = 0

        self._scoreRegion = bs.NodeActor(
            bs.newNode(
                'region',
                attrs={'position': self.getMap().defs.boxes['scoreRegion']
                       [0: 3],
                       'scale': self.getMap().defs.boxes['scoreRegion']
                       [6: 9],
                       'type': 'box', 'materials':
                       [self._scoreRegionMaterial]}))

    def onBegin(self):

        bs.CoopGameActivity.onBegin(self)
        self._dingSound = bs.getSound('dingSmall')
        self._dingSoundHigh = bs.getSound('dingSmallHigh')

        playerCount = len(self.players)

        hard = False if self._preset in ['proEasy', 'uberEasy'] else True

        if self._preset in ['pro', 'proEasy', 'tournament']:
            self._excludePowerups = ['curse']
            self._haveTnt = True
            self._waves = [
                {'entries': [
                    {'type': bs.BomberBot, 'path': 3 if hard else 2},
                    {'type': bs.BomberBot, 'path': 2},
                    {'type': bs.BomberBot, 'path': 2} if hard else None,
                    {'type': bs.BomberBot, 'path': 2} if playerCount > 1 \
                    else None,
                    {'type': bs.BomberBot, 'path': 1} if hard else None,
                    {'type': bs.BomberBot, 'path': 1} if playerCount > 2 \
                    else None,
                    {'type': bs.BomberBot, 'path': 1} if playerCount > 3 \
                    else None,
                ]},
                {'entries': [
                    {'type': bs.BomberBot, 'path': 1} if hard else None,
                    {'type': bs.BomberBot, 'path': 2} if hard else None,
                    {'type': bs.BomberBot, 'path': 2},
                    {'type': bs.BomberBot, 'path': 2},
                    {'type': bs.BomberBot, 'path': 2} if playerCount > 3 \
                    else None,
                    {'type': bs.ToughGuyBot, 'path': 3},
                    {'type': bs.ToughGuyBot, 'path': 3},
                    {'type': bs.ToughGuyBot, 'path': 3} if hard else None,
                    {'type': bs.ToughGuyBot, 'path': 3} if playerCount > 1 \
                    else None,
                    {'type': bs.ToughGuyBot, 'path': 3} if playerCount > 2 \
                    else None,
                ]},
                {'entries': [
                    {'type': bs.NinjaBot, 'path': 2} if hard else None,
                    {'type': bs.NinjaBot, 'path': 2} if playerCount > 2 \
                    else None,
                    {'type': bs.ChickBot, 'path': 2},
                    {'type': bs.ChickBot, 'path': 2} if playerCount > 1 \
                    else None,
                    {'type': 'spacing', 'duration': 3000},
                    {'type': bs.BomberBot, 'path': 2} if hard else None,
                    {'type': bs.BomberBot, 'path': 2} if hard else None,
                    {'type': bs.BomberBot, 'path': 2},
                    {'type': bs.BomberBot, 'path': 3} if hard else None,
                    {'type': bs.BomberBot, 'path': 3},
                    {'type': bs.BomberBot, 'path': 3},
                    {'type': bs.BomberBot, 'path': 3} if playerCount > 3 \
                    else None,
                ]},
                {'entries': [
                    {'type': bs.ChickBot, 'path': 1} if hard else None,
                    {'type': 'spacing', 'duration': 1000} if hard else None,
                    {'type': bs.ChickBot, 'path': 2},
                    {'type': 'spacing', 'duration': 1000},
                    {'type': bs.ChickBot, 'path': 3},
                    {'type': 'spacing', 'duration': 1000},
                    {'type': bs.ChickBot, 'path': 1} if hard else None,
                    {'type': 'spacing', 'duration': 1000} if hard else None,
                    {'type': bs.ChickBot, 'path': 2},
                    {'type': 'spacing', 'duration': 1000},
                    {'type': bs.ChickBot, 'path': 3},
                    {'type': 'spacing', 'duration': 1000},
                    {'type': bs.ChickBot, 'path': 1} if (playerCount > 1 \
                                                         and hard) else None,
                    {'type': 'spacing', 'duration': 1000},
                    {'type': bs.ChickBot, 'path': 2} if playerCount > 2 \
                    else None,
                    {'type': 'spacing', 'duration': 1000},
                    {'type': bs.ChickBot, 'path': 3} if playerCount > 3 \
                    else None,
                    {'type': 'spacing', 'duration': 1000},
                ]},
                {'entries': [
                    {'type': bs.NinjaBotProShielded if hard else bs.NinjaBot,
                     'path': 1},
                    {'type': bs.ToughGuyBot, 'path': 2} if hard else None,
                    {'type': bs.ToughGuyBot, 'path': 2},
                    {'type': bs.ToughGuyBot, 'path': 2},
                    {'type': bs.ToughGuyBot, 'path': 3} if hard else None,
                    {'type': bs.ToughGuyBot, 'path': 3},
                    {'type': bs.ToughGuyBot, 'path': 3},
                    {'type': bs.ToughGuyBot, 'path': 3} if playerCount > 1 \
                    else None,
                    {'type': bs.ToughGuyBot, 'path': 3} if playerCount > 2 \
                    else None,
                    {'type': bs.ToughGuyBot, 'path': 3} if playerCount > 3 \
                    else None,
                ]},
                {'entries': [
                    {'type': bs.BomberBotProShielded, 'path': 3},
                    {'type': 'spacing', 'duration': 1500},
                    {'type': bs.BomberBotProShielded, 'path': 2},
                    {'type': 'spacing', 'duration': 1500},
                    {'type': bs.BomberBotProShielded, 'path': 1} if hard \
                    else None,
                    {'type': 'spacing', 'duration': 1000} if hard else None,
                    {'type': bs.BomberBotProShielded, 'path': 3},
                    {'type': 'spacing', 'duration': 1500},
                    {'type': bs.BomberBotProShielded, 'path': 2},
                    {'type': 'spacing', 'duration': 1500},
                    {'type': bs.BomberBotProShielded, 'path': 1} if hard \
                    else None,
                    {'type': 'spacing', 'duration': 1500} if hard else None,
                    {'type': bs.BomberBotProShielded, 'path': 3} \
                    if playerCount > 1 else None,
                    {'type': 'spacing', 'duration': 1500},
                    {'type': bs.BomberBotProShielded, 'path': 2} \
                    if playerCount > 2 else None,
                    {'type': 'spacing', 'duration': 1500},
                    {'type': bs.BomberBotProShielded, 'path': 1} \
                    if playerCount > 3 else None,
                ]},
            ]
        elif self._preset in ['uberEasy', 'uber', 'tournamentUber']:
            self._excludePowerups = []
            self._haveTnt = True
            self._waves = [
                {'entries': [
                    {'type': bs.ChickBot, 'path': 1} if hard else None,
                    {'type': bs.ChickBot, 'path': 2},
                    {'type': bs.ChickBot, 'path': 2},
                    {'type': bs.ChickBot, 'path': 3},
                    {'type': bs.ToughGuyBotPro if hard else bs.ToughGuyBot,
                     'point': 'BottomLeft'},
                    {'type': bs.ToughGuyBotPro, 'point': 'BottomRight'} \
                    if playerCount > 2 else None,
                ]},
                {'entries': [
                    {'type': bs.NinjaBot, 'path': 2},
                    {'type': bs.NinjaBot, 'path': 3},
                    {'type': bs.NinjaBot, 'path': 1} if hard else None,
                    {'type': bs.NinjaBot, 'path': 2},
                    {'type': bs.NinjaBot, 'path': 3},
                    {'type': bs.NinjaBot, 'path': 1} if playerCount > 2 \
                    else None,
                ]},
                {'entries': [
                    {'type': bs.BomberBotProShielded, 'path': 1} if hard \
                    else None,
                    {'type': bs.BomberBotProShielded, 'path': 2},
                    {'type': bs.BomberBotProShielded, 'path': 2},
                    {'type': bs.BomberBotProShielded, 'path': 3},
                    {'type': bs.BomberBotProShielded, 'path': 3},
                    {'type': bs.NinjaBot, 'point': 'BottomRight'},
                    {'type': bs.NinjaBot, 'point': 'BottomLeft'} \
                    if playerCount > 2 else None,
                ]},
                {'entries': [
                    {'type': bs.ChickBotPro, 'path': 1} if hard else None,
                    {'type': bs.ChickBotPro, 'path': 1 if hard else 2},
                    {'type': bs.ChickBotPro, 'path': 1 if hard else 2},
                    {'type': bs.ChickBotPro, 'path': 1 if hard else 2},
                    {'type': bs.ChickBotPro, 'path': 1 if hard else 2},
                    {'type': bs.ChickBotPro, 'path': 1 if hard else 2},
                    {'type': bs.ChickBotPro, 'path': 1 if hard else 2} \
                    if playerCount > 1 else None,
                    {'type': bs.ChickBotPro, 'path': 1 if hard else 2} \
                    if playerCount > 3 else None,
                ]},
                {'entries': [
                    {'type': bs.ChickBotProShielded if hard else bs.ChickBotPro,
                     'point': 'BottomLeft'},
                    {'type': bs.ChickBotProShielded, 'point': 'BottomRight'} \
                    if hard else None,
                    {'type': bs.ChickBotProShielded, 'point': 'BottomRight'} \
                    if playerCount > 2 else None,
                    {'type': bs.BomberBot, 'path': 3},
                    {'type': bs.BomberBot, 'path': 3},
                    {'type': 'spacing', 'duration': 5000},
                    {'type': bs.ToughGuyBot, 'path': 2},
                    {'type': bs.ToughGuyBot, 'path': 2},
                    {'type': 'spacing', 'duration': 5000},
                    {'type': bs.ChickBot, 'path': 1} if hard else None,
                    {'type': bs.ChickBot, 'path': 1} if hard else None,
                ]},
                {'entries': [
                    {'type': bs.BomberBotProShielded, 'path': 2},
                    {'type': bs.BomberBotProShielded, 'path': 2} if hard \
                    else None,
                    {'type': bs.MelBot, 'point': 'BottomRight'},
                    {'type': bs.BomberBotProShielded, 'path': 2},
                    {'type': bs.BomberBotProShielded, 'path': 2},
                    {'type': bs.MelBot, 'point': 'BottomRight'} \
                    if playerCount > 2 else None,
                    {'type': bs.BomberBotProShielded, 'path': 2},
                    {'type': bs.PirateBot, 'point': 'BottomLeft'},
                    {'type': bs.BomberBotProShielded, 'path': 2},
                    {'type': bs.BomberBotProShielded, 'path': 2} \
                    if playerCount > 1 else None,
                    {'type': 'spacing', 'duration': 5000},
                    {'type': bs.MelBot, 'point': 'BottomLeft'},
                    {'type': 'spacing', 'duration': 2000},
                    {'type': bs.PirateBot, 'point': 'BottomRight'},
                ]},
            ]
        elif self._preset in ['endless', 'endlessTournament']:
            self._excludePowerups = []
            self._haveTnt = True

        # spit out a few powerups and start dropping more shortly
        self._dropPowerups(standardPoints=True)
        bs.gameTimer(4000, self._startPowerupDrops)
        self.setupLowLifeWarningSound()
        self._updateScores()
        self._bots = bs.BotSet()

        # our TNT spawner (if applicable)
        if self._haveTnt:
            self._tntSpawner = bs.TNTSpawner(position=self._tntSpawnPosition)

        # make sure to stay out of the way of menu/party buttons in the corner
        interfaceType = bs.getEnvironment()['interfaceType']
        lOffs = (-80 if interfaceType == 'small'
                 else -40 if interfaceType == 'medium' else 0)

        self._livesBG = bs.NodeActor(
            bs.newNode(
                'image',
                attrs={'texture': self._heartTex,
                       'modelOpaque': self._heartModelOpaque,
                       'modelTransparent': self._heartModelTransparent,
                       'attach': 'topRight', 'scale': (90, 90),
                       'position': (-110 + lOffs, -50),
                       'color': (1, 0.2, 0.2)}))
        vr = bs.getEnvironment()['vrMode']
        self._startLives = 10
        self._lives = self._startLives
        self._livesText = bs.NodeActor(
            bs.newNode(
                'text',
                attrs={'vAttach': 'top', 'hAttach': 'right', 'hAlign': 'center',
                       'color': (1, 1, 1, 1) if vr else(0.8, 0.8, 0.8, 1.0),
                       'flatness': 1.0 if vr else 0.5, 'shadow': 1.0
                       if vr else 0.5, 'vrDepth': 10,
                       'position': (-113 + lOffs, -69),
                       'scale': 1.3, 'text': str(self._lives)}))

        bs.gameTimer(2000, self._startUpdatingWaves)

    def _handleReachedEnd(self):
        n = bs.getCollisionInfo("opposingNode")
        spaz = n.getDelegate()

        if not spaz.isAlive():
            return  # ignore bodies flying in..

        self._flawless = False
        p = spaz.node.position
        bs.playSound(self._badGuyScoreSound, position=p)
        light = bs.newNode('light',
                           attrs={'position': p,
                                  'radius': 0.5,
                                  'color': (1, 0, 0)})
        bs.animate(light, 'intensity', {0: 0, 100: 1, 500: 0}, loop=False)
        bs.gameTimer(1000, light.delete)
        spaz.handleMessage(bs.DieMessage(immediate=True, how='goal'))

        if self._lives > 0:
            self._lives -= 1
            if self._lives == 0:
                self._bots.stopMoving()
                self.continueOrEndGame()

            self._livesText.node.text = str(self._lives)
            t = 0

            def _safeSetAttr(node, attr, value):
                if node.exists():
                    setattr(node, attr, value)
            for i in range(4):
                bs.gameTimer(t, bs.Call(_safeSetAttr, self._livesText.node,
                                         'color', (1, 0, 0, 1.0)))
                bs.gameTimer(t, bs.Call(_safeSetAttr, self._livesBG.node,
                                          'opacity', 0.5))
                t += 125
                bs.gameTimer(t, bs.Call(_safeSetAttr, self._livesText.node,
                                        'color', (1.0, 1.0, 0.0, 1.0)))
                bs.gameTimer(t, bs.Call(_safeSetAttr, self._livesBG.node,
                                        'opacity', 1.0))
                t += 125
            bs.gameTimer(
                t, bs.Call(
                    _safeSetAttr, self._livesText.node, 'color',
                    (0.8, 0.8, 0.8, 1.0)))

    def onContinue(self):
        self._lives = 3
        self._livesText.node.text = str(self._lives)
        self._bots.startMoving()

    def spawnPlayer(self, player):
        pos = (
            self._spawnCenter[0] + random.uniform(-1.5, 1.5),
            self._spawnCenter[1],
            self._spawnCenter[2] + random.uniform(-1.5, 1.5))
        s = self.spawnPlayerSpaz(player, position=pos)
        if self._preset in ['proEasy', 'uberEasy']:
            s._impactScale = 0.25

        # add the material that causes us to hit the player-wall
        s.pickUpPowerupCallback = self._onPlayerPickedUpPowerup

    def _onPlayerPickedUpPowerup(self, player):
        self._playerHasPickedUpPowerup = True

    def _dropPowerup(self, index, powerupType=None):
        if powerupType is None:
            powerupType = bs.Powerup.getFactory().getRandomPowerupType(
                excludeTypes=self._excludePowerups)
        bs.Powerup(
            position=self.getMap().powerupSpawnPoints[index],
            powerupType=powerupType).autoRetain()

    def _startPowerupDrops(self):
        bs.gameTimer(3000, self._dropPowerups, repeat=True)

    def _dropPowerups(self, standardPoints=False, forceFirst=None):
        """ Generic powerup drop """

        # if its been a minute since our last wave finished emerging, stop
        # giving out land-mine powerups. (prevents players from waiting
        # around for them on purpose and filling the map up)
        if bs.getGameTime() - self._lastWaveEndTime > 60000:
            extraExcludes = ['landMines']
        else:
            extraExcludes = []

        if standardPoints:
            pts = self.getMap().powerupSpawnPoints
            for i, pt in enumerate(pts):
                bs.gameTimer(1000+i*500, bs.Call(
                    self._dropPowerup, i, forceFirst if i == 0 else None))
        else:
            pt = (self._powerupCenter[0]
                  +random.uniform(-1.0*self._powerupSpread[0],
                                  1.0*self._powerupSpread[0]),
                  self._powerupCenter[1],
                  self._powerupCenter[2]+random.uniform(-self._powerupSpread[1],
                                                        self._powerupSpread[1]))

            # drop one random one somewhere..
            bs.Powerup(position=pt,
                       powerupType=bs.Powerup.getFactory().getRandomPowerupType(
                           excludeTypes=self._excludePowerups+extraExcludes)
            ).autoRetain()

    def endGame(self):
        # FIXME FIXME FIXME - if we don't start our bots moving again we get
        # stuck this is because the bot-set never prunes itself while movement
        # is off and onFinalize never gets called for some bots because
        # _pruneDeadObjects() saw them as dead and pulled them off the
        # weak-ref lists. this is an architectural issue; can hopefully fix
        # this by having _actorWeakRefs not look at exists()
        self._bots.startMoving()
        bs.gameTimer(1, bs.Call(self.doEnd, 'defeat'))
        bs.playMusic(None)
        bs.playSound(self._playerDeathSound)

    def doEnd(self, outcome):

        if outcome == 'defeat':
            delay = 2000
            self.fadeToRed()
        else:
            delay = 0

        if self._wave >= 2:
            score = self._score.get()
            failMessage = None
        else:
            score = None
            failMessage = 'Reach wave 2 to rank.'

        self.end(
            delay=delay,
            results={'outcome': outcome, 'score': score,
                     'failMessage': failMessage,
                     'playerInfo': self.initialPlayerInfo})

    def _onGotScoresToBeat(self, scores):
        self._showStandardScoresToBeatUI(scores)

    def _updateWaves(self):

        # if we have no living bots, go to the next wave
        if (self._canEndWave and not self._bots.haveLivingBots()
            and not self._gameOver and self._lives > 0):

            self._canEndWave = False
            self._timeBonusTimer = None
            self._timeBonusText = None

            if self._preset in ['endless', 'endlessTournament']:
                won = False
            else:
                won = (self._wave == len(self._waves))

            # reward time bonus
            baseDelay = 4000 if won else 0
            if self._timeBonus > 0:
                bs.gameTimer(0, bs.Call(bs.playSound, self._cashRegisterSound))
                bs.gameTimer(baseDelay, bs.Call(
                    self._awardTimeBonus, self._timeBonus))
                baseDelay += 1000

            # reward flawless bonus
            if self._wave > 0 and self._flawless:
                bs.gameTimer(baseDelay, self._awardFlawlessBonus)
                baseDelay += 1000

            self._flawless = True  # reset

            if won:

                # completion achievements
                if self._preset in ['pro', 'proEasy']:
                    self._awardAchievement('Pro Runaround Victory', sound=False)
                    if self._lives == self._startLives:
                        self._awardAchievement('The Wall', sound=False)
                    if not self._playerHasPickedUpPowerup:
                        self._awardAchievement('Precision Bombing', sound=False)

                elif self._preset in ['uber', 'uberEasy']:
                    self._awardAchievement(
                        'Uber Runaround Victory', sound=False)
                    if self._lives == self._startLives:
                        self._awardAchievement('The Great Wall', sound=False)
                    if not self._aPlayerHasBeenKilled:
                        self._awardAchievement('Stayin\' Alive', sound=False)

                # give remaining players some points and have them celebrate
                self.showZoomMessage(
                    bs.Lstr(resource='victoryText'),
                    scale=1.0, duration=4000)

                self.celebrate(10000)

                bs.gameTimer(baseDelay, self._awardLivesBonus)
                baseDelay += 1000

                bs.gameTimer(baseDelay, self._awardCompletionBonus)
                baseDelay += 850

                bs.playSound(self._winSound)
                self.cameraFlash()
                bs.playMusic('Victory')
                self._gameOver = True
                bs.gameTimer(baseDelay, bs.Call(self.doEnd, 'victory'))
                return

            self._wave += 1

            # short celebration after waves
            if self._wave > 1:
                self.celebrate(500)

            bs.gameTimer(baseDelay, self._startNextWave)

    def _awardCompletionBonus(self):
        bonus = 200
        bs.playSound(self._cashRegisterSound)
        bs.PopupText(
            bs.Lstr(
                value='+${A} ${B}',
                subs=[('${A}', str(bonus)),
                      ('${B}', bs.Lstr(resource='completionBonusText'))]),
            color=(0.7, 0.7, 1.0, 1),
            scale=1.6, position=(0, 1.5, -1)).autoRetain()
        self._score.add(bonus)
        self._updateScores()

    def _awardLivesBonus(self,):
        bonus = self._lives * 30
        bs.playSound(self._cashRegisterSound)
        bs.PopupText(
            bs.Lstr(
                value='+${A} ${B}',
                subs=[('${A}', str(bonus)),
                      ('${B}', bs.Lstr(resource='livesBonusText'))]),
            color=(0.7, 1.0, 0.3, 1),
            scale=1.3, position=(0, 1, -1)).autoRetain()
        self._score.add(bonus)
        self._updateScores()

    def _awardTimeBonus(self, bonus):
        bs.playSound(self._cashRegisterSound)
        bs.PopupText(
            bs.Lstr(
                value='+${A} ${B}',
                subs=[('${A}', str(bonus)),
                      ('${B}', bs.Lstr(resource='timeBonusText'))]),
            color=(1, 1, 0.5, 1),
            scale=1.0, position=(0, 3, -1)).autoRetain()

        self._score.add(self._timeBonus)
        self._updateScores()

    def _awardFlawlessBonus(self):
        bs.playSound(self._cashRegisterSound)
        bs.PopupText(
            bs.Lstr(
                value='+${A} ${B}',
                subs=[('${A}', str(self._flawlessBonus)),
                      ('${B}', bs.Lstr(resource='perfectWaveText'))]),
            color=(1, 1, 0.2, 1),
            scale=1.2, position=(0, 2, -1)).autoRetain()

        self._score.add(self._flawlessBonus)
        self._updateScores()

    def _startTimeBonusTimer(self):
        self._timeBonusTimer = bs.Timer(
            1000, self._updateTimeBonus, repeat=True)

    def _startNextWave(self):

        self.showZoomMessage(
            bs.Lstr(
                value='${A} ${B}',
                subs=[('${A}', bs.Lstr(resource='waveText')),
                      ('${B}', str(self._wave))]),
            scale=1.0, duration=1000, trail=True)
        bs.gameTimer(400, bs.Call(bs.playSound, self._newWaveSound))
        t = 0
        baseDelay = 500
        botAngle = random.random()*360.0
        spawnTime = 100
        botTypes = []

        if self._preset in ['endless', 'endlessTournament']:

            level = self._wave
            targetPoints = (level+1) * 8.0
            groupCount = random.randint(1, 3)
            entries = []

            spazTypes = []
            if level < 6:
                spazTypes += [[bs.BomberBot, 5.0]]
            if level < 10:
                spazTypes += [[bs.ToughGuyBot, 5.0]]
            if level < 15:
                spazTypes += [[bs.ChickBot, 6.0]]
            if level > 5:
                spazTypes += [[bs.ChickBotPro, 7.5]]*(1+(level-5)/7)
            if level > 2:
                spazTypes += [[bs.BomberBotProShielded, 8.0]]*(1+(level-2)/6)
            if level > 6:
                spazTypes += [[bs.ChickBotProShielded, 12.0]]*(1+(level-6)/5)
            if level > 1:
                spazTypes += [[bs.NinjaBot, 10.0]]*(1+(level-1)/4)
            if level > 7:
                spazTypes += [[bs.NinjaBotProShielded, 15.0]]*(1+(level-7)/3)

            # bot type, their effect on target points
            defenderTypes = [[bs.BomberBot, 0.9],
                             [bs.ToughGuyBot, 0.9],
                             [bs.ChickBot, 0.85]]
            if level > 2:
                defenderTypes += [[bs.NinjaBot, 0.75]]
            if level > 4:
                defenderTypes += [[bs.MelBot, 0.7]]*(1+(level-5)/6)
            if level > 6:
                defenderTypes += [[bs.PirateBot, 0.7]]*(1+(level-5)/5)
            if level > 8:
                defenderTypes += [[bs.ToughGuyBotProShielded,
                                   0.65]]*(1+(level-5)/4)
            if level > 10:
                defenderTypes += [[bs.ChickBotProShielded, 0.6]]*(1+(level-6)/3)

            for group in range(groupCount):
                thisTargetPoints = targetPoints/groupCount

                # adding spacing makes things slightly harder
                r = random.random()
                if r < 0.07:
                    spacing = 1500
                    thisTargetPoints *= 0.85
                elif r < 0.15:
                    spacing = 1000
                    thisTargetPoints *= 0.9
                else:
                    spacing = 0

                path = random.randint(1, 3)
                # dont allow hard paths on early levels
                if level < 3:
                    if path == 1:
                        path = 3
                # easy path
                if path == 3:
                    pass
                # harder path
                elif path == 2:
                    thisTargetPoints *= 0.8
                # even harder path
                elif path == 1:
                    thisTargetPoints *= 0.7
                # looping forward
                elif path == 4:
                    thisTargetPoints *= 0.7
                # looping backward
                elif path == 5:
                    thisTargetPoints *= 0.7
                # random
                elif path == 6:
                    thisTargetPoints *= 0.7

                def _addDefender(defenderType, point):
                    # entries.append()
                    return thisTargetPoints * defenderType[1], {
                        'type': defenderType[0],
                        'point': point}

                # add defenders
                defenderType1 = defenderTypes[random.randrange(
                    len(defenderTypes))]
                defenderType2 = defenderTypes[random.randrange(
                    len(defenderTypes))]
                defender1 = defender2 = None
                if ((group == 0) or (group == 1 and level > 3)
                        or (group == 2 and level > 5)):
                    if random.random() < min(0.75, (level-1)*0.11):
                        thisTargetPoints, defender1 = _addDefender(
                            defenderType1, 'BottomLeft')
                    if random.random() < min(0.75, (level-1)*0.04):
                        thisTargetPoints, defender2 = _addDefender(
                            defenderType2, 'BottomRight')

                spazType = spazTypes[random.randrange(len(spazTypes))]
                memberCount = max(1, int(round(thisTargetPoints/spazType[1])))
                for i, member in enumerate(range(memberCount)):
                    if path == 4:
                        thisPath = i % 3  # looping forward
                    elif path == 5:
                        thisPath = 3-(i % 3)  # looping backward
                    elif path == 6:
                        thisPath = random.randint(1, 3)  # random
                    else:
                        thisPath = path
                    entries.append({'type': spazType[0], 'path': thisPath})
                    if spacing != 0:
                        entries.append({'type': 'spacing', 'duration': spacing})

                if defender1 is not None:
                    entries.append(defender1)
                if defender2 is not None:
                    entries.append(defender2)

                # some spacing between groups
                r = random.random()
                if r < 0.1:
                    spacing = 5000
                elif r < 0.5:
                    spacing = 1000
                else:
                    spacing = 1
                entries.append({'type': 'spacing', 'duration': spacing})

            wave = {'entries': entries}

        else:
            wave = self._waves[self._wave-1]

        try:
            botAngle = wave['baseAngle']
        except Exception:
            botAngle = 0

        botTypes += wave['entries']

        self._timeBonusMult = 1.0
        thisFlawlessBonus = 0

        nonRunnerSpawnTime = 1000
        for info in botTypes:
            if info is None:
                continue

            botType = info['type']

            if botType is not None:

                if botType == 'nonRunnerDelay':
                    nonRunnerSpawnTime += info['duration']
                    continue

                if botType == 'spacing':
                    t += info['duration']
                    continue
                else:
                    try:
                        path = info['path']
                    except Exception:
                        path = random.randint(1, 3)
                    self._timeBonusMult += botType.pointsMult * 0.02
                    thisFlawlessBonus += botType.pointsMult * 5

            # if its got a position, use that
            try:
                point = info['point']
            except Exception:
                point = 'Start'

            # space our our slower bots
            delay = baseDelay
            delay /= self._getBotSpeed(botType)

            t += int(delay*0.5)
            bs.gameTimer(
                t, bs.Call(
                    self.addBotAtPoint, point,
                    {'type': botType, 'path': path},
                    100 if point == 'Start' else nonRunnerSpawnTime))
            t += int(delay*0.5)

        # we can end the wave after all the spawning happens
        bs.gameTimer(t-int(delay*0.5)+nonRunnerSpawnTime+10,
                     self._setCanEndWave)

        # reset our time bonus
        # in this game we use a constant time bonus so it erodes away in
        # roughly the same time (since the time limit a wave can take is
        # relatively constant) ..we then post-multiply a modifier to adjust
        # points
        self._timeBonus = 150
        self._flawlessBonus = thisFlawlessBonus

        self._timeBonusText = bs.NodeActor(
            bs.newNode(
                'text',
                attrs={'vAttach': 'top', 'hAttach': 'center',
                       'hAlign': 'center', 'color': (1, 1, 0.0, 1),
                       'shadow': 1.0, 'vrDepth': -30, 'flatness': 1.0,
                       'position': (0, -60),
                       'scale': 0.8, 'text': bs.Lstr(
                           value='${A}: ${B}',
                           subs=[('${A}', bs.Lstr(
                               resource='timeBonusText')),
                               ('${B}',
                                str(
                                    int(
                                        self._timeBonus *
                                        self._timeBonusMult)))])}))

        bs.gameTimer(t, self._startTimeBonusTimer)

        # keep track of when this wave finishes emerging - we wanna
        # stop dropping land-mines powerups at some point
        # (otherwise a crafty player could fill the whole map with them)
        self._lastWaveEndTime = bs.getGameTime()+t
        self._waveText = bs.NodeActor(
            bs.newNode(
                'text',
                attrs={'vAttach': 'top', 'hAttach': 'center',
                       'hAlign': 'center', 'vrDepth': -10, 'color':
                       (1, 1, 1, 1),
                       'shadow': 1.0, 'flatness': 1.0, 'position': (0, -40),
                       'scale': 1.3, 'text': bs.Lstr(
                           value='${A} ${B}',
                           subs=[('${A}', bs.Lstr(resource='waveText')),
                                 ('${B}', str(self._wave) +
                                  (''
                                   if self._preset
                                   in ['endless', 'endlessTournament']
                                   else('/' + str(len(self._waves)))))])}))

    def _onBotSpawn(self, path, spaz):
        # add our custom update callback and set some info for this bot..
        spazType = type(spaz)
        spaz.updateCallback = self._updateBot
        spaz.rWalkRow = path
        spaz.rWalkSpeed = self._getBotSpeed(spazType)

    def addBotAtPoint(self, point, spazInfo, spawnTime=100):
        # dont add if the game has ended
        if self._gameOver:
            return
        pt = self.getMap().defs.points['botSpawn'+point][:3]
        self._bots.spawnBot(
            spazInfo['type'],
            pos=pt, spawnTime=spawnTime, onSpawnCall=bs.Call(
                self._onBotSpawn, spazInfo['path']))

    def _updateTimeBonus(self):
        self._timeBonus = int(self._timeBonus * 0.91)
        if self._timeBonus > 0 and self._timeBonusText is not None:
            self._timeBonusText.node.text = bs.Lstr(
                value='${A}: ${B}',
                subs=[('${A}', bs.Lstr(resource='timeBonusText')),
                      ('${B}', str(
                          int(self._timeBonus * self._timeBonusMult)))])
        else:
            self._timeBonusText = None

    def _startUpdatingWaves(self):
        self._waveUpdateTimer = bs.Timer(2000, self._updateWaves, repeat=True)

    def _updateScores(self):

        score = self._score.get()
        if self._preset == 'endless':
            if score >= 500:
                self._awardAchievement('Runaround Master')
            if score >= 1000:
                self._awardAchievement('Runaround Wizard')
            if score >= 2000:
                self._awardAchievement('Runaround God')

        self._scoreBoard.setTeamValue(self.teams[0], score, maxScore=None)

    def _updateBot(self, bot):

        speed = bot.rWalkSpeed
        t = bot.node.position

        boxes = self.getMap().defs.boxes

        # bots in row 1 attempt the high road..
        if bot.rWalkRow == 1:
            if bs.isPointInBox(t, boxes['b4']):
                bot.node.moveUpDown = speed
                bot.node.moveLeftRight = 0
                bot.node.run = 0.0
                return True

        # row 1 and 2 bots attempt the middle road..
        if bot.rWalkRow in [1, 2]:
            if bs.isPointInBox(t, boxes['b1']):
                bot.node.moveUpDown = speed
                bot.node.moveLeftRight = 0
                bot.node.run = 0.0
                return True

        # *all* bots settle for the third row
        if bs.isPointInBox(t, boxes['b7']):
            bot.node.moveUpDown = speed
            bot.node.moveLeftRight = 0
            bot.node.run = 0.0
            return True
        elif bs.isPointInBox(t, boxes['b2']):
            bot.node.moveUpDown = -speed
            bot.node.moveLeftRight = 0
            bot.node.run = 0.0
            return True
        elif bs.isPointInBox(t, boxes['b3']):
            bot.node.moveUpDown = -speed
            bot.node.moveLeftRight = 0
            bot.node.run = 0.0
            return True
        elif bs.isPointInBox(t, boxes['b5']):
            bot.node.moveUpDown = -speed
            bot.node.moveLeftRight = 0
            bot.node.run = 0.0
            return True
        elif bs.isPointInBox(t, boxes['b6']):
            bot.node.moveUpDown = speed
            bot.node.moveLeftRight = 0
            bot.node.run = 0.0
            return True
        elif (bs.isPointInBox(t, boxes['b8'])
              and not bs.isPointInBox(t, boxes['b9'])) or t == (0.0, 0.0, 0.0):
            # default to walking right if we're still in the walking area
            bot.node.moveLeftRight = speed
            bot.node.moveUpDown = 0
            bot.node.run = 0.0
            return True

        # revert to normal bot behavior otherwise..
        return False

    def handleMessage(self, m):

        if isinstance(m, bs.PlayerScoredMessage):
            self._score.add(m.score)
            self._updateScores()

        # respawn dead players
        elif isinstance(m, bs.PlayerSpazDeathMessage):
            self._aPlayerHasBeenKilled = True
            player = m.spaz.getPlayer()
            if player is None:
                bs.printError('FIXME: getPlayer() should no'
                              ' longer ever be returning None')
                return
            if not player.exists():
                return

            self.scoreSet.playerLostSpaz(player)

            # respawn them shortly
            respawnTime = 2000+len(self.initialPlayerInfo)*1000

            player.gameData['respawnTimer'] = bs.Timer(
                respawnTime, bs.Call(self.spawnPlayerIfExists, player))
            player.gameData['respawnIcon'] = bs.RespawnIcon(player, respawnTime)

        elif isinstance(m, bs.SpazBotDeathMessage):
            if m.how == 'goal':
                return
            pts, importance = m.badGuy.getDeathPoints(m.how)
            if m.killerPlayer is not None:
                try:
                    target = m.badGuy.node.position
                except Exception:
                    target = None
                try:
                    if m.killerPlayer is not None and m.killerPlayer.exists():
                        self.scoreSet.playerScored(
                            m.killerPlayer, pts, target=target, kill=True,
                            screenMessage=False, importance=importance)
                        bs.playSound(
                            self._dingSound
                            if importance == 1 else self._dingSoundHigh,
                            volume=0.6)
                except Exception as e:
                    print 'EXC in Runaround handling SpazBotDeathMessage:', e
            # normally we pull scores from the score-set, but if there's no
            # player lets be explicit..
            else:
                self._score.add(pts)
            self._updateScores()

        else:
            self.__superHandleMessage(m)

    def __superHandleMessage(self, m):
        super(RunaroundGame, self).handleMessage(m)

    def _getBotSpeed(self, botType):
        if botType == bs.BomberBot:
            return 0.48
        elif botType == bs.BomberBotPro:
            return 0.48
        elif botType == bs.BomberBotProShielded:
            return 0.48
        elif botType == bs.ToughGuyBot:
            return 0.57
        elif botType == bs.ToughGuyBotPro:
            return 0.57
        elif botType == bs.ToughGuyBotProShielded:
            return 0.57
        elif botType == bs.ChickBot:
            return 0.73
        elif botType == bs.ChickBotPro:
            return 0.78
        elif botType == bs.ChickBotProShielded:
            return 0.78
        elif botType == bs.NinjaBot:
            return 1.0
        elif botType == bs.NinjaBotProShielded:
            return 1.0
        elif botType == bs.PirateBot:
            return 1.0
        elif botType == bs.MelBot:
            return 0.5
        else:
            raise Exception('Invalid bot type to _getBotSpeed(): '+str(botType))

    def _setCanEndWave(self):
        self._canEndWave = True
