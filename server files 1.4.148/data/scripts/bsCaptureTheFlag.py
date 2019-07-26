import bs
import random


def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4


def bsGetGames():
    return [CTFGame]


class CTFFlag(bs.Flag):
    def __init__(self, activity, team):
        bs.Flag.__init__(
            self,
            materials=[team.gameData['flagMaterial']],
            position=team.gameData['basePos'],
            color=team.color)
        self._team = team
        self._heldCount = 0
        self._counter = bs.newNode(
            'text',
            owner=self.node,
            attrs={
                'inWorld': True,
                'scale': 0.02,
                'hAlign': 'center'
            })
        self.resetReturnTimes()

    def resetReturnTimes(self):
        self._timeOutRespawnTime = int(
            self.getActivity().settings['Flag Idle Return Time'])
        self._touchReturnTime = float(
            self.getActivity().settings['Flag Touch Return Time'])

    def getTeam(self):
        return self._team


class CTFGame(bs.TeamGameActivity):
    @classmethod
    def getName(cls):
        return 'Capture the Flag'

    @classmethod
    def getDescription(cls, sessionType):
        return 'Return the enemy flag to score.'

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.TeamsSession) else False

    @classmethod
    def getSupportedMaps(cls, sessionType):
        return bs.getMapsSupportingPlayType("teamFlag")

    @classmethod
    def getSettings(cls, sessionType):
        return [
            ("Score to Win", {'minValue': 1, 'default': 3}),
            ("Flag Touch Return Time", {
                'minValue': 0, 'default': 0, 'increment': 1}),
            ("Flag Idle Return Time", {
                'minValue': 5, 'default': 30, 'increment': 5}),
            ("Time Limit", {
                'choices': [('None', 0), ('1 Minute', 60),
                            ('2 Minutes', 120), ('5 Minutes', 300),
                            ('10 Minutes', 600), ('20 Minutes', 1200)],
                'default': 0 }),
            ("Respawn Times", {
                'choices': [('Shorter', 0.25), ('Short', 0.5), ('Normal',1.0),
                            ('Long',2.0), ('Longer', 4.0)],
                'default': 1.0}),
            ("Epic Mode", {'default': False})] # yapf: disable


    def __init__(self, settings):
        bs.TeamGameActivity.__init__(self, settings)
        self._scoreBoard = bs.ScoreBoard()
        if self.settings['Epic Mode']: self._isSlowMotion = True
        self._alarmSound = bs.getSound("alarm")
        self._tickingSound = bs.getSound("ticking")
        self._lastScoreTime = 0
        self._scoreSound = bs.getSound("score")
        self._swipSound = bs.getSound("swip")
        self._allBasesMaterial = bs.Material()

    def getInstanceDescription(self):
        if self.settings['Score to Win'] == 1: return 'Steal the enemy flag.'
        else:
            return ('Steal the enemy flag ${ARG1} times.',
                    self.settings['Score to Win'])

    def getInstanceScoreBoardDescription(self):
        if self.settings['Score to Win'] == 1: return 'return 1 flag'
        else: return ('return ${ARG1} flags', self.settings['Score to Win'])

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(
            self,
            music='Epic' if self.settings['Epic Mode'] else 'FlagCatcher')

    def onTeamJoin(self, team):

        team.gameData['score'] = 0
        team.gameData['flagReturnTouches'] = 0
        team.gameData['homeFlagAtBase'] = True
        team.gameData['touchReturnTimer'] = None
        team.gameData['enemyFlagAtBase'] = False
        team.gameData['basePos'] = self.getMap().getFlagPosition(team.getID())

        self.projectFlagStand(team.gameData['basePos'])

        bs.newNode(
            'light',
            attrs={
                'position': team.gameData['basePos'],
                'intensity': 0.6,
                'heightAttenuated': False,
                'volumeIntensityScale': 0.1,
                'radius': 0.1,
                'color': team.color
            })

        baseRegionMat = team.gameData['baseRegionMaterial'] = bs.Material()
        p = team.gameData['basePos']
        team.gameData['baseRegion'] = bs.newNode(
            "region",
            attrs={
                'position': (p[0], p[1] + 0.75, p[2]),
                'scale': (0.5, 0.5, 0.5),
                'type': 'sphere',
                'materials': [baseRegionMat, self._allBasesMaterial]
            })

        # create some materials for this team
        spazMatNoFlagPhysical = team.gameData[
            'spazMaterialNoFlagPhysical'] = bs.Material()
        spazMatNoFlagCollide = team.gameData[
            'spazMaterialNoFlagCollide'] = bs.Material()
        flagMat = team.gameData['flagMaterial'] = bs.Material()

        # some parts of our spazzes don't collide physically with our
        # flags but generate callbacks
        spazMatNoFlagPhysical.addActions(
            conditions=('theyHaveMaterial', flagMat),
            actions=(('modifyPartCollision', 'physical',
                      False), ('call', 'atConnect',
                               lambda: self._handleHitOwnFlag(team, 1)),
                     ('call', 'atDisconnect',
                      lambda: self._handleHitOwnFlag(team, 0))))
        # other parts of our spazzes don't collide with our flags at all
        spazMatNoFlagCollide.addActions(
            conditions=('theyHaveMaterial', flagMat),
            actions=('modifyPartCollision', 'collide', False))

        # we wanna know when *any* flag enters/leaves our base
        baseRegionMat.addActions(
            conditions=('theyHaveMaterial', bs.Flag.getFactory().flagMaterial),
            actions=(('modifyPartCollision', 'collide',
                      True), ('modifyPartCollision', 'physical', False),
                     ('call', 'atConnect',
                      lambda: self._handleFlagEnteredBase(team)),
                     ('call', 'atDisconnect',
                      lambda: self._handleFlagLeftBase(team))))

        self._spawnFlagForTeam(team)
        self._updateScoreBoard()

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        self.setupStandardPowerupDrops()

        bs.gameTimer(1000, call=self._tick, repeat=True)

    def _spawnFlagForTeam(self, team):
        flag = team.gameData['flag'] = CTFFlag(self, team)
        team.gameData['flagReturnTouches'] = 0
        self._flashBase(team, length=1000)
        bs.playSound(self._swipSound, position=flag.node.position)

    def _handleFlagEnteredBase(self, team):
        flag = bs.getCollisionInfo("opposingNode").getDelegate()

        if flag.getTeam() is team:
            team.gameData['homeFlagAtBase'] = True

            # if the enemy flag is already here, score!
            if team.gameData['enemyFlagAtBase']:
                self._score(team)
        else:
            team.gameData['enemyFlagAtBase'] = True
            if team.gameData['homeFlagAtBase']:
                # award points to whoever was carrying the enemy flag
                try:
                    player = flag._lastPlayerToHold
                except Exception:
                    player = None
                if player is not None and player.exists(
                ) and player.getTeam() is team:
                    self.scoreSet.playerScored(player, 50, bigMessage=True)

                # update score and reset flags
                self._score(team)

            # if the home-team flag isn't here, print a message to that effect
            else:
                if not hasattr(self, '_lastHomeFlagNoticePrintTime'):
                    self._lastHomeFlagNoticePrintTime = 0
                t = bs.getRealTime()
                if t - self._lastHomeFlagNoticePrintTime > 5000:
                    self._lastHomeFlagNoticePrintTime = t
                    p = team.gameData['basePos']
                    tNode = bs.newNode(
                        'text',
                        attrs={
                            'text':
                                bs.Lstr(resource='ownFlagAtYourBaseWarning'),
                            'inWorld':
                                True,
                            'scale':
                                0.013,
                            'color': (1, 1, 0, 1),
                            'hAlign':
                                'center',
                            'position': (p[0], p[1] + 3.2, p[2])
                        })
                    bs.gameTimer(5100, tNode.delete)
                    bs.animate(tNode, 'scale', {
                        0: 0,
                        200: 0.013,
                        4800: 0.013,
                        5000: 0
                    })

    def _tick(self):
        # if either flag is away from base and not being held, tick down its
        # respawn timer
        for team in self.teams:
            flag = team.gameData['flag']

            if not team.gameData['homeFlagAtBase'] and flag._heldCount == 0:
                timeOutCountingDown = True
                flag._timeOutRespawnTime -= 1
                if flag._timeOutRespawnTime <= 0:
                    flag.handleMessage(bs.DieMessage())
            else:
                timeOutCountingDown = False

            if flag.node.exists() and flag._counter.exists():
                t = flag.node.position
                flag._counter.position = (t[0], t[1] + 1.3, t[2])

                # if there's no self-touches on this flag, set its text
                # to show its auto-return counter.  (if there's self-touches
                # its showing that time)
                if team.gameData['flagReturnTouches'] == 0:
                    flag._counter.text = str(flag._timeOutRespawnTime) if (
                        timeOutCountingDown
                        and flag._timeOutRespawnTime <= 10) else ''
                    flag._counter.color = (1, 1, 1, 0.5)
                    flag._counter.scale = 0.014

    def _score(self, team):
        team.gameData['score'] += 1
        bs.playSound(self._scoreSound)
        self._flashBase(team)
        self._updateScoreBoard()
        # have teammates celebrate
        for player in team.players:
            try:
                player.actor.node.handleMessage('celebrate', 2000)
            except Exception:
                pass
        # reset all flags/state
        for resetTeam in self.teams:
            if not resetTeam.gameData['homeFlagAtBase']:
                resetTeam.gameData['flag'].handleMessage(bs.DieMessage())
            resetTeam.gameData['enemyFlagAtBase'] = False
        if team.gameData['score'] >= self.settings['Score to Win']:
            self.endGame()

    def endGame(self):
        results = bs.TeamGameResults()
        for t in self.teams:
            results.setTeamScore(t, t.gameData['score'])
        self.end(results=results, announceDelay=800)

    def _handleFlagLeftBase(self, team):
        curTime = bs.getGameTime()

        opNode = bs.getCollisionInfo("opposingNode")

        try:
            flag = opNode.getDelegate()
        except Exception:
            return  # can happen when we kill a flag

        if flag.getTeam() is team:

            # check times here to prevent too much flashing
            if ('lastFlagLeaveTime' not in team.gameData
                    or curTime - team.gameData['lastFlagLeaveTime'] > 3000):
                bs.playSound(
                    self._alarmSound, position=team.gameData['basePos'])
                self._flashBase(team)
            team.gameData['lastFlagLeaveTime'] = curTime
            team.gameData['homeFlagAtBase'] = False
        else:
            team.gameData['enemyFlagAtBase'] = False

    def _touchReturnUpdate(self, team):

        # count down only while its away from base and not being held
        if (team.gameData['homeFlagAtBase']
                or team.gameData['flag']._heldCount > 0):
            team.gameData['touchReturnTimerTicking'] = None
            return  # no need to return when its at home
        else:
            if team.gameData['touchReturnTimerTicking'] is None:
                team.gameData['touchReturnTimerTicking'] = bs.NodeActor(
                    bs.newNode(
                        'sound',
                        attrs={
                            'sound': self._tickingSound,
                            'positional': False,
                            'loop': True
                        }))
        flag = team.gameData['flag']
        flag._touchReturnTime -= 0.1
        if flag._counter.exists():
            flag._counter.text = "%.1f" % flag._touchReturnTime
            flag._counter.color = (1, 1, 0, 1)
            flag._counter.scale = 0.02

        if flag._touchReturnTime <= 0.0:
            self._awardPlayersTouchingOwnFlag(team)
            flag.handleMessage(bs.DieMessage())

    def _awardPlayersTouchingOwnFlag(self, team):
        for player in team.players:
            if player.gameData['touchingOwnFlag'] > 0:
                returnScore = 10 + 5 * int(
                    self.settings['Flag Touch Return Time'])
                self.scoreSet.playerScored(
                    player, returnScore, screenMessage=False)

    def _handleHitOwnFlag(self, team, val):

        # keep track of when each player is touching their own flag so we can
        # award points when returned
        srcNode = bs.getCollisionInfo('sourceNode')
        try:
            player = srcNode.getDelegate().getPlayer()
        except Exception:
            player = None
        if player is not None and player.exists():
            if val: player.gameData['touchingOwnFlag'] += 1
            else: player.gameData['touchingOwnFlag'] -= 1

        # if return-time is zero, just kill it immediately.. otherwise keep
        # track of touches and count down
        if float(self.settings['Flag Touch Return Time']) <= 0.0:
            if (not team.gameData['homeFlagAtBase']
                    and team.gameData['flag']._heldCount == 0):
                # use a node message to kill the flag instead of just killing
                # our team's. (avoids redundantly killing new flags if
                # multiple body parts generate callbacks in one step)
                node = bs.getCollisionInfo("opposingNode")
                if node is not None and node.exists():
                    self._awardPlayersTouchingOwnFlag(team)
                    node.handleMessage(bs.DieMessage())
        # takes a non-zero amount of time to return
        else:
            if val:
                team.gameData['flagReturnTouches'] += 1
                if team.gameData['flagReturnTouches'] == 1:
                    team.gameData['touchReturnTimer'] = bs.Timer(
                        100,
                        call=bs.Call(self._touchReturnUpdate, team),
                        repeat=True)
                    team.gameData['touchReturnTimerTicking'] = None
            else:
                team.gameData['flagReturnTouches'] -= 1
                if team.gameData['flagReturnTouches'] == 0:
                    team.gameData['touchReturnTimer'] = None
                    team.gameData['touchReturnTimerTicking'] = None
            if team.gameData['flagReturnTouches'] < 0:
                bs.printError(
                    'CTF: flagReturnTouches < 0; this shouldn\'t happen.')

    def _flashBase(self, team, length=2000):
        light = bs.newNode(
            'light',
            attrs={
                'position': team.gameData['basePos'],
                'heightAttenuated': False,
                'radius': 0.3,
                'color': team.color
            })
        bs.animate(light, 'intensity', {0: 0, 250: 2.0, 500: 0}, loop=True)
        bs.gameTimer(length, light.delete)

    def spawnPlayerSpaz(self, *args, **keywds):
        # intercept new spazzes and add our team material for them
        spaz = bs.TeamGameActivity.spawnPlayerSpaz(self, *args, **keywds)
        spaz.getPlayer().gameData['touchingOwnFlag'] = 0
        noPhysicalMats = [
            spaz.getPlayer().getTeam().gameData['spazMaterialNoFlagPhysical']
        ]
        noCollideMats = [
            spaz.getPlayer().getTeam().gameData['spazMaterialNoFlagCollide']
        ]
        # our normal parts should still collide; just not physically
        # (so we can calc restores)
        spaz.node.materials = list(spaz.node.materials) + noPhysicalMats
        spaz.node.rollerMaterials = list(
            spaz.node.rollerMaterials) + noPhysicalMats
        # pickups and punches shouldn't hit at all though
        spaz.node.punchMaterials = list(
            spaz.node.punchMaterials) + noCollideMats
        spaz.node.pickupMaterials = list(
            spaz.node.pickupMaterials) + noCollideMats
        spaz.node.extrasMaterials = list(
            spaz.node.extrasMaterials) + noCollideMats
        return spaz

    def _updateScoreBoard(self):
        for team in self.teams:
            self._scoreBoard.setTeamValue(team, team.gameData['score'],
                                          self.settings['Score to Win'])

    def handleMessage(self, m):
        if isinstance(m, bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self, m)  # augment standard
            self.respawnPlayer(m.spaz.getPlayer())
        elif isinstance(m, bs.FlagDeathMessage):
            bs.gameTimer(100, bs.Call(self._spawnFlagForTeam,
                                      m.flag.getTeam()))
        elif isinstance(m, bs.FlagPickedUpMessage):
            # store the last player to hold the flag for scoring purposes
            m.flag._lastPlayerToHold = m.node.getDelegate().getPlayer()
            m.flag._heldCount += 1
            m.flag.resetReturnTimes()
        elif isinstance(m, bs.FlagDroppedMessage):
            # store the last player to hold the flag for scoring purposes
            m.flag._heldCount -= 1
        else:
            bs.TeamGameActivity.handleMessage(self, m)
