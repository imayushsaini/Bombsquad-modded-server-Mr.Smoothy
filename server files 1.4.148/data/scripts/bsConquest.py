import bs
import random


def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4


def bsGetGames():
    return [ConquestGame]


class ConquestFlag(bs.Flag):
    def __init__(self, *args, **keywds):
        bs.Flag.__init__(self, *args, **keywds)
        self._team = None

    def setTeam(self, team):
        self._team = None if team is None else team

    def getTeam(self):
        return self._team


class ConquestGame(bs.TeamGameActivity):
    @classmethod
    def getName(cls):
        return 'Conquest'

    @classmethod
    def getDescription(cls, sessionType):
        return 'Secure all flags on the map to win.'

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.TeamsSession) else False

    @classmethod
    def getSupportedMaps(self, sessionType):
        return bs.getMapsSupportingPlayType("conquest")

    @classmethod
    def getSettings(cls, sessionType):
        return [
            ("Time Limit",{
                'choices': [('None', 0), ('1 Minute', 60),
                            ('2 Minutes', 120),
                            ('5 Minutes', 300),
                            ('10 Minutes', 600),
                            ('20 Minutes', 1200)],
                'default': 0
            }),
            ('Respawn Times', {
                'choices': [('Shorter', 0.25),
                            ('Short', 0.5),
                            ('Normal', 1.0),
                            ('Long', 2.0),
                            ('Longer', 4.0)],
                'default': 1.0
            }),
            ('Epic Mode', {'default': False})] # yapf: disable

    def __init__(self, settings):
        bs.TeamGameActivity.__init__(self, settings)
        if self.settings['Epic Mode']:
            self._isSlowMotion = True
        self._scoreBoard = bs.ScoreBoard()
        self._scoreSound = bs.getSound('score')
        self._swipSound = bs.getSound('swip')

        self._extraFlagMaterial = bs.Material()

        # we want flags to tell us they've been hit but not react physically
        self._extraFlagMaterial.addActions(
            conditions=('theyHaveMaterial',
                        bs.getSharedObject('playerMaterial')),
            actions=(('modifyPartCollision', 'collide', True),
                     ('call', 'atConnect', self._handleFlagPlayerCollide)))

    def getInstanceDescription(self):
        return ('Secure all ${ARG1} flags.', len(self.getMap().flagPoints))

    def getInstanceScoreBoardDescription(self):
        return ('secure all ${ARG1} flags', len(self.getMap().flagPoints))

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(
            self, music='Epic' if self.settings['Epic Mode'] else 'GrandRomp')

    def onTeamJoin(self, team):
        if self.hasBegun():
            self._updateScores()
        team.gameData['flagsHeld'] = 0

    def onPlayerJoin(self, player):
        player.gameData['respawnTimer'] = None
        # only spawn if this player's team has a flag currently
        if player.getTeam().gameData['flagsHeld'] > 0:
            self.spawnPlayer(player)

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)

        self.setupStandardTimeLimit(self.settings['Time Limit'])
        self.setupStandardPowerupDrops()

        # set up flags with marker lights..
        self._flags = []
        for i in range(len(self.getMap().flagPoints)):
            point = self.getMap().flagPoints[i]
            flag = ConquestFlag(
                position=point,
                touchable=False,
                materials=[self._extraFlagMaterial])
            self.projectFlagStand(point)
            self._flags.append(flag)
            flag.id = i
            flag.light = bs.newNode(
                'light',
                owner=flag.node,
                attrs={
                    'position': point,
                    'intensity': 0.25,
                    'heightAttenuated': False,
                    'radius': 0.3,
                    'color': (1, 1, 1)
                })

        # give teams a flag to start with
        for i in range(len(self.teams)):
            self._flags[i].setTeam(self.teams[i])
            self._flags[i].light.color = self.teams[i].color
            self._flags[i].node.color = self.teams[i].color

        self._updateScores()

        # initial joiners didn't spawn due to no flags being owned yet;
        # spawn them now
        for player in self.players:
            self.spawnPlayer(player)

    def _updateScores(self):

        for team in self.teams:
            team.gameData['flagsHeld'] = 0

        for flag in self._flags:
            try:
                flag.getTeam().gameData['flagsHeld'] += 1
            except Exception:
                pass

        for team in self.teams:
            # if a team finds themselves with no flags, cancel all
            # outstanding spawn-timers
            if team.gameData['flagsHeld'] == 0:
                for player in team.players:
                    player.gameData['respawnTimer'] = None
                    player.gameData['respawnIcon'] = None
            if team.gameData['flagsHeld'] == len(self._flags):
                self.endGame()
            self._scoreBoard.setTeamValue(team, team.gameData['flagsHeld'],
                                          len(self._flags))

    def endGame(self):
        results = bs.TeamGameResults()
        for t in self.teams:
            results.setTeamScore(t, t.gameData['flagsHeld'])
        self.end(results=results)

    def _flashFlag(self, flag, length=1000):
        light = bs.newNode(
            'light',
            attrs={
                'position': flag.node.position,
                'heightAttenuated': False,
                'color': flag.light.color
            })
        bs.animate(light, "intensity", {0: 0, 250: 1, 500: 0}, loop=True)
        bs.gameTimer(length, light.delete)

    def _handleFlagPlayerCollide(self):
        flagNode, playerNode = bs.getCollisionInfo("sourceNode",
                                                   "opposingNode")
        try:
            player = playerNode.getDelegate().getPlayer()
            flag = flagNode.getDelegate()
        except Exception:
            return  # player may have left and his body hit the flag

        if flag.getTeam() is not player.getTeam():
            flag.setTeam(player.getTeam())
            flag.light.color = player.getTeam().color
            flag.node.color = player.getTeam().color
            self.scoreSet.playerScored(player, 10, screenMessage=False)
            bs.playSound(self._swipSound)
            self._flashFlag(flag)
            self._updateScores()

            # respawn any players on this team that were in limbo due to the
            # lack of a flag for their team
            for p in self.players:
                if (p.getTeam() is flag.getTeam() and p.actor is not None
                        and not p.isAlive()
                        and p.gameData['respawnTimer'] is None):
                    self.spawnPlayer(p)

    def handleMessage(self, m):
        if isinstance(m, bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,
                                              m)  # augment standard behavior

            # respawn only if this team has a flag
            player = m.spaz.getPlayer()
            if player.getTeam().gameData['flagsHeld'] > 0:
                self.respawnPlayer(m.spaz.getPlayer())
            else:
                player.gameData['respawnTimer'] = None

        else:
            bs.TeamGameActivity.handleMessage(self, m)

    def spawnPlayer(self, player):
        # we spawn players at different places based on what flags are held
        self.spawnPlayerSpaz(player, self._getPlayerSpawnPosition(player))

    def _getPlayerSpawnPosition(self, player):

        # iterate until we find a spawn owned by this team..
        spawnCount = len(self.getMap().spawnByFlagPoints)

        # get all spawns owned by this team
        spawns = [
            i for i in range(spawnCount)
            if self._flags[i].getTeam() is player.getTeam()
        ]

        closestSpawn = 0
        closestDistance = 9999

        # now find the spawn thats closest to a spawn not owned by us..
        # we'll use that one
        for s in spawns:
            p = self.getMap().spawnByFlagPoints[s]
            ourPt = bs.Vector(p[0], p[1], p[2])
            for os in [
                    i for i in range(spawnCount)
                    if self._flags[i].getTeam() is not player.getTeam()
            ]:
                p = self.getMap().spawnByFlagPoints[os]
                theirPt = bs.Vector(p[0], p[1], p[2])
                dist = (theirPt - ourPt).length()
                if dist < closestDistance:
                    closestDistance = dist
                    closestSpawn = s

        pt = self.getMap().spawnByFlagPoints[closestSpawn]
        xRange = (-0.5, 0.5) if pt[3] == 0 else (-pt[3], pt[3])
        zRange = (-0.5, 0.5) if pt[5] == 0 else (-pt[5], pt[5])
        pt = (pt[0] + random.uniform(*xRange), pt[1],
              pt[2] + random.uniform(*zRange))
        return pt
