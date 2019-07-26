import random

import bs


def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4


def bsGetGames():
    return [HockeyGame]


class PuckDeathMessage(object):
    """A puck has died."""

    def __init__(self, puck):
        self.puck = puck


class Puck(bs.Actor):
    def __init__(self, position=(0, 1, 0)):
        bs.Actor.__init__(self)
        activity = self.getActivity()
        # spawn just above the provided point
        self._spawnpos = (position[0], position[1] + 1.0, position[2])
        self.lastplayerstotouch = {}
        self.node = bs.newNode(
            "prop",
            delegate=self,
            attrs={
                'model':
                    activity._puckmodel,
                'colorTexture':
                    activity._pucktex,
                'body':
                    'puck',
                'reflection':
                    'soft',
                'reflectionScale': [0.2],
                'shadowSize':
                    1.0,
                'isAreaOfInterest':
                    True,
                'position':
                    self._spawnpos,
                'materials': [
                    bs.getSharedObject('objectMaterial'),
                    activity._puckmaterial
                ]
            })

    def handleMessage(self, m):
        if isinstance(m, bs.DieMessage):
            self.node.delete()
            activity = self._activity()
            if activity and not m.immediate:
                activity.handleMessage(PuckDeathMessage(self))

        # if we go out of bounds, move back to where we started...
        elif isinstance(m, bs.OutOfBoundsMessage):
            self.node.position = self._spawnpos

        elif isinstance(m, bs.HitMessage):
            self.node.handleMessage(
                "impulse", m.pos[0], m.pos[1], m.pos[2], m.velocity[0],
                m.velocity[1], m.velocity[2], 1.0 * m.magnitude,
                1.0 * m.velocityMagnitude, m.radius, 0, m.forceDirection[0],
                m.forceDirection[1], m.forceDirection[2])

            # if this hit came from a player, log them as the last to touch us
            if m.sourcePlayer is not None:
                activity = self._activity()
                if activity:
                    if m.sourcePlayer in activity.players:
                        self.lastplayerstotouch[m.sourcePlayer.getTeam()
                                                .getID()] = m.sourcePlayer
        else:
            bs.Actor.handleMessage(self, m)


class HockeyGame(bs.TeamGameActivity):
    @classmethod
    def getName(cls):
        return 'Hockey'

    @classmethod
    def getDescription(cls, sessionType):
        return 'Score some goals.'

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.TeamsSession) else False

    @classmethod
    def getSupportedMaps(cls, sessionType):
        return bs.getMapsSupportingPlayType('hockey')

    @classmethod
    def getSettings(cls, sessionType):
        return [
            ("Score to Win", {
                'minValue': 1, 'default': 1, 'increment': 1
            }),
            ("Time Limit", {
                'choices': [('None', 0), ('1 Minute', 60),
                            ('2 Minutes', 120), ('5 Minutes', 300),
                            ('10 Minutes', 600), ('20 Minutes', 1200)],
                'default': 0
            }),
            ("Respawn Times", {
                'choices': [('Shorter', 0.25), ('Short', 0.5), ('Normal', 1.0),
                            ('Long', 2.0), ('Longer', 4.0)],
                'default': 1.0
            })] # yapf: disable

    def __init__(self, settings):
        bs.TeamGameActivity.__init__(self, settings)
        self._scoreBoard = bs.ScoreBoard()

        self._cheersound = bs.getSound("cheer")
        self._chantsound = bs.getSound("crowdChant")
        self._foghornsound = bs.getSound("foghorn")
        self._swipsound = bs.getSound("swip")
        self._whistlesound = bs.getSound("refWhistle")
        self._puckmodel = bs.getModel("puck")
        self._pucktex = bs.getTexture("puckColor")
        self._pucksound = bs.getSound("metalHit")

        self._puckmaterial = bs.Material()
        self._puckmaterial.addActions(
            actions=(("modifyPartCollision", "friction", 0.5)))
        self._puckmaterial.addActions(
            conditions=("theyHaveMaterial",
                        bs.getSharedObject('pickupMaterial')),
            actions=(("modifyPartCollision", "collide", False)))
        self._puckmaterial.addActions(
            conditions=(("weAreYoungerThan", 100), 'and',
                        ("theyHaveMaterial",
                         bs.getSharedObject('objectMaterial'))),
            actions=(("modifyNodeCollision", "collide", False)))
        self._puckmaterial.addActions(
            conditions=("theyHaveMaterial",
                        bs.getSharedObject('footingMaterial')),
            actions=(("impactSound", self._pucksound, 0.2, 5)))
        # keep track of which player last touched the puck
        self._puckmaterial.addActions(
            conditions=("theyHaveMaterial",
                        bs.getSharedObject('playerMaterial')),
            actions=(("call", "atConnect", self._handlepuckplayercollide), ))
        # we want the puck to kill powerups; not get stopped by them
        self._puckmaterial.addActions(
            conditions=("theyHaveMaterial",
                        bs.Powerup.getFactory().powerupMaterial),
            actions=(("modifyPartCollision", "physical", False),
                     ("message", "theirNode", "atConnect", bs.DieMessage())))
        self._scoreregionmaterial = bs.Material()
        self._scoreregionmaterial.addActions(
            conditions=("theyHaveMaterial", self._puckmaterial),
            actions=(("modifyPartCollision", "collide",
                      True), ("modifyPartCollision", "physical", False),
                     ("call", "atConnect", self._handlescore)))

    def getInstanceDescription(self):
        if self.settings['Score to Win'] == 1: return 'Score a goal.'
        else: return ('Score ${ARG1} goals.', self.settings['Score to Win'])

    def getInstanceScoreBoardDescription(self):
        if self.settings['Score to Win'] == 1: return 'score a goal'
        else: return ('score ${ARG1} goals', self.settings['Score to Win'])

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Hockey')

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)

        self.setupStandardTimeLimit(self.settings['Time Limit'])
        self.setupStandardPowerupDrops()

        self._puckspawnpos = self.getMap().getFlagPosition(None)
        self._spawnpuck()

        # set up the two score regions
        defs = self.getMap().defs
        self._scoreregions = []
        self._scoreregions.append(
            bs.NodeActor(
                bs.newNode(
                    "region",
                    attrs={
                        'position': defs.boxes["goal1"][0:3],
                        'scale': defs.boxes["goal1"][6:9],
                        'type': "box",
                        'materials': [self._scoreregionmaterial]
                    })))
        self._scoreregions.append(
            bs.NodeActor(
                bs.newNode(
                    "region",
                    attrs={
                        'position': defs.boxes["goal2"][0:3],
                        'scale': defs.boxes["goal2"][6:9],
                        'type': "box",
                        'materials': [self._scoreregionmaterial]
                    })))
        self._updatescoreboard()
        bs.playSound(self._chantsound)

    def onTeamJoin(self, team):
        team.gameData['score'] = 0
        self._updatescoreboard()

    def _handlepuckplayercollide(self):
        try:
            pucknode, playernode = bs.getCollisionInfo('sourceNode',
                                                       'opposingNode')
            puck = pucknode.getDelegate()
            player = playernode.getDelegate().getPlayer()
        except Exception:
            player = puck = None

        if player is not None and player.exists() and puck is not None:
            puck.lastplayerstotouch[player.getTeam().getID()] = player

    def _killpuck(self):
        self._puck = None

    def _handlescore(self):
        """ a point has been scored """

        # our puck might stick around for a second or two
        # we dont want it to be able to score again
        if self._puck.scored: return

        region = bs.getCollisionInfo("sourceNode")
        for i in range(len(self._scoreregions)):
            if region == self._scoreregions[i].node:
                break

        scoringteam = None
        for team in self.teams:
            if team.getID() == i:
                scoringteam = team
                team.gameData['score'] += 1

                # tell all players to celebrate
                for player in team.players:
                    try:
                        player.actor.node.handleMessage('celebrate', 2000)
                    except Exception:
                        pass

                # if weve got the player from the scoring
                # team that last touched us, give them points
                if (scoringteam.getID() in self._puck.lastplayerstotouch
                        and self._puck.lastplayerstotouch[scoringteam.getID()]
                        .exists()):
                    self.scoreSet.playerScored(
                        self._puck.lastplayerstotouch[scoringteam.getID()],
                        100,
                        bigMessage=True)

                # end game if we won
                if team.gameData['score'] >= self.settings['Score to Win']:
                    self.endGame()

        bs.playSound(self._foghornsound)
        bs.playSound(self._cheersound)

        self._puck.scored = True

        # kill the puck (it'll respawn itself shortly)
        bs.gameTimer(1000, self._killpuck)

        light = bs.newNode(
            'light',
            attrs={
                'position': bs.getCollisionInfo('position'),
                'heightAttenuated': False,
                'color': (1, 0, 0)
            })
        bs.animate(light, 'intensity', {0: 0, 500: 1, 1000: 0}, loop=True)
        bs.gameTimer(1000, light.delete)

        self.cameraFlash(duration=10)
        self._updatescoreboard()

    def endGame(self):
        results = bs.TeamGameResults()
        for t in self.teams:
            results.setTeamScore(t, t.gameData['score'])
        self.end(results=results)

    def _updatescoreboard(self):
        """ update scoreboard and check for winners """
        winscore = self.settings['Score to Win']
        for team in self.teams:
            self._scoreBoard.setTeamValue(team, team.gameData['score'],
                                          winscore)

    def handleMessage(self, m):

        # respawn dead players if they're still in the game
        if isinstance(m, bs.PlayerSpazDeathMessage):
            # augment standard behavior...
            bs.TeamGameActivity.handleMessage(self, m)
            self.respawnPlayer(m.spaz.getPlayer())

        # respawn dead pucks
        elif isinstance(m, PuckDeathMessage):
            if not self.hasEnded():
                bs.gameTimer(3000, self._spawnpuck)
        else:
            bs.TeamGameActivity.handleMessage(self, m)

    def _flashpuckspawn(self):
        light = bs.newNode(
            'light',
            attrs={
                'position': self._puckspawnpos,
                'heightAttenuated': False,
                'color': (1, 0, 0)
            })
        bs.animate(light, 'intensity', {0: 0, 250: 1, 500: 0}, loop=True)
        bs.gameTimer(1000, light.delete)

    def _spawnpuck(self):
        bs.playSound(self._swipsound)
        bs.playSound(self._whistlesound)
        self._flashpuckspawn()
        self._puck = Puck(position=self._puckspawnpos)
        self._puck.scored = False
        self._puck.lastHoldingPlayer = None
        self._puck.light = bs.newNode(
            'light',
            owner=self._puck.node,
            attrs={
                'intensity': 0.3,
                'heightAttenuated': False,
                'radius': 0.2,
                'color': (0.3, 0.0, 1.0)
            })
        self._puck.node.connectAttr('position', self._puck.light, 'position')
