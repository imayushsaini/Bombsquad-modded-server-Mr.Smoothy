import bs
import random
import math
import weakref


class OnslaughtGame(bs.CoopGameActivity):

    tips = [
        'Hold any button to run.  (Trigger buttons work well if you have them)',
        'Try tricking enemies into killing eachother or running off cliffs.',
        'Try \'Cooking off\' bombs for a second or two before throwing them.',
        'It\'s easier to win with a friend or two helping.',
        'If you stay in one place, you\'re toast. Run and dodge to survive..',
        'Practice using your momentum to throw bombs more accurately.',
        'Your punches do much more damage if you are running or spinning.']

    @classmethod
    def getName(cls):
        return 'Onslaught'

    @classmethod
    def getDescription(cls, sessionType):
        return "Defeat all enemies."

    def __init__(self, settings={}):

        try:
            self._preset = settings['preset']
        except Exception:
            self._preset = 'training'

        if self._preset in [
            'training', 'trainingEasy', 'pro', 'proEasy', 'endless',
                'endlessTournament']:
            settings['map'] = 'Doom Shroom'
        else:
            settings['map'] = 'Courtyard'

        bs.CoopGameActivity.__init__(self, settings)

        # show messages when players die since it matters here..
        self.announcePlayerDeaths = True

        self._newWaveSound = bs.getSound('scoreHit01')
        self._winSound = bs.getSound("score")
        self._cashRegisterSound = bs.getSound('cashRegister')
        self._aPlayerHasBeenHurt = False
        self._playerHasDroppedBomb = False

        # fixme - should use standard map defs..
        if settings['map'] == 'Doom Shroom':
            self._spawnCenter = (0, 3, -5)
            self._tntSpawnPosition = (0, 3, -5)
            self._powerupCenter = (0, 5, -3.6)
            self._powerupSpread = (6, 4)
        elif settings['map'] == 'Courtyard':
            self._spawnCenter = (0, 3, -2)
            self._tntSpawnPosition = (0, 3, 2.1)
            self._powerupCenter = (0, 5, -1.6)
            self._powerupSpread = (4.6, 2.7)
        else:
            raise Exception("Unsupported map: "+str(settings['map']))

    def onTransitionIn(self):

        bs.CoopGameActivity.onTransitionIn(self)

        # show special landmine tip on rookie preset
        if self._preset in ['rookie', 'rookieEasy']:
            # show once per session only (then we revert to regular tips)
            if not hasattr(bs.getSession(), '_gShowedOnslaughtLandMineTip'):
                bs.getSession()._gShowedOnslaughtLandMineTip = True
                self.tips = [
                    {'tip': "Land-mines are a good way to stop speedy enemies.",
                     'icon': bs.getTexture('powerupLandMines'),
                     'sound': bs.getSound('ding')}]

        # show special tnt tip on pro preset
        if self._preset in ['pro', 'proEasy']:
            # show once per session only (then we revert to regular tips)
            if not hasattr(bs.getSession(), '_gShowedOnslaughtTntTip'):
                bs.getSession()._gShowedOnslaughtTntTip = True
                self.tips = [{
                    'tip':
                    "Take out a group of enemies by\nsetting"
                    " off a bomb near a TNT box.",
                    'icon': bs.getTexture('tnt'),
                    'sound': bs.getSound('ding')}]

        # show special curse tip on uber preset
        if self._preset in ['uber', 'uberEasy']:
            # show once per session only (then we revert to regular tips)
            if not hasattr(bs.getSession(), '_gShowedOnslaughtCurseTip'):
                bs.getSession()._gShowedOnslaughtCurseTip = True
                self.tips = [{
                    'tip':
                    "Curse boxes turn you into a ticking time bomb.\n"
                    "The only cure is to quickly grab a health-pack.",
                    'icon': bs.getTexture('powerupCurse'),
                    'sound': bs.getSound('ding')}]

        self._spawnInfoText = bs.NodeActor(
            bs.newNode(
                "text",
                attrs={'position': (15, -130),
                       'hAttach': "left", 'vAttach': "top", 'scale': 0.55,
                       'color': (0.3, 0.8, 0.3, 1.0),
                       'text': ''}))
        bs.playMusic('Onslaught')

        self._scoreBoard = bs.ScoreBoard(
            label=bs.Lstr(resource='scoreText'),
            scoreSplit=0.5)
        self._gameOver = False
        self._wave = 0
        self._canEndWave = True
        # we use this in place of a regular int to make it harder to hack scores
        self._score = bs.SecureInt(0)
        self._timeBonus = 0

    def onBegin(self):

        bs.CoopGameActivity.onBegin(self)
        playerCount = len(self.players)
        self._dingSound = bs.getSound('dingSmall')
        self._dingSoundHigh = bs.getSound('dingSmallHigh')

        hard = False if self._preset in [
            'trainingEasy', 'rookieEasy', 'proEasy', 'uberEasy'] else True

        if self._preset in ['training', 'trainingEasy']:
            import bsUtils
            bsUtils.ControlsHelpOverlay(
                delay=3000, lifespan=10000, bright=True).autoRetain()

            self._haveTnt = False
            self._excludePowerups = ['curse', 'landMines']
            self._waves = [

                {'baseAngle': 195,
                 'entries': ([
                     {'type': bs.BomberBotLame, 'spacing': 5},
                 ] * playerCount)},

                {'baseAngle': 130,
                 'entries': ([
                     {'type': bs.ToughGuyBotLame, 'spacing': 5},
                 ] * playerCount)},

                {'baseAngle': 195,
                 'entries': ([
                     {'type': bs.BomberBotLame, 'spacing': 10},
                 ] * (playerCount+1))},

                {'baseAngle': 130,
                 'entries': ([
                     {'type': bs.ToughGuyBotLame, 'spacing': 10},
                 ] * (playerCount+1))},

                {'baseAngle': 130,
                 'entries': ([
                     {'type': bs.ToughGuyBotLame,
                      'spacing': 5} if playerCount > 1 else None,
                     {'type': bs.ToughGuyBotLame, 'spacing': 5},
                     {'type': None, 'spacing': 30},
                     {'type': bs.BomberBotLame,
                      'spacing': 5} if playerCount > 3 else None,
                     {'type': bs.BomberBotLame, 'spacing': 5},
                     {'type': None, 'spacing': 30},
                     {'type': bs.ToughGuyBotLame, 'spacing': 5},
                     {'type': bs.ToughGuyBotLame,
                      'spacing': 5} if playerCount > 2 else None,
                 ])},

                {'baseAngle': 195,
                 'entries': ([
                     {'type': bs.ChickBot, 'spacing': 90},
                     {'type': bs.ChickBot,
                      'spacing': 90} if playerCount > 1 else None
                 ])},
            ]

        elif self._preset in ['rookie', 'rookieEasy']:
            self._haveTnt = False
            self._excludePowerups = ['curse']
            self._waves = [

                {'entries': [
                    {'type': bs.NinjaBot,
                     'point': 'LeftUpperMore'} if playerCount > 2 else None,
                    {'type': bs.NinjaBot, 'point': 'LeftUpper'},
                ]},

                {'entries': [
                    {'type': bs.BomberBotStaticLame, 'point': 'TurretTopRight'},
                    {'type': bs.ToughGuyBotLame, 'point': 'RightUpper'},
                    {'type': bs.ToughGuyBotLame, 'point': 'RightLower'} \
                    if playerCount > 1 else None,
                    {'type': bs.BomberBotStaticLame,
                     'point': 'TurretBottomRight'} if playerCount > 2 else None,
                ]},

                {'entries': [
                    {'type': bs.BomberBotStaticLame,
                     'point': 'TurretBottomLeft'},
                    {'type': bs.ChickBot,
                     'point': 'Left'},
                    {'type': bs.ChickBot,
                     'point': 'LeftLower'} if playerCount > 1 else None,
                    {'type': bs.ChickBot,
                     'point': 'LeftUpper'} if playerCount > 2 else None,
                ]},
                {'entries': [
                    {'type': bs.ToughGuyBotLame, 'point': 'TopRight'},
                    {'type': bs.ToughGuyBot,
                     'point': 'TopHalfRight'} if playerCount > 1 else None,
                    {'type': bs.ToughGuyBotLame, 'point': 'TopLeft'},
                    {'type': bs.ToughGuyBotLame,
                     'point': 'TopHalfLeft'} if playerCount > 2 else None,
                    {'type': bs.ToughGuyBot, 'point': 'Top'},
                    {'type': bs.BomberBotStaticLame,
                     'point': 'TurretTopMiddle'},
                ]},

                {'entries': [
                    {'type': bs.ChickBotStatic, 'point': 'TurretBottomLeft'},
                    {'type': bs.ChickBotStatic, 'point': 'TurretBottomRight'},
                    {'type': bs.ChickBot, 'point': 'Bottom'},
                    {'type': bs.ChickBot,
                     'point': 'BottomHalfRight'} if playerCount > 1 else None,
                    {'type': bs.ChickBot,
                     'point': 'BottomHalfLeft'} if playerCount > 2 else None,
                ]},

                {'entries': [
                    {'type': bs.BomberBotStaticLame, 'point': 'TurretTopLeft'},
                    {'type': bs.BomberBotStaticLame, 'point': 'TurretTopRight'},
                    {'type': bs.NinjaBot, 'point': 'Bottom'},
                    {'type': bs.NinjaBot,
                     'point': 'BottomHalfLeft'} if playerCount > 1 else None,
                    {'type': bs.NinjaBot,
                     'point': 'BottomHalfRight'} if playerCount > 2 else None,
                ]},
            ]

        elif self._preset in ['pro', 'proEasy']:
            self._excludePowerups = ['curse']
            self._haveTnt = True
            self._waves = [

                {'baseAngle': -50,
                 'entries': ([
                     {'type': bs.ToughGuyBot,
                      'spacing': 12} if playerCount > 3 else None,
                     {'type': bs.ToughGuyBot, 'spacing': 12},
                     {'type': bs.BomberBot, 'spacing': 6},
                     {'type': bs.BomberBot,
                         'spacing': 6} if self._preset == 'pro' else None,
                     {'type': bs.BomberBot,
                      'spacing': 6} if playerCount > 1 else None,
                     {'type': bs.ToughGuyBot, 'spacing': 12},
                     {'type': bs.ToughGuyBot,
                      'spacing': 12} if playerCount > 2 else None,
                 ])},

                {'baseAngle': 180,
                 'entries': ([
                     {'type': bs.ToughGuyBot,
                      'spacing': 6} if playerCount > 3 else None,
                     {'type': bs.ToughGuyBot,
                         'spacing': 6} if self._preset == 'pro' else None,
                     {'type': bs.ToughGuyBot, 'spacing': 6},
                     {'type': bs.NinjaBot, 'spacing': 45},
                     {'type': bs.NinjaBot,
                      'spacing': 45} if playerCount > 1 else None,
                     {'type': bs.ToughGuyBot, 'spacing': 6},
                     {'type': bs.ToughGuyBot,
                         'spacing': 6} if self._preset == 'pro' else None,
                     {'type': bs.ToughGuyBot,
                      'spacing': 6} if playerCount > 2 else None,
                 ])},

                {'baseAngle': 0,
                 'entries': ([
                     {'type': bs.NinjaBot, 'spacing': 30},
                     {'type': bs.ChickBot, 'spacing': 30},
                     {'type': bs.ChickBot, 'spacing': 30},
                     {'type': bs.ChickBot,
                         'spacing': 30} if self._preset == 'pro' else None,
                     {'type': bs.ChickBot,
                      'spacing': 30} if playerCount > 1 else None,
                     {'type': bs.ChickBot,
                      'spacing': 30} if playerCount > 3 else None,
                     {'type': bs.NinjaBot, 'spacing': 30},
                 ])},

                {'baseAngle': 90,
                 'entries': ([
                     {'type': bs.MelBot, 'spacing': 50},
                     {'type': bs.MelBot,
                      'spacing': 50} if self._preset == 'pro' else None,
                     {'type': bs.MelBot, 'spacing': 50},
                     {'type': bs.MelBot,
                      'spacing': 50} if playerCount > 1 else None,
                     {'type': bs.MelBot,
                      'spacing': 50} if playerCount > 3 else None,
                 ])},

                {'baseAngle': 0,
                 'entries': ([
                     {'type': bs.ChickBot, 'spacing': 72},
                     {'type': bs.ChickBot, 'spacing': 72},
                     {'type': bs.ChickBot,
                         'spacing': 72} if self._preset == 'pro' else None,
                     {'type': bs.ChickBot, 'spacing': 72},
                     {'type': bs.ChickBot, 'spacing': 72},
                     {'type': bs.ChickBot,
                      'spacing': 36} if playerCount > 2 else None,
                 ])},

                {'baseAngle': 30,
                 'entries': ([
                     {'type': bs.NinjaBotProShielded, 'spacing': 50},
                     {'type': bs.NinjaBotProShielded, 'spacing': 50},
                     {'type': bs.NinjaBotProShielded,
                         'spacing': 50} if self._preset == 'pro' else None,
                     {'type': bs.NinjaBotProShielded,
                         'spacing': 50} if playerCount > 1 else None,
                     {'type': bs.NinjaBotProShielded,
                         'spacing': 50} if playerCount > 2 else None,
                 ])},
            ]

        elif self._preset in ['uber', 'uberEasy']:

            # show controls help in kiosk mode
            if bs.getEnvironment()['kioskMode']:
                import bsUtils
                bsUtils.ControlsHelpOverlay(
                    delay=3000, lifespan=10000, bright=True).autoRetain()

            self._haveTnt = True
            self._excludePowerups = []
            self._waves = [

                {'entries': [
                    {'type': bs.BomberBotProStatic,
                     'point': 'TurretTopMiddleLeft'} if hard else None,
                    {'type': bs.BomberBotProStatic,
                     'point': 'TurretTopMiddleRight'},
                    {'type': bs.BomberBotProStatic,
                     'point': 'TurretTopLeft'} if playerCount > 2 else None,
                    {'type': bs.PirateBot, 'point': 'TopRight'},
                    {'type': 'delay', 'duration': 4000},
                    {'type': bs.PirateBot, 'point': 'TopLeft'},
                ]},

                {'entries': [
                    {'type': bs.NinjaBot, 'point': 'Left'},
                    {'type': bs.NinjaBot, 'point': 'Right'},
                    {'type': bs.NinjaBot,
                     'point': 'RightUpperMore'} if playerCount > 2 else None,
                    {'type': bs.BomberBotProStatic, 'point': 'TurretTopLeft'},
                    {'type': bs.BomberBotProStatic, 'point': 'TurretTopRight'},
                ]},

                {'entries': [
                    {'type': bs.ChickBotPro, 'point': 'TopRight'},
                    {'type': bs.ChickBotPro,
                     'point': 'RightUpperMore'} if playerCount > 1 else None,
                    {'type': bs.ChickBotPro, 'point': 'RightUpper'},
                    {'type': bs.ChickBotPro,
                     'point': 'RightLower'} if hard else None,
                    {'type': bs.ChickBotPro,
                     'point': 'RightLowerMore'} if playerCount > 2 else None,
                    {'type': bs.ChickBotPro, 'point': 'BottomRight'},
                ]},

                {'entries': [
                    {'type': bs.NinjaBotProShielded, 'point': 'BottomRight'},
                    {'type': bs.NinjaBotProShielded,
                     'point': 'Bottom'} if playerCount > 2 else None,
                    {'type': bs.NinjaBotProShielded, 'point': 'BottomLeft'},
                    {'type': bs.NinjaBotProShielded,
                     'point': 'Top'} if hard else None,
                    {'type': bs.BomberBotProStatic, 'point': 'TurretTopMiddle'},
                ]},

                {'entries': [
                    {'type': bs.PirateBot, 'point': 'LeftUpper'},
                    {'type': 'delay', 'duration': 1000},
                    {'type': bs.ToughGuyBotProShielded, 'point': 'LeftLower'},
                    {'type': bs.ToughGuyBotProShielded,
                     'point': 'LeftLowerMore'},
                    {'type': 'delay', 'duration': 4000},
                    {'type': bs.PirateBot, 'point': 'RightUpper'},
                    {'type': 'delay', 'duration': 1000},
                    {'type': bs.ToughGuyBotProShielded, 'point': 'RightLower'},
                    {'type': bs.ToughGuyBotProShielded,
                     'point': 'RightUpperMore'},
                    {'type': 'delay', 'duration': 4000},
                    {'type': bs.PirateBot, 'point': 'Left'},
                    {'type': 'delay', 'duration': 5000},
                    {'type': bs.PirateBot, 'point': 'Right'},
                ]},

                {'entries': [
                    {'type': bs.BomberBotProStatic,
                     'point': 'TurretTopLeft'},
                    {'type': bs.BomberBotProStatic,
                     'point': 'TurretTopRight'},
                    {'type': bs.BomberBotProStatic,
                     'point': 'TurretBottomLeft'},
                    {'type': bs.BomberBotProStatic,
                     'point': 'TurretBottomRight'},
                    {'type': bs.BomberBotProStatic,
                     'point': 'TurretTopMiddleLeft'} if hard else None,
                    {'type': bs.BomberBotProStatic,
                     'point': 'TurretTopMiddleRight'} if hard else None,
                ]},
            ]
        # we generate these on the fly in endless..
        elif self._preset in ['endless', 'endlessTournament']:
            self._haveTnt = True
            self._excludePowerups = []

        else:
            raise Exception("Invalid preset: "+str(self._preset))

        # FIXME - should migrate to use setupStandardPowerupDrops()

        # spit out a few powerups and start dropping more shortly
        self._dropPowerups(
            standardPoints=True, powerupType='curse'
            if self._preset
            in ['uber', 'uberEasy']
            else(
                'landMines'
                if self._preset in ['rookie', 'rookieEasy'] else None))
        bs.gameTimer(4000, self._startPowerupDrops)
        # our TNT spawner (if applicable)
        if self._haveTnt:
            self._tntSpawner = bs.TNTSpawner(position=self._tntSpawnPosition)

        self.setupLowLifeWarningSound()

        self._updateScores()
        self._bots = bs.BotSet()

        bs.gameTimer(4000, self._startUpdatingWaves)

    def _onGotScoresToBeat(self, scores):
        self._showStandardScoresToBeatUI(scores)

    def _getDistribution(
            self, targetPoints, minDudes, maxDudes, groupCount, maxLevel):
        """ calculate a distribution of bad guys given some params """

        maxIterations = 10+maxDudes*2

        def _getTotals(groups):
            totalPoints = 0
            totalDudes = 0
            for group in groups:
                for entry in group:
                    dudes = entry[1]
                    totalPoints += entry[0]*dudes
                    totalDudes += dudes
            return totalPoints, totalDudes

        groups = []
        for g in range(groupCount):
            groups.append([])

        types = [1]
        if maxLevel > 1:
            types.append(2)
        if maxLevel > 2:
            types.append(3)
        if maxLevel > 3:
            types.append(4)

        for iteration in range(maxIterations):
            # see how much we're off our target by
            totalPoints, totalDudes = _getTotals(groups)
            diff = targetPoints - totalPoints
            dudesDiff = maxDudes - totalDudes
            # add an entry if one will fit
            value = types[random.randrange(len(types))]
            group = groups[random.randrange(len(groups))]
            if len(group) == 0:
                maxCount = random.randint(1, 6)
            else:
                maxCount = 2*random.randint(1, 3)
            maxCount = min(maxCount, dudesDiff)
            count = min(maxCount, diff/value)
            if count > 0:
                group.append((value, count))
                totalPoints += value*count
                totalDudes += count
                diff = targetPoints - totalPoints

            totalPoints, totalDudes = _getTotals(groups)
            full = (totalPoints >= targetPoints)

            if full:
                # every so often, delete a random entry just to
                # shake up our distribution
                if random.random() < 0.2 and iteration != maxIterations-1:
                    entryCount = 0
                    for group in groups:
                        for entry in group:
                            entryCount += 1
                    if entryCount > 1:
                        delEntry = random.randrange(entryCount)
                        entryCount = 0
                        for group in groups:
                            for entry in group:
                                if entryCount == delEntry:
                                    group.remove(entry)
                                    break
                                entryCount += 1

                # if we don't have enough dudes, kill the group with
                # the biggest point value
                elif totalDudes < minDudes and iteration != maxIterations-1:
                    biggestValue = 9999
                    biggestEntry = None
                    for group in groups:
                        for entry in group:
                            if entry[0] > biggestValue or biggestEntry is None:
                                biggestValue = entry[0]
                                biggestEntry = entry
                                biggestEntryGroup = group
                    if biggestEntry is not None:
                        biggestEntryGroup.remove(biggestEntry)

                # if we've got too many dudes, kill the group with the
                # smallest point value
                elif totalDudes > maxDudes and iteration != maxIterations-1:
                    smallestValue = 9999
                    smallestEntry = None
                    for group in groups:
                        for entry in group:
                            if entry[0] < smallestValue or smallestEntry is None:
                                smallestValue = entry[0]
                                smallestEntry = entry
                                smallestEntryGroup = group
                    smallestEntryGroup.remove(smallestEntry)

                # close enough.. we're done.
                else:
                    if diff == 0:
                        break

        return groups

    def spawnPlayer(self, player):

        # we keep track of who got hurt each wave for score purposes
        player.gameData['hasBeenHurt'] = False

        pos = (
            self._spawnCenter[0] + random.uniform(-1.5, 1.5),
            self._spawnCenter[1],
            self._spawnCenter[2] + random.uniform(-1.5, 1.5))
        s = self.spawnPlayerSpaz(player, position=pos)
        if self._preset in [
                'trainingEasy', 'rookieEasy', 'proEasy', 'uberEasy']:
            s._impactScale = 0.25
        s.addDroppedBombCallback(self._handlePlayerDroppedBomb)

    def _handlePlayerDroppedBomb(self, player, bomb):
        self._playerHasDroppedBomb = True

    def _dropPowerup(self, index, powerupType=None):
        powerupType = bs.Powerup.getFactory().getRandomPowerupType(
            forceType=powerupType, excludeTypes=self._excludePowerups)
        bs.Powerup(
            position=self.getMap().powerupSpawnPoints[index],
            powerupType=powerupType).autoRetain()

    def _startPowerupDrops(self):
        self._powerupDropTimer = bs.Timer(
            3000, bs.WeakCall(self._dropPowerups), repeat=True)

    def _dropPowerups(self, standardPoints=False, powerupType=None):
        """ Generic powerup drop """

        if standardPoints:
            pts = self.getMap().powerupSpawnPoints
            for i, pt in enumerate(pts):
                bs.gameTimer(1000+i*500, bs.WeakCall(
                    self._dropPowerup,
                    i, powerupType if i == 0 else None))
        else:
            pt = (self._powerupCenter[0]+random.uniform(
                -1.0*self._powerupSpread[0], 1.0*self._powerupSpread[0]),
                  self._powerupCenter[1], self._powerupCenter[2]+random.uniform(
                      -self._powerupSpread[1], self._powerupSpread[1]))

            # drop one random one somewhere..
            bs.Powerup(
                position=pt,
                powerupType=bs.Powerup.getFactory().getRandomPowerupType(
                    excludeTypes=self._excludePowerups)).autoRetain()

    def doEnd(self, outcome, delay=0):

        if outcome == 'defeat':
            self.fadeToRed()

        if self._wave >= 2:
            score = self._score.get()
            failMessage = None
        else:
            score = None
            failMessage = bs.Lstr(resource='reachWave2Text')
        self.end({'outcome': outcome, 'score': score,
                  'failMessage': failMessage,
                  'playerInfo': self.initialPlayerInfo},
                 delay=delay)

    def _updateWaves(self):

        # if we have no living bots, go to the next wave
        if (self._canEndWave and not self._bots.haveLivingBots()
                and not self._gameOver):

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
                bs.gameTimer(0, lambda: bs.playSound(self._cashRegisterSound))
                bs.gameTimer(baseDelay, bs.WeakCall(
                    self._awardTimeBonus, self._timeBonus))
                baseDelay += 1000

            # reward flawless bonus
            if self._wave > 0:
                haveFlawless = False
                for player in self.players:
                    if (player.isAlive()
                            and player.gameData['hasBeenHurt'] == False):
                        haveFlawless = True
                        bs.gameTimer(baseDelay, bs.WeakCall(
                            self._awardFlawlessBonus, player))
                    player.gameData['hasBeenHurt'] = False  # reset
                if haveFlawless:
                    baseDelay += 1000

            if won:

                self.showZoomMessage(
                    bs.Lstr(resource='victoryText'),
                    scale=1.0, duration=4000)

                self.celebrate(20000)

                # rookie onslaught completion
                if self._preset in ['training', 'trainingEasy']:
                    self._awardAchievement(
                        'Onslaught Training Victory', sound=False)
                    if not self._playerHasDroppedBomb:
                        self._awardAchievement('Boxer', sound=False)
                elif self._preset in ['rookie', 'rookieEasy']:
                    self._awardAchievement(
                        'Rookie Onslaught Victory', sound=False)
                    if not self._aPlayerHasBeenHurt:
                        self._awardAchievement('Flawless Victory', sound=False)
                elif self._preset in ['pro', 'proEasy']:
                    self._awardAchievement('Pro Onslaught Victory', sound=False)
                    if not self._playerHasDroppedBomb:
                        self._awardAchievement('Pro Boxer', sound=False)
                elif self._preset in ['uber', 'uberEasy']:
                    self._awardAchievement(
                        'Uber Onslaught Victory', sound=False)

                bs.gameTimer(baseDelay, bs.WeakCall(self._awardCompletionBonus))
                baseDelay += 850
                bs.playSound(self._winSound)
                self.cameraFlash()
                bs.playMusic('Victory')
                self._gameOver = True

                # cant just pass delay to doEnd because our extra bonuses
                # havnt been added yet (once we call doEnd the score
                # gets locked in)
                bs.gameTimer(baseDelay, bs.WeakCall(self.doEnd, 'victory'))

                return

            self._wave += 1

            # short celebration after waves
            if self._wave > 1:
                self.celebrate(500)

            bs.gameTimer(baseDelay, bs.WeakCall(self._startNextWave))

    def _awardCompletionBonus(self):
        bs.playSound(self._cashRegisterSound)
        for player in self.players:
            try:
                if player.isAlive():
                    self.scoreSet.playerScored(
                        player, int(100 / len(self.initialPlayerInfo)),
                        scale=1.4, color=(0.6, 0.6, 1.0, 1.0),
                        title=bs.Lstr(resource='completionBonusText'),
                        screenMessage=False)
            except Exception:
                bs.printException()

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

    def _awardFlawlessBonus(self, player):
        bs.playSound(self._cashRegisterSound)
        try:
            if player.isAlive():
                self.scoreSet.playerScored(
                    player, self._flawlessBonus, scale=1.2,
                    color=(0.6, 1.0, 0.6, 1.0),
                    title=bs.Lstr(resource='flawlessWaveText'),
                    screenMessage=False)
        except Exception:
            bs.printException()

    def _startTimeBonusTimer(self):
        self._timeBonusTimer = bs.Timer(
            1000, bs.WeakCall(self._updateTimeBonus),
            repeat=True)

    def _updatePlayerSpawnInfo(self):

        # if we have no living players lets just blank this
        if not any(player.isAlive() for player in self.teams[0].players):
            self._spawnInfoText.node.text = ''
        else:
            t = ''
            for player in self.players:
                if (not player.isAlive() and (
                        self._preset in ['endless', 'endlessTournament']
                        or (player.gameData['respawnWave'] <=
                            len(self._waves)))):
                    t = bs.Lstr(value='${A}${B}\n', subs=[
                        ('${A}', t), ('${B}', bs.Lstr(
                            resource='onslaughtRespawnText', subs=[
                                ('${PLAYER}', player.getName()),
                                ('${WAVE}', str(player.gameData['respawnWave']
                                ))]))])
            self._spawnInfoText.node.text = t

    def _startNextWave(self):

        # this could happen if we beat a wave as we die..
        # we dont wanna respawn players and whatnot if this happens
        if self._gameOver:
            return

        # respawn applicable players
        if self._wave > 1 and not self.isWaitingForContinue():
            for player in self.players:
                if (not player.isAlive()
                        and player.gameData['respawnWave'] == self._wave):
                    self.spawnPlayer(player)

        self._updatePlayerSpawnInfo()

        self.showZoomMessage(
            bs.Lstr(
                value='${A} ${B}',
                subs=[('${A}', bs.Lstr(resource='waveText')),
                      ('${B}', str(self._wave))]),
            scale=1.0, duration=1000, trail=True)
        bs.gameTimer(400, bs.Call(bs.playSound, self._newWaveSound))

        t = 0
        dt = 200
        botAngle = random.random()*360.0

        if self._wave == 1:
            spawnTime = 3973
            t += 500
        else:
            spawnTime = 2648

        offs = 0  # debugging

        # populate waves

        # generate random waves in endless mode
        if self._preset in ['endless', 'endlessTournament']:

            level = self._wave

            botTypes2 = [bs.BomberBot,
                         bs.ToughGuyBot,
                         bs.ChickBot,
                         bs.NinjaBot,
                         bs.BomberBotPro,
                         bs.ToughGuyBotPro,
                         bs.ChickBotPro,
                         bs.BomberBotProShielded,
                         bs.PirateBot,
                         bs.NinjaBotProShielded,
                         bs.MelBot,
                         bs.ToughGuyBotProShielded,
                         bs.ChickBotProShielded
                         ]

            if level > 5:
                botTypes2 += [
                    bs.PirateBot,
                    bs.ChickBotProShielded,
                    bs.ToughGuyBotProShielded,
                    bs.NinjaBotProShielded,
                ]
            if level > 7:
                botTypes2 += [
                    bs.PirateBot,
                    bs.ChickBotProShielded,
                    bs.ToughGuyBotProShielded,
                    bs.NinjaBotProShielded,
                ]
            if level > 10:
                botTypes2 += [
                    bs.ChickBotProShielded,
                    bs.ChickBotProShielded,
                    bs.ChickBotProShielded,
                    bs.ChickBotProShielded
                ]
            if level > 13:
                botTypes2 += [
                    bs.ChickBotProShielded,
                    bs.ChickBotProShielded,
                    bs.ChickBotProShielded,
                    bs.ChickBotProShielded
                ]

            botLevels = [[b for b in botTypes2 if b.pointsMult == 1],
                         [b for b in botTypes2 if b.pointsMult == 2],
                         [b for b in botTypes2 if b.pointsMult == 3],
                         [b for b in botTypes2 if b.pointsMult == 4]]
            if not all([len(a) > 0 for a in botLevels]):
                raise Exception()

            targetPoints = level*3-2
            minDudes = min(1+level/3, 10)
            maxDudes = min(10, level+1)
            maxLevel = 4 if level > 6 else(
                3 if level > 3 else(2 if level > 2 else 1))
            groupCount = 3
            distribution = self._getDistribution(
                targetPoints, minDudes, maxDudes, groupCount, maxLevel)

            allEntries = []
            for group in distribution:
                entries = []
                for entry in group:
                    botLevel = botLevels[entry[0]-1]
                    botType = botLevel[random.randrange(len(botLevel))]
                    r = random.random()
                    if r < 0.5:
                        spacing = 10
                    elif r < 0.9:
                        spacing = 20
                    else:
                        spacing = 40
                    split = random.random() > 0.3
                    for i in range(entry[1]):
                        if split and i % 2 == 0:
                            entries.insert(
                                0, {"type": botType, "spacing": spacing})
                        else:
                            entries.append(
                                {"type": botType, "spacing": spacing})
                if len(entries) > 0:
                    allEntries += entries
                    allEntries.append(
                        {"type": None, "spacing": 40
                         if random.random() < 0.5 else 80})

            angleRand = random.random()
            if angleRand > 0.75:
                baseAngle = 130
            elif angleRand > 0.5:
                baseAngle = 210
            elif angleRand > 0.25:
                baseAngle = 20
            else:
                baseAngle = -30
            baseAngle += (0.5-random.random())*20.0

            wave = {'baseAngle': baseAngle,
                    'entries': allEntries}
        else:
            wave = self._waves[self._wave-1]

        entries = []

        try:
            botAngle = wave['baseAngle']
        except Exception:
            botAngle = 0

        entries += wave['entries']

        thisTimeBonus = 0
        thisFlawlessBonus = 0

        for info in entries:
            if info is None:
                continue

            botType = info['type']

            if botType == 'delay':
                spawnTime += info['duration']
                continue
            if botType is not None:
                thisTimeBonus += botType.pointsMult * 20
                thisFlawlessBonus += botType.pointsMult * 5
            # if its got a position, use that
            try:
                point = info['point']
            except Exception:
                point = None
            if point is not None:
                bs.gameTimer(
                    t, bs.WeakCall(
                        self.addBotAtPoint, point, botType, spawnTime))
                t += dt
            else:
                try:
                    spacing = info['spacing']
                except Exception:
                    spacing = 5.0
                botAngle += spacing*0.5
                if botType is not None:
                    bs.gameTimer(
                        t, bs.WeakCall(
                            self.addBotAtAngle, botAngle, botType, spawnTime))
                    t += dt
                botAngle += spacing*0.5

        # we can end the wave after all the spawning happens
        bs.gameTimer(t+spawnTime-dt+10, bs.WeakCall(self._setCanEndWave))

        # reset our time bonus
        self._timeBonus = thisTimeBonus
        self._flawlessBonus = thisFlawlessBonus
        vrMode = bs.getEnvironment()['vrMode']
        self._timeBonusText = bs.NodeActor(
            bs.newNode(
                'text',
                attrs={'vAttach': 'top', 'hAttach': 'center',
                       'hAlign': 'center', 'vrDepth': -30, 'color':
                       (1, 1, 0, 1) if True else(1, 1, 0.5, 1), 'shadow': 1.0
                       if True else 0.5, 'flatness': 1.0 if True else 0.5,
                       'position': (0, -60),
                       'scale': 0.8 if True else 0.6, 'text': bs.Lstr(
                           value='${A}: ${B}',
                           subs=[('${A}', bs.Lstr(
                               resource='timeBonusText')),
                               ('${B}', str(self._timeBonus))])}))

        bs.gameTimer(5000, bs.WeakCall(self._startTimeBonusTimer))
        self._waveText = bs.NodeActor(
            bs.newNode(
                'text',
                attrs={'vAttach': 'top', 'hAttach': 'center',
                       'hAlign': 'center', 'vrDepth': -10, 'color':
                       (1, 1, 1, 1) if True else(0.7, 0.7, 0.7, 1.0), 'shadow':
                       1.0 if True else 0.7, 'flatness': 1.0
                       if True else 0.5, 'position': (0, -40),
                       'scale': 1.3 if True else 1.1, 'text': bs.Lstr(
                           value='${A} ${B}',
                           subs=[('${A}', bs.Lstr(resource='waveText')),
                                 ('${B}', str(self._wave) +
                                  (''
                                   if self._preset
                                   in ['endless', 'endlessTournament']
                                   else('/' + str(len(self._waves)))))])}))

    def addBotAtPoint(self, point, spazType, spawnTime=1000):
        # dont add if the game has ended
        if self._gameOver:
            return
        pt = self.getMap().defs.points['botSpawn'+point]
        self._bots.spawnBot(spazType, pos=pt, spawnTime=spawnTime)

    def addBotAtAngle(self, angle, spazType, spawnTime=1000):

        # dont add if the game has ended
        if self._gameOver:
            return

        angleRadians = angle/57.2957795
        x = math.sin(angleRadians)*1.06
        z = math.cos(angleRadians)*1.06
        pt = (x/0.125, 2.3, (z/0.2)-3.7)

        self._bots.spawnBot(spazType, pos=pt, spawnTime=spawnTime)

    def _updateTimeBonus(self):
        self._timeBonus = int(self._timeBonus * 0.93)
        if self._timeBonus > 0 and self._timeBonusText is not None:
            self._timeBonusText.node.text = bs.Lstr(
                value='${A}: ${B}',
                subs=[('${A}', bs.Lstr(resource='timeBonusText')),
                      ('${B}', str(self._timeBonus))])
        else:
            self._timeBonusText = None

    def _startUpdatingWaves(self):
        self._waveUpdateTimer = bs.Timer(
            2000, bs.WeakCall(self._updateWaves), repeat=True)

    def _updateScores(self):

        score = self._score.get()
        if self._preset == 'endless':
            if score >= 500:
                self._awardAchievement('Onslaught Master')
            if score >= 1000:
                self._awardAchievement('Onslaught Wizard')
            if score >= 5000:
                self._awardAchievement('Onslaught God')
        self._scoreBoard.setTeamValue(self.teams[0], score, maxScore=None)

    def handleMessage(self, m):

        if isinstance(m, bs.PlayerSpazHurtMessage):
            player = m.spaz.getPlayer()
            if player is None:
                bs.printError('FIXME: getPlayer() should no'
                              ' longer ever be returning None')
                return
            if not player.exists():
                return
            player.gameData['hasBeenHurt'] = True
            self._aPlayerHasBeenHurt = True

        elif isinstance(m, bs.PlayerScoredMessage):
            self._score.add(m.score)
            self._updateScores()

        elif isinstance(m, bs.PlayerSpazDeathMessage):
            self.__superHandleMessage(m)  # augment standard behavior
            player = m.spaz.getPlayer()
            self._aPlayerHasBeenHurt = True
            # make note with the player when they can respawn
            if self._wave < 10:
                player.gameData['respawnWave'] = max(2, self._wave+1)
            elif self._wave < 15:
                player.gameData['respawnWave'] = max(2, self._wave+2)
            else:
                player.gameData['respawnWave'] = max(2, self._wave+3)
            bs.gameTimer(100, self._updatePlayerSpawnInfo)
            bs.gameTimer(100, self._checkRoundOver)

        elif isinstance(m, bs.SpazBotDeathMessage):
            pts, importance = m.badGuy.getDeathPoints(m.how)
            if m.killerPlayer is not None:

                # toss-off-map achievement
                if self._preset in ['training', 'trainingEasy']:
                    if m.badGuy.lastAttackedType == ('pickedUp', 'default'):
                        if not hasattr(self, '_throwOffKills'):
                            self._throwOffKills = 0
                        self._throwOffKills += 1
                        if self._throwOffKills >= 3:
                            self._awardAchievement('Off You Go Then')

                # land-mine achievement
                elif self._preset in ['rookie', 'rookieEasy']:
                    if m.badGuy.lastAttackedType == ('explosion', 'landMine'):
                        if not hasattr(self, '_landMineKills'):
                            self._landMineKills = 0
                        self._landMineKills += 1
                        if self._landMineKills >= 3:
                            self._awardAchievement('Mine Games')

                # tnt achievement
                elif self._preset in ['pro', 'proEasy']:
                    if m.badGuy.lastAttackedType == ('explosion', 'tnt'):
                        if not hasattr(self, '_tntKills'):
                            self._tntKills = 0
                        self._tntKills += 1
                        if self._tntKills >= 3:
                            bs.gameTimer(
                                500, bs.WeakCall(
                                    self._awardAchievement,
                                    'Boom Goes the Dynamite'))

                elif self._preset in ['uber', 'uberEasy']:

                    # uber mine achievement
                    if m.badGuy.lastAttackedType == ('explosion', 'landMine'):
                        if not hasattr(self, '_landMineKills'):
                            self._landMineKills = 0
                        self._landMineKills += 1
                        if self._landMineKills >= 6:
                            self._awardAchievement('Gold Miner')
                    # uber tnt achievement
                    if m.badGuy.lastAttackedType == ('explosion', 'tnt'):
                        if not hasattr(self, '_tntKills'):
                            self._tntKills = 0
                        self._tntKills += 1
                        if self._tntKills >= 6:
                            bs.gameTimer(
                                500, bs.WeakCall(
                                    self._awardAchievement, 'TNT Terror'))

                try:
                    target = m.badGuy.node.position
                except Exception:
                    target = None
                try:
                    killerPlayer = m.killerPlayer
                    self.scoreSet.playerScored(
                        killerPlayer, pts, target=target, kill=True,
                        screenMessage=False, importance=importance)
                    bs.playSound(self._dingSound if importance ==
                                 1 else self._dingSoundHigh, volume=0.6)
                except Exception:
                    pass
            # normally we pull scores from the score-set, but if there's
            # no player lets be explicit..
            else:
                self._score.add(pts)
            self._updateScores()
        else:
            self.__superHandleMessage(m)

    def _setCanEndWave(self):
        self._canEndWave = True

    def __superHandleMessage(self, m):
        super(OnslaughtGame, self).handleMessage(m)

    def endGame(self):
        # tell our bots to celebrate just to rub it in
        self._bots.finalCelebrate()

        self._gameOver = True
        self.doEnd('defeat', delay=2000)
        bs.playMusic(None)

    def onContinue(self):
        for player in self.players:
            if not player.isAlive():
                self.spawnPlayer(player)

    def _checkRoundOver(self):
        """
        see if the round is over in response to an event (player died, etc)
        """

        # if we already ended it doesn't matter
        if self.hasEnded():
            return

        if not any(player.isAlive() for player in self.teams[0].players):
            # allow continuing after wave 1
            if self._wave > 1:
                self.continueOrEndGame()
            else:
                self.endGame()
