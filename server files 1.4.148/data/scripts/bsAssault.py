import bs
import random


def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4


def bsGetGames():
    return [AssaultGame]


class AssaultGame(bs.TeamGameActivity):
    @classmethod
    def getName(cls):
        return 'Assault'

    @classmethod
    def getDescription(cls, sessionType):
        return 'Reach the enemy flag to score.'

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.TeamsSession) else False

    @classmethod
    def getSupportedMaps(cls, sessionType):
        return bs.getMapsSupportingPlayType("teamFlag")

    @classmethod
    def getSettings(cls, sessionType):
        return [("Score to Win", {'minValue': 1, 'default': 3}),
                ("Time Limit", {
                    'choices': [('None', 0), ('1 Minute', 60),
                                ('2 Minutes', 120), ('5 Minutes', 300),
                                ('10 Minutes', 600), ('20 Minutes', 1200)],
                    'default': 0}),
                ("Respawn Times", {
                    'choices': [('Shorter', 0.25), ('Short', 0.5),
                                ('Normal', 1.0), ('Long', 2.0),
                                ('Longer', 4.0)],
                    'default': 1.0}),
                ("Epic Mode", {'default': False})] # yapf: disable

    def __init__(self, settings):
        bs.TeamGameActivity.__init__(self, settings)
        self._scoreBoard = bs.ScoreBoard()
        if self.settings['Epic Mode']:
            self._isSlowMotion = True
        self._lastScoreTime = 0
        self._scoreSound = bs.getSound("score")

    def getInstanceDescription(self):
        if self.settings['Score to Win'] == 1:
            return 'Touch the enemy flag.'
        else:
            return ('Touch the enemy flag ${ARG1} times.',
                    self.settings['Score to Win'])

    def getInstanceScoreBoardDescription(self):
        if self.settings['Score to Win'] == 1:
            return 'touch 1 flag'
        else:
            return ('touch ${ARG1} flags', self.settings['Score to Win'])

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(
            self,
            music='Epic' if self.settings['Epic Mode'] else 'ForwardMarch')

    def onTeamJoin(self, team):
        team.gameData['score'] = 0
        self._updateScoreBoard()

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)

        self.setupStandardTimeLimit(self.settings['Time Limit'])
        self.setupStandardPowerupDrops()

        self._baseRegionMaterials = {}
        for team in self.teams:
            m = self._baseRegionMaterials[team.getID()] = bs.Material()
            m.addActions(
                conditions=('theyHaveMaterial',
                            bs.getSharedObject('playerMaterial')),
                actions=(('modifyPartCollision', 'collide',
                          True), ('modifyPartCollision', 'physical', False),
                         ('call', 'atConnect',
                          bs.Call(self._handleBaseCollide, team))))

        # create a score region and flag for each team
        for team in self.teams:
            team.gameData['basePos'] = self.getMap().getFlagPosition(
                team.getID())

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

            self.projectFlagStand(team.gameData['basePos'])

            team.gameData['flag'] = bs.Flag(
                touchable=False,
                position=team.gameData['basePos'],
                color=team.color)
            p = team.gameData['basePos']
            region = bs.newNode(
                'region',
                owner=team.gameData['flag'].node,
                attrs={
                    'position': (p[0], p[1] + 0.75, p[2]),
                    'scale': (0.5, 0.5, 0.5),
                    'type': 'sphere',
                    'materials': [self._baseRegionMaterials[team.getID()]]
                })

    def handleMessage(self, m):
        if isinstance(m, bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self, m)  # augment standard
            self.respawnPlayer(m.spaz.getPlayer())
        else:
            bs.TeamGameActivity.handleMessage(self, m)

    def _flashBase(self, team, length=2000):
        light = bs.newNode(
            'light',
            attrs={
                'position': team.gameData['basePos'],
                'heightAttenuated': False,
                'radius': 0.3,
                'color': team.color
            })
        bs.animate(light, "intensity", {0: 0, 250: 2.0, 500: 0}, loop=True)
        bs.gameTimer(length, light.delete)

    def _handleBaseCollide(self, team):
        cval = bs.getCollisionInfo('opposingNode')
        try:
            player = cval.getDelegate().getPlayer()
        except Exception:
            return
        if player is None or not player.exists() or not player.isAlive():
            return

        # if its another team's player, they scored
        playerTeam = player.getTeam()
        if playerTeam is not team:

            # (prevent multiple simultaneous scores)
            if bs.getGameTime() != self._lastScoreTime:
                self._lastScoreTime = bs.getGameTime()

                self.scoreSet.playerScored(player, 50, bigMessage=True)

                bs.playSound(self._scoreSound)
                self._flashBase(team)

                # move all players on the scoring team back to their start
                # and add flashes of light so its noticable
                for p in playerTeam.players:
                    if p.isAlive():
                        pos = p.actor.node.position
                        light = bs.newNode(
                            'light',
                            attrs={
                                'position': pos,
                                'color': playerTeam.color,
                                'heightAttenuated': False,
                                'radius': 0.4
                            })
                        bs.gameTimer(500, light.delete)
                        bs.animate(light, 'intensity', {
                            0: 0,
                            100: 1.0,
                            500: 0
                        })

                        newPos = \
                            self.getMap().getStartPosition(playerTeam.getID())
                        light = bs.newNode(
                            'light',
                            attrs={
                                'position': newPos,
                                'color': playerTeam.color,
                                'radius': 0.4,
                                'heightAttenuated': False
                            })
                        bs.gameTimer(500, light.delete)
                        bs.animate(light, 'intensity', {
                            0: 0,
                            100: 1.0,
                            500: 0
                        })
                        p.actor.handleMessage(
                            bs.StandMessage(newPos, random.uniform(0, 360)))

                # have teammates celebrate
                for player in playerTeam.players:
                    try:
                        player.actor.node.handleMessage('celebrate', 2000)
                    except Exception:
                        pass

                playerTeam.gameData['score'] += 1
                self._updateScoreBoard()
                if (playerTeam.gameData['score'] >=
                        self.settings['Score to Win']):
                    self.endGame()

    def endGame(self):
        results = bs.TeamGameResults()
        for team in self.teams:
            results.setTeamScore(team, team.gameData['score'])
        self.end(results=results)

    def _updateScoreBoard(self):
        for team in self.teams:
            self._scoreBoard.setTeamValue(team, team.gameData['score'],
                                          self.settings['Score to Win'])
