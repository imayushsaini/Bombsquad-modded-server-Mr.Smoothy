import bs
import bsGame
import bsUtils
import random
import weakref
import copy
import bsTutorial
import bsInternal

gDefaultTeamColors = ((0.6, 0.25, 1.0), (0.0, 0.25, 1.2))
gDefaultTeamNames = ("Swat", "SahilP")

gTeamSeriesLength = 7
gFFASeriesLength = 24


class TeamGameResults(object):
    """
    category: Game Flow Classes

    Results for a completed bs.TeamGameActivity.
    Upon completion, a game should fill one of these out and pass it to its
    bs.Activity.end() call.
    """

    def __init__(self):
        """
        Instantiate a results instance.
        """

        self._gameSet = False
        self._scores = {}

    def _setGame(self, game):
        if self._gameSet:
            raise Exception("game being set twice for TeamGameResults")
        self._gameSet = True
        self._teams = [weakref.ref(team) for team in game.teams]
        scoreInfo = game.getResolvedScoreInfo()
        self._playerInfo = copy.deepcopy(game.initialPlayerInfo)
        self._lowerIsBetter = scoreInfo['lowerIsBetter']
        self._scoreName = scoreInfo['scoreName']
        self._noneIsWinner = scoreInfo['noneIsWinner']
        self._scoreType = scoreInfo['scoreType']

    def setTeamScore(self, team, score):
        """
        Set the score for a given bs.Team.
        This can be a number or None.
        (see the noneIsWinner arg in the constructor)
        """
        self._scores[team.getID()] = (weakref.ref(team), score)

    def _getTeamScore(self, team):
        'Return the score for a given bs.Team'
        for score in self._scores.values():
            if score[0]() is team:
                return score[1]
        # if we have no score, None is assumed
        return None

    def _getTeams(self):
        'Return all bs.Teams in the results.'
        if not self._gameSet:
            raise Exception("cant get this until game is set")
        teams = []
        for teamRef in self._teams:
            team = teamRef()
            if team is not None:
                teams.append(team)
        return teams

    def _hasScoreForTeam(self, team):
        'Return whether there is a score for a given bs.Team'
        for score in self._scores.values():
            if score[0]() is team:
                return True
        return False

    def _getTeamScoreStr(self, team):
        """
        Return a score for a bs.Team as a string,
        properly formatted for the score type.
        """
        if not self._gameSet:
            raise Exception("cant get this until game is set")
        for score in self._scores.values():
            if score[0]() is team:
                if score[1] is None:
                    return '-'
                if self._scoreType == 'seconds':
                    return bsUtils.getTimeString(score[1]*1000, centi=False)
                elif self._scoreType == 'milliseconds':
                    return bsUtils.getTimeString(score[1], centi=True)
                else:
                    return str(score[1])
        return '-'

    def _getScoreName(self):
        'Return the name associated with scores (\'points\', etc)'
        if not self._gameSet:
            raise Exception("cant get this until game is set")
        return self._scoreName

    def _getLowerIsBetter(self):
        'Return whether lower scores are better'
        if not self._gameSet:
            raise Exception("cant get this until game is set")
        return self._lowerIsBetter

    def _getWinningTeam(self):
        'Return the winning bs.Team if there is one; None othewise.'
        if not self._gameSet:
            raise Exception("cant get winners until game is set")
        winners = self._getWinners()
        if len(winners) > 0 and len(winners[0]['teams']) == 1:
            return winners[0]['teams'][0]
        else:
            return None

    def _getWinners(self):
        'Return an ordered list of dicts containing score and teams'
        if not self._gameSet:
            raise Exception("cant get winners until game is set")
        winners = {}
        # filter out any dead teams
        scores = [score for score in self._scores.values()
                  if score[0]() is not None and score[1] is not None]
        for score in scores:
            try:
                s = winners[score[1]]
            except Exception:
                s = winners[score[1]] = []
            s.append(score[0]())
        results = winners.items()
        results.sort(reverse=not self._lowerIsBetter)

        # tack a group with all our 'None' scores onto the end
        noneTeams = [score[0]() for score in self._scores.values()
                     if score[0]() is not None and score[1] is None]
        if len(noneTeams) > 0:
            nones = [(None, noneTeams)]
            if self._noneIsWinner:
                results = nones + results
            else:
                results = results + nones
        return [{'score': r[0], 'teams':r[1]} for r in results]


class ShuffleList(object):
    """
    shuffles a set of games with some smarts
    to avoid repeats in maps or game types
    """

    def __init__(self, items, shuffle=True):
        self.sourceList = items
        self.shuffle = shuffle
        self.shuffleList = []
        self.lastGotten = None

    def pullNext(self):

        # refill our list if its empty
        if len(self.shuffleList) == 0:
            self.shuffleList = list(self.sourceList)

        # ok now find an index we should pull
        index = 0

        if self.shuffle:
            for i in range(4):
                index = random.randrange(0, len(self.shuffleList))
                testObj = self.shuffleList[index]
                # if the new one is the same map or game-type as the previous,
                # lets try to keep looking..
                if len(self.shuffleList) > 1 and self.lastGotten is not None:
                    if testObj['settings']['map'] == \
                       self.lastGotten['settings']['map']:
                        continue
                    if testObj['type'] == self.lastGotten['type']:
                        continue
                # sufficiently different.. lets go with it
                break

        obj = self.shuffleList.pop(index)
        self.lastGotten = obj
        return obj


class TeamsScoreScreenActivity(bsGame.ScoreScreenActivity):

    def __init__(self, settings={}):
        bsGame.ScoreScreenActivity.__init__(self, settings=settings)
        self._scoreDisplaySound = bs.getSound("scoreHit01")
        self._scoreDisplaySoundSmall = bs.getSound("scoreHit02")

    def onBegin(self, showUpNext=True, customContinueMessage=None):
        bsGame.ScoreScreenActivity.onBegin(
            self, customContinueMessage=customContinueMessage)
        if showUpNext:
            t = bs.Lstr(value='${A}   ${B}',
                        subs=[('${A}', bs.Lstr(
                            resource='upNextText',
                            subs=[('${COUNT}',
                                   str(self.getSession().getGameNumber()+1))])
                        ),('${B}', self.getSession().getNextGameDescription())])
            bsUtils.Text(t,
                         maxWidth=900,
                         hAttach='center',
                         vAttach='bottom',
                         hAlign='center',
                         vAlign='center',
                         position=(0, 53),
                         flash=False,
                         color=(0.3, 0.3, 0.35, 1.0),
                         transition='fadeIn',
                         transitionDelay=2000).autoRetain()

    def showPlayerScores(
            self, delay=2500, results=None, scale=1.0, xOffset=0, yOffset=0):
        tsVOffset = 150.0+yOffset
        tsHOffs = 80.0+xOffset
        tDelay = delay
        spacing = 40

        isFreeForAll = isinstance(self.getSession(), bs.FreeForAllSession)

        def _getPlayerScore(player):
            if isFreeForAll and results is not None:
                return results._getTeamScore(player.getTeam())
            else:
                return player.accumScore

        def _getPlayerScoreStr(player):
            if isFreeForAll and results is not None:
                return results._getTeamScoreStr(player.getTeam())
            else:
                return str(player.accumScore)

        # getValidPlayers() can return players that are no longer in the game..
        # if we're using results we have to filter
        # those out (since they're not in results and that's where we pull their
        # scores from)
        if results is not None:
            playersSorted = []
            validPlayers = self.scoreSet.getValidPlayers().items()

            def _getPlayerScoreSetEntry(player):
                for p in validPlayers:
                    if p[1].getPlayer() is player:
                        return p[1]
                return None

            # results is already sorted; just convert it into a list of
            # score-set-entries
            for winner in results._getWinners():
                for team in winner['teams']:
                    if len(team.players) == 1:
                        playerEntry = _getPlayerScoreSetEntry(team.players[0])
                        if playerEntry is not None:
                            playersSorted.append(playerEntry)
        else:
            playersSorted = [
                [_getPlayerScore(p),
                 name, p] for name, p in
                self.scoreSet.getValidPlayers().items()]
            playersSorted.sort(
                reverse=(
                    results
                    is None or
                    not results._getLowerIsBetter()))
            # just want living player entries
            playersSorted = [p[2] for p in playersSorted if p[2]]

        vOffs = -140.0 + spacing*len(playersSorted)*0.5

        def _txt(
                xOffs, yOffs, text, hAlign='right', extraScale=1.0,
                maxWidth=120.0):
            bsUtils.Text(text, color=(0.5, 0.5, 0.6, 0.5),
                         position=(tsHOffs + xOffs * scale, tsVOffset +
                                   (vOffs + yOffs + 4.0) * scale),
                         hAlign=hAlign, vAlign='center', scale=0.8 * scale *
                         extraScale, maxWidth=maxWidth, transition='inLeft',
                         transitionDelay=tDelay).autoRetain()

        _txt(
            180, 43, bs.Lstr(
                resource='gameLeadersText',
                subs=[('${COUNT}', str(self.getSession().getGameNumber()))]),
            hAlign='center', extraScale=1.4, maxWidth=None)
        _txt(-15, 4, bs.Lstr(resource='playerText'), hAlign='left')
        _txt(180, 4, bs.Lstr(resource='killsText'))
        _txt(280, 4, bs.Lstr(resource='deathsText'), maxWidth=100)

        scoreName = 'Score' if results is None else results._getScoreName()
        translated = bs.Lstr(translate=('scoreNames', scoreName))

        _txt(390, 0, translated)

        topKillCount = 0
        topKilledCount = 99999
        topScore = 0 if(
            len(playersSorted) == 0) else _getPlayerScore(
            playersSorted[0])

        for p in playersSorted:
            topKillCount = max(topKillCount, p.accumKillCount)
            topKilledCount = min(topKilledCount, p.accumKilledCount)

        def _scoreTxt(text, xOffs, highlight, delay, maxWidth=70.0):
            bsUtils.Text(
                text,
                position=(tsHOffs + xOffs * scale, tsVOffset + (vOffs + 15)
                          * scale),
                scale=scale, color=(1.0, 0.9, 0.5, 1.0)
                if highlight else(0.5, 0.5, 0.6, 0.5), hAlign='right',
                vAlign='center', maxWidth=maxWidth, transition='inLeft',
                transitionDelay=tDelay + delay).autoRetain()

        for p in playersSorted:
            tDelay += 50
            vOffs -= spacing
            bsUtils.Image(
                p.getIcon(),
                position=(tsHOffs - 12 * scale,
                          tsVOffset + (vOffs + 15.0) * scale),
                scale=(30.0 * scale, 30.0 * scale),
                transition='inLeft', transitionDelay=tDelay).autoRetain()
            bsUtils.Text(
                bs.Lstr(value=p.getName(full=True)),
                maxWidth=160, scale=0.75 * scale,
                position=(tsHOffs + 10.0 * scale,
                          tsVOffset + (vOffs + 15) * scale),
                hAlign='left', vAlign='center', color=bs.getSafeColor(
                    p.getTeam().color + (1,)),
                transition='inLeft', transitionDelay=tDelay).autoRetain()
            _scoreTxt(
                str(p.accumKillCount),
                180, p.accumKillCount == topKillCount, 100)
            _scoreTxt(str(p.accumKilledCount), 280,
                      p.accumKilledCount == topKilledCount, 100)
            _scoreTxt(
                _getPlayerScoreStr(p),
                390, _getPlayerScore(p) == topScore, 200)


class FreeForAllVictoryScoreScreenActivity(TeamsScoreScreenActivity):

    def __init__(self, settings={}):
        TeamsScoreScreenActivity.__init__(self, settings=settings)
        self._transitionTime = 500  # keeps prev activity alive while we fade in

        self._cymbalSound = bs.getSound('cymbal')

    def onBegin(self):
        bsInternal._setAnalyticsScreen('FreeForAll Score Screen')
        TeamsScoreScreenActivity.onBegin(self)

        yBase = 100
        tsHOffs = -305
        tDelay = 1000
        scale = 1.2
        spacing = 37.0

        # we include name and previous score in the sort to reduce the amount
        # of random jumping around the list we do in cases of ties
        playerOrderPrev = list(self.players)
        playerOrderPrev.sort(reverse=True, key=lambda player: (
            player.getTeam().sessionData['previousScore'],
            player.getName(full=True)))
        playerOrder = list(self.players)
        playerOrder.sort(reverse=True,
                         key=lambda player: (
                             player.getTeam().sessionData['score'],
                             player.getTeam().sessionData['score'],
                             player.getName(full=True)))

        vOffs = -74.0 + spacing*len(playerOrderPrev)*0.5

        delay1 = 1300+100
        delay2 = 2900+100
        delay3 = 2900+100

        orderChange = playerOrder != playerOrderPrev

        if orderChange:
            delay3 += 1500

        bs.gameTimer(300, bs.Call(bs.playSound, self._scoreDisplaySound))
        self.showPlayerScores(
            delay=1, results=self.settings['results'],
            scale=1.2, xOffset=-110)

        soundTimes = set()

        def _scoreTxt(
                text, xOffs, yOffs, highlight, delay, extraScale, flash=False):
            return bsUtils.Text(text,
                                position=(tsHOffs+xOffs*scale,
                                          yBase+(yOffs+vOffs+2.0)*scale),
                                scale=scale*extraScale,
                                color=((1.0, 0.7, 0.3, 1.0) if highlight
                                       else (0.7, 0.7, 0.7, 0.7)),
                                hAlign='right',
                                transition='inLeft',
                                transitionDelay=tDelay+delay,
                                flash=flash).autoRetain()
        vOffs -= spacing

        slideAmt = 0.0

        transitionTime = 250
        transitionTime2 = 250

        title = bsUtils.Text(
            bs.Lstr(
                resource='firstToSeriesText',
                subs=[('${COUNT}', str(self.getSession()._ffaSeriesLength))]),
            scale=1.05 * scale,
            position=(tsHOffs - 0.0 * scale, yBase + (vOffs + 50.0) * scale),
            hAlign='center', color=(0.5, 0.5, 0.5, 0.5),
            transition='inLeft', transitionDelay=tDelay).autoRetain()

        vOffs -= 25
        vOffsStart = vOffs

        bs.gameTimer(tDelay+delay3, bs.WeakCall(
            self._safeAnimate,
            title.positionCombine,
            'input0', {0: tsHOffs-0.0*scale,
                       transitionTime2: tsHOffs-(0.0+slideAmt)*scale}))

        for i, player in enumerate(playerOrderPrev):
            vOffs2 = vOffsStart - spacing * (playerOrder.index(player))

            bs.gameTimer(tDelay+300, bs.Call(bs.playSound,
                                             self._scoreDisplaySoundSmall))
            if orderChange:
                bs.gameTimer(tDelay+delay2+100,
                             bs.Call(bs.playSound, self._cymbalSound))

            img = bsUtils.Image(
                player.getIcon(),
                position=(tsHOffs - 72.0 * scale,
                          yBase + (vOffs + 15.0) * scale),
                scale=(30.0 * scale, 30.0 * scale),
                transition='inLeft', transitionDelay=tDelay).autoRetain()
            bs.gameTimer(
                tDelay + delay2, bs.WeakCall(
                    self._safeAnimate, img.positionCombine, 'input1',
                    {0: yBase + (vOffs + 15.0) * scale, transitionTime: yBase +
                     (vOffs2 + 15.0) * scale}))
            bs.gameTimer(
                tDelay + delay3, bs.WeakCall(
                    self._safeAnimate, img.positionCombine, 'input0',
                    {0: tsHOffs - 72.0 * scale, transitionTime2: tsHOffs -
                     (72.0 + slideAmt) * scale}))
            txt = bsUtils.Text(
                bs.Lstr(value=player.getName(full=True)),
                maxWidth=130.0, scale=0.75 * scale,
                position=(tsHOffs - 50.0 * scale,
                          yBase + (vOffs + 15.0) * scale),
                hAlign='left', vAlign='center', color=bs.getSafeColor(
                    player.getTeam().color + (1,)),
                transition='inLeft', transitionDelay=tDelay).autoRetain()
            bs.gameTimer(
                tDelay + delay2, bs.WeakCall(
                    self._safeAnimate, txt.positionCombine, 'input1',
                    {0: yBase + (vOffs + 15.0) * scale, transitionTime: yBase +
                     (vOffs2 + 15.0) * scale}))
            bs.gameTimer(
                tDelay + delay3, bs.WeakCall(
                    self._safeAnimate, txt.positionCombine, 'input0',
                    {0: tsHOffs - 50.0 * scale, transitionTime2: tsHOffs -
                     (50.0 + slideAmt) * scale}))

            txtNum = bsUtils.Text(
                '#' + str(i + 1),
                scale=0.55 * scale,
                position=(tsHOffs - 95.0 * scale,
                          yBase + (vOffs + 8.0) * scale),
                hAlign='right', color=(0.6, 0.6, 0.6, 0.6),
                transition='inLeft', transitionDelay=tDelay).autoRetain()
            bs.gameTimer(
                tDelay + delay3, bs.WeakCall(
                    self._safeAnimate, txtNum.positionCombine, 'input0',
                    {0: tsHOffs - 95.0 * scale, transitionTime2: tsHOffs -
                     (95.0 + slideAmt) * scale}))

            sTxt = _scoreTxt(
                str(player.getTeam().sessionData['previousScore']),
                80, 0, False, 0, 1.0)
            bs.gameTimer(
                tDelay + delay2, bs.WeakCall(
                    self._safeAnimate, sTxt.positionCombine, 'input1',
                    {0: yBase + (vOffs + 2.0) * scale, transitionTime: yBase +
                     (vOffs2 + 2.0) * scale}))
            bs.gameTimer(tDelay+delay3, bs.WeakCall(
                self._safeAnimate, sTxt.positionCombine,
                'input0', {0: tsHOffs+80*scale,
                           transitionTime2: tsHOffs+(80-slideAmt)*scale}))

            scoreChange = player.getTeam().sessionData['score'] \
                - player.getTeam().sessionData['previousScore']
            if scoreChange > 0:
                x = 113
                y = 3.0
                sTxt2 = _scoreTxt(
                    '+' + str(scoreChange),
                    x, y, True, 0, 0.7, flash=True)
                bs.gameTimer(tDelay + delay2, bs.WeakCall(
                    self._safeAnimate, sTxt2.positionCombine,
                    'input1',
                    {0: yBase + (vOffs + y + 2.0) * scale,
                     transitionTime: yBase + (vOffs2 + y + 2.0) *
                     scale}))
                bs.gameTimer(
                    tDelay + delay3, bs.WeakCall(
                        self._safeAnimate, sTxt2.positionCombine, 'input0',
                        {0: tsHOffs + x * scale, transitionTime2: tsHOffs +
                         (x - slideAmt) * scale}))

                def _safeSetAttr(node, attr, value):
                    if node.exists():
                        setattr(node, attr, value)

                bs.gameTimer(tDelay+delay1, bs.Call(
                    _safeSetAttr, sTxt.node, 'color', (1, 1, 1, 1)))
                for j in range(scoreChange):
                    bs.gameTimer(tDelay+delay1+150*j, bs.Call(
                        _safeSetAttr, sTxt.node, 'text',
                        str(player.getTeam().sessionData['previousScore']+j+1)))
                    t = tDelay+delay1+150*j
                    if not t in soundTimes:
                        soundTimes.add(t)
                        bs.gameTimer(
                            t, bs.Call(
                                bs.playSound, self._scoreDisplaySoundSmall))

            vOffs -= spacing

    def _safeAnimate(self, node, attr, keys):
        if node.exists():
            bsUtils.animate(node, attr, keys)


class DrawScoreScreenActivity(TeamsScoreScreenActivity):

    def __init__(self, settings={}):
        TeamsScoreScreenActivity.__init__(self, settings=settings)

    def onTransitionIn(self):
        TeamsScoreScreenActivity.onTransitionIn(self, music=None)

    def onBegin(self):
        bsInternal._setAnalyticsScreen('Draw Score Screen')
        TeamsScoreScreenActivity.onBegin(self)
        bsUtils.ZoomText(bs.Lstr(resource='drawText'), position=(0, 0),
                         maxWidth=400,
                         shiftPosition=(-220, 0), shiftDelay=2000,
                         flash=False, trail=False, jitter=1.0).autoRetain()
        bs.gameTimer(350, bs.Call(bs.playSound, self._scoreDisplaySound))

        if 'results' in self.settings:
            r = self.settings['results']
        else:
            r = None

        self.showPlayerScores(results=r)


class TeamVictoryScoreScreenActivity(TeamsScoreScreenActivity):

    def __init__(self, settings={}):
        TeamsScoreScreenActivity.__init__(self, settings=settings)

    def onBegin(self):
        bsInternal._setAnalyticsScreen('Teams Score Screen')
        TeamsScoreScreenActivity.onBegin(self)

        # call bsOnGameEnd() for any modules that define it..
        # this is intended as a simple way to upload game scores to a server or
        # whatnot TODO...

        height = 130
        activeTeamCount = len(self.teams)
        v = (height*activeTeamCount)/2 - height/2
        i = 0
        shiftTime = 2500

        # usually we say 'Best of 7', but if the language prefers we can say
        # 'First to 4'
        if bsUtils._getResource('bestOfUseFirstToInstead'):
            bestTxt = bs.Lstr(
                resource='firstToSeriesText', subs=[
                    ('${COUNT}', str(self.getSession()._seriesLength/2+1))])
        else:
            bestTxt = bs.Lstr(
                resource='bestOfSeriesText', subs=[
                    ('${COUNT}', str(self.getSession()._seriesLength))])

        bsUtils.ZoomText(bestTxt,
                         position=(0, 175),
                         shiftPosition=(-250, 175), shiftDelay=2500,
                         flash=False, trail=False, hAlign='center',
                         scale=0.25,
                         color=(0.5, 0.5, 0.5, 1.0), jitter=3.0).autoRetain()
        for team in self.teams:
            bs.gameTimer(i*150+150, bs.WeakCall(
                self._showTeamName,
                v-i*height, team, i*200, shiftTime-(i*150+150)))
            bs.gameTimer(i*150+500, bs.Call(bs.playSound,
                                            self._scoreDisplaySoundSmall))
            scored = (team is self.settings['winner'])
            delay = 200
            if scored:
                delay = 1200
                bs.gameTimer(i*150+200, bs.WeakCall(
                    self._showTeamOldScore,
                    v-i*height, team, shiftTime-(i*150+200)))
                bs.gameTimer(i*150+1500, bs.Call(bs.playSound,
                                                 self._scoreDisplaySound))

            bs.gameTimer(i*150+delay, bs.WeakCall(
                self._showTeamScore,
                v-i*height, team, scored, i*200+100, shiftTime-(i*150+delay)))
            i += 1
        self.showPlayerScores()

    def _showTeamName(self, posV, team, killDelay, shiftDelay):
        bsUtils.ZoomText(bs.Lstr(value='${A}:', subs=[('${A}', team.name)]),
                         # team.name+":",
                         position=(100, posV),
                         shiftPosition=(-150, posV), shiftDelay=shiftDelay,
                         flash=False, trail=False, hAlign='right', maxWidth=300,
                         color=team.color, jitter=1.0).autoRetain()

    def _showTeamOldScore(self, posV, team, shiftDelay):
        bsUtils.ZoomText(
            str(team.sessionData['score'] - 1),
            position=(150, posV),
            maxWidth=100, color=(0.6, 0.6, 0.7),
            shiftPosition=(-100, posV),
            shiftDelay=shiftDelay, flash=False, trail=False, lifespan=1000,
            hAlign='left', jitter=1.0).autoRetain()

    def _showTeamScore(self, posV, team, scored, killDelay, shiftDelay):
        bsUtils.ZoomText(str(team.sessionData['score']), position=(150, posV),
                         maxWidth=100,
                         color=(1.0, 0.9, 0.5) if scored else (0.6, 0.6, 0.7),
                         shiftPosition=(-100, posV), shiftDelay=shiftDelay,
                         flash=scored, trail=scored,
                         hAlign='left', jitter=1.0,
                         trailColor=(1, 0.8, 0.0, 0)).autoRetain()


class TeamSeriesVictoryScoreScreenActivity(TeamsScoreScreenActivity):

    def __init__(self, settings={}):
        TeamsScoreScreenActivity.__init__(self, settings=settings)
        self._minViewTime = 15000
        self._isFFA = isinstance(self.getSession(), bs.FreeForAllSession)
        self._allowServerRestart = True

    def onTransitionIn(self):
        # we dont yet want music and stuff..
        TeamsScoreScreenActivity.onTransitionIn(
            self, music=None, showTips=False)

    def onBegin(self):
        bsInternal._setAnalyticsScreen(
            'FreeForAll Series Victory Screen'
            if self._isFFA else 'Teams Series Victory Screen')

        if bs.getEnvironment()['interfaceType'] == 'large':
            s = bs.Lstr(resource='pressAnyKeyButtonPlayAgainText')
        else:
            s = bs.Lstr(resource='pressAnyButtonPlayAgainText')

        TeamsScoreScreenActivity.onBegin(
            self, showUpNext=False, customContinueMessage=s)

        winningTeam = self.settings['winner']

        # pause a moment before playing victory music
        bs.gameTimer(600, bs.WeakCall(self._playVictoryMusic))
        bs.gameTimer(4400, bs.WeakCall(
            self._showWinner, self.settings['winner']))
        bs.gameTimer(4400+200, bs.Call(bs.playSound, self._scoreDisplaySound))

        # make sure to exclude players without teams (this means they're
        # still doing selection)
        if self._isFFA:
            playersSorted = [
                [p.getTeam().sessionData['score'],
                 p.getName(full=True),
                 p] for name, p in self.scoreSet.getValidPlayers().items()
                if p.getTeam() is not None]
            playersSorted.sort(reverse=True)
        else:
            playersSorted = [
                [p.score, p.nameFull, p]
                for name, p in self.scoreSet.getValidPlayers().items()]
            playersSorted.sort(reverse=True)

        tsHeight = 300
        tsHOffs = -390
        t = 6400
        tIncr = 120

        if self._isFFA:
            txt = bs.Lstr(value='${A}:',
                          subs=[('${A}', bs.Lstr(
                              resource='firstToFinalText', subs=[
                                  ('${COUNT}',
                                   str(self.getSession()._ffaSeriesLength))]))])
        else:
            # some languages may prefer to always show 'first to X' instead of
            # 'best of X' FIXME - this will affect all clients connected to
            # us even if they're not using a language with this enabled.. not
            # the end of the world but something to be aware of.
            if bsUtils._getResource('bestOfUseFirstToInstead'):
                txt = bs.Lstr(value='${A}:', subs=[
                    ('${A}', bs.Lstr(resource='firstToFinalText', subs=[
                        ('${COUNT}',
                         str(self.getSession()._seriesLength/2+1))]))])
            else:
                txt = bs.Lstr(value='${A}:', subs=[
                    ('${A}', bs.Lstr(resource='bestOfFinalText', subs=[
                        ('${COUNT}', str(self.getSession()._seriesLength))]))])

        bsUtils.Text(txt,
                     vAlign='center',
                     maxWidth=300,
                     color=(0.5, 0.5, 0.5, 1.0), position=(0, 220),
                     scale=1.2, transition='inTopSlow', hAlign='center',
                     transitionDelay=tIncr*4).autoRetain()

        winScore = (self.getSession()._seriesLength-1)/2+1
        loseScore = 0
        for team in self.teams:
            if team.sessionData['score'] != winScore:
                loseScore = team.sessionData['score']

        if not self._isFFA:
            bsUtils.Text(
                bs.Lstr(
                    resource='gamesToText',
                    subs=[('${WINCOUNT}', str(winScore)),
                          ('${LOSECOUNT}', str(loseScore))]),
                color=(0.5, 0.5, 0.5, 1.0),
                maxWidth=160, vAlign='center', position=(0, -215),
                scale=1.8, transition='inLeft', hAlign='center',
                transitionDelay=4800 + tIncr * 4).autoRetain()

        if self._isFFA:
            vExtra = 120
        else:
            vExtra = 0

        # show game MVP
        if not self._isFFA:
            mvp, mvpName = None, None
            for p in playersSorted:
                if p[2].getTeam() == winningTeam:
                    mvp = p[2]
                    mvpName = p[1]
                    break
            if mvp is not None:
                bsUtils.Text(bs.Lstr(resource='mostValuablePlayerText'),
                             color=(0.5, 0.5, 0.5, 1.0),
                             vAlign='center',
                             maxWidth=300,
                             position=(180, tsHeight/2+15), transition='inLeft',
                             hAlign='left', transitionDelay=t).autoRetain()
                t += 4*tIncr

                bsUtils.Image(
                    mvp.getIcon(),
                    position=(230, tsHeight / 2 - 55 + 14 - 5),
                    scale=(70, 70),
                    transition='inLeft', transitionDelay=t).autoRetain()
                bsUtils.Text(
                    bs.Lstr(value=mvpName),
                    position=(280, tsHeight / 2 - 55 + 15 - 5),
                    hAlign='left', vAlign='center', maxWidth=170, scale=1.3,
                    color=bs.getSafeColor(mvp.getTeam().color + (1,)),
                    transition='inLeft', transitionDelay=t).autoRetain()
                t += 4*tIncr

        # most violent
        mostKills = 0
        for p in playersSorted:
            if p[2].killCount >= mostKills:
                mvp = p[2]
                mvpName = p[1]
                mostKills = p[2].killCount
        if mvp is not None:
            bsUtils.Text(bs.Lstr(resource='mostViolentPlayerText'),
                         color=(0.5, 0.5, 0.5, 1.0),
                         vAlign='center',
                         maxWidth=300,
                         position=(180, tsHeight/2-150+vExtra+15),
                         transition='inLeft',
                         hAlign='left', transitionDelay=t).autoRetain()
            bsUtils.Text(
                bs.Lstr(
                    value='(${A})',
                    subs=[('${A}', bs.Lstr(
                        resource='killsTallyText',
                        subs=[('${COUNT}', str(mostKills))]))]),
                position=(260, tsHeight / 2 - 150 - 15 + vExtra),
                color=(0.3, 0.3, 0.3, 1.0),
                scale=0.6, hAlign='left', transition='inLeft',
                transitionDelay=t).autoRetain()
            t += 4*tIncr

            bsUtils.Image(
                mvp.getIcon(),
                position=(233, tsHeight / 2 - 150 - 30 - 46 + 25 + vExtra),
                scale=(50, 50),
                transition='inLeft', transitionDelay=t).autoRetain()
            bsUtils.Text(
                bs.Lstr(value=mvpName),
                position=(270, tsHeight / 2 - 150 - 30 - 36 + vExtra + 15),
                hAlign='left', vAlign='center', maxWidth=180,
                color=bs.getSafeColor(mvp.getTeam().color + (1,)),
                transition='inLeft', transitionDelay=t).autoRetain()
            t += 4*tIncr

        # most killed
        mostKilled = 0
        mkp, mkpName = None, None
        for p in playersSorted:
            if p[2].killedCount >= mostKilled:
                mkp = p[2]
                mkpName = p[1]
                mostKilled = p[2].killedCount
        if mkp is not None:
            bsUtils.Text(bs.Lstr(resource='mostViolatedPlayerText'),
                         color=(0.5, 0.5, 0.5, 1.0),
                         vAlign='center',
                         maxWidth=300,
                         position=(180, tsHeight/2-300+vExtra+15),
                         transition='inLeft',
                         hAlign='left', transitionDelay=t).autoRetain()
            bsUtils.Text(
                bs.Lstr(
                    value='(${A})',
                    subs=[('${A}', bs.Lstr(
                        resource='deathsTallyText',
                        subs=[('${COUNT}', str(mostKilled))]))]),
                position=(260, tsHeight / 2 - 300 - 15 + vExtra),
                hAlign='left', scale=0.6, color=(0.3, 0.3, 0.3, 1.0),
                transition='inLeft', transitionDelay=t).autoRetain()
            t += 4*tIncr
            bsUtils.Image(
                mkp.getIcon(),
                position=(233, tsHeight / 2 - 300 - 30 - 46 + 25 + vExtra),
                scale=(50, 50),
                transition='inLeft', transitionDelay=t).autoRetain()
            bsUtils.Text(bs.Lstr(value=mkpName),
                         position=(270, tsHeight/2-300-30-36+vExtra+15),
                         hAlign='left', vAlign='center',
                         color=bs.getSafeColor(mkp.getTeam().color+(1,)),
                         maxWidth=180, transition='inLeft',
                         transitionDelay=t).autoRetain()
            t += 4*tIncr

        # now show individual scores
        tDelay = t
        bsUtils.Text(bs.Lstr(resource='finalScoresText'),
                     color=(0.5, 0.5, 0.5, 1.0),
                     position=(tsHOffs, tsHeight/2),
                     transition='inRight',
                     transitionDelay=tDelay).autoRetain()
        tDelay += 4*tIncr

        vOffs = 0.0
        tDelay += len(playersSorted) * 8*tIncr
        for score, name, p in playersSorted:
            tDelay -= 4*tIncr
            vOffs -= 40
            bsUtils.Text(str(p.getTeam().sessionData['score'])
                         if self._isFFA else str(p.score),
                         color=(0.5, 0.5, 0.5, 1.0),
                         position=(tsHOffs + 230, tsHeight / 2 + vOffs),
                         hAlign='right', transition='inRight',
                         transitionDelay=tDelay).autoRetain()
            tDelay -= 4*tIncr

            bsUtils.Image(
                p.getIcon(),
                position=(tsHOffs - 72, tsHeight / 2 + vOffs + 15),
                scale=(30, 30),
                transition='inLeft', transitionDelay=tDelay).autoRetain()
            bsUtils.Text(
                bs.Lstr(value=name),
                position=(tsHOffs - 50, tsHeight / 2 + vOffs + 15),
                hAlign='left', vAlign='center', maxWidth=180,
                color=bs.getSafeColor(p.getTeam().color + (1,)),
                transition='inRight', transitionDelay=tDelay).autoRetain()

        bs.gameTimer(15000, bs.WeakCall(self._showTips))

    def _showTips(self):
        self._tipsText = bsUtils.TipsText(offsY=70)

    def _playVictoryMusic(self):
        # make sure we dont stomp on the next activity's music choice
        if not self.isTransitioningOut():
            bs.playMusic('Victory')

    def _showWinner(self, team):
        if not self._isFFA:
            offsV = 0
            bsUtils.ZoomText(team.name, position=(0, 97),
                             color=team.color, scale=1.15, jitter=1.0,
                             maxWidth=250).autoRetain()
        else:
            offsV = -80
            if len(team.players) == 1:
                i = bsUtils.Image(
                    team.players[0].getIcon(),
                    position=(0, 143),
                    scale=(100, 100)).autoRetain()
                bsUtils.animate(i.node, 'opacity', {0: 0.0, 250: 1.0})
                bsUtils.ZoomText(bs.Lstr(
                    value=team.players[0].getName(
                        full=True, icon=False)),
                    position=(0, 97 + offsV),
                    color=team.color, scale=1.15, jitter=1.0,
                    maxWidth=250).autoRetain()

        sExtra = 1.0 if self._isFFA else 1.0

        # some languages say "FOO WINS" differently for teams vs players
        if isinstance(self.getSession(), bs.FreeForAllSession):
            winsResource = 'seriesWinLine1PlayerText'
        else:
            winsResource = 'seriesWinLine1TeamText'
        winsText = bs.Lstr(resource=winsResource)
        # temp - if these come up as the english default, fall-back to the
        # unified old form which is more likely to be translated

        bsUtils.ZoomText(winsText, position=(0, -10 + offsV),
                         color=team.color, scale=0.65 * sExtra, jitter=1.0,
                         maxWidth=250).autoRetain()
        bsUtils.ZoomText(bs.Lstr(resource='seriesWinLine2Text'),
                         position=(0, -110 + offsV),
                         scale=1.0 * sExtra, color=team.color, jitter=1.0,
                         maxWidth=250).autoRetain()


class TeamJoiningActivity(bsGame.JoiningActivity):
    def __init__(self, settings={}):
        bsGame.JoiningActivity.__init__(self, settings)

    def onTransitionIn(self):
        bsGame.JoiningActivity.onTransitionIn(self)

        bsUtils.ControlsHelpOverlay(delay=1000).autoRetain()

        # show info about the next up game
        self._nextUpText = bsUtils.Text(
            bs.Lstr(
                value='${1} ${2}',
                subs=[('${1}', bs.Lstr(resource='upFirstText')),
                      ('${2}', self.getSession().getNextGameDescription())]),
            hAttach='center', scale=0.7, vAttach='top', hAlign='center',
            position=(0, -70),
            flash=False, color=(0.5, 0.5, 0.5, 1.0),
            transition='fadeIn', transitionDelay=5000)

        # in teams mode, show our two team names
        # (technically should have Lobby handle this, but this works for now)
        if isinstance(bs.getSession(), bs.TeamsSession):
            teamNames = [team.name for team in bs.getSession().teams]
            teamColors = [tuple(team.color) + (0.5,)
                          for team in bs.getSession().teams]
            if len(teamNames) == 2:
                for i in range(2):
                    teamColor = (1, 0, 0)+(1,)
                    bsUtils.Text(teamNames[i],
                                 scale=0.7,
                                 hAttach='center',
                                 vAttach='top',
                                 hAlign='center',
                                 position=(-200+350*i, -100),
                                 color=teamColors[i],
                                 transition='fadeIn').autoRetain()

        bsUtils.Text(bs.Lstr(
            resource='mustInviteFriendsText',
            subs=[('${GATHER}', bs.Lstr(
                resource='gatherWindow.titleText'))]),
            hAttach='center', scale=0.8, hostOnly=True,
            vAttach='center', hAlign='center', position=(0, 0),
            flash=False, color=(0, 1, 0, 1.0),
            transition='fadeIn', transitionDelay=2000,
            transitionOutDelay=7000).autoRetain()


class TeamGameActivity(bs.GameActivity):
    """
    category: Game Flow Classes

    Base class for teams and free-for-all mode games.
    (Free-for-all is essentially just a special case where every
    bs.Player has their own bs.Team)
    """

    @classmethod
    def supportsSessionType(cls, sessionType):
        """
        Class method override;
        returns True for bs.TeamsSessions and bs.FreeForAllSessions;
        False otherwise.
        """
        return True if(
            issubclass(sessionType, bs.TeamsSession)
            or issubclass(sessionType, bs.FreeForAllSession)) else False

    def __init__(self, settings={}):
        bs.GameActivity.__init__(self, settings)
        # by default we don't show kill-points in free-for-all
        # (there's usually some activity-specific score and we dont
        # wanna confuse things)
        if isinstance(bs.getSession(), bs.FreeForAllSession):
            self._showKillPoints = False

    def onTransitionIn(self, music=None):
        bs.GameActivity.onTransitionIn(self, music)

        # on the first game, show the controls UI momentarily
        # (unless we're being run in co-op mode, in which case we leave
        # it up to them)
        if not isinstance(self.getSession(), bs.CoopSession):
            if not self.getSession()._haveShownControlsHelpOverlay:
                delay = 4000
                lifespan = 10000
                if self._isSlowMotion:
                    lifespan = int(lifespan*0.3)
                bsUtils.ControlsHelpOverlay(
                    delay=delay, lifespan=lifespan, scale=0.8,
                    position=(380, 200),
                    bright=True).autoRetain()
                self.getSession()._haveShownControlsHelpOverlay = True

    def onBegin(self):
        bs.GameActivity.onBegin(self)

        # a few achievements...
        try:
            # award a few achievements..
            if issubclass(type(self.getSession()), bs.FreeForAllSession):
                if len(self.players) >= 2:
                    import bsAchievement
                    bsAchievement._awardLocalAchievement('Free Loader')
            elif issubclass(type(self.getSession()), bs.TeamsSession):
                if len(self.players) >= 4:
                    import bsAchievement
                    bsAchievement._awardLocalAchievement('Team Player')
        except Exception:
            bs.printException()

    def spawnPlayerSpaz(self, player, position=None, angle=None):
        """
        Method override; spawns and wires up a standard bs.PlayerSpaz for
        a bs.Player.

        If position or angle is not supplied, a default will be chosen based
        on the bs.Player and their bs.Team.
        """
        if position is None:
            # in teams-mode get our team-start-location
            if isinstance(self.getSession(), bs.TeamsSession):
                position = \
                    self.getMap().getStartPosition(player.getTeam().getID())
            else:
                # otherwise do free-for-all spawn locations
                position = self.getMap().getFFAStartPosition(self.players)

        return bs.GameActivity.spawnPlayerSpaz(self, player, position, angle)

    def end(
            self, results=None, announceWinningTeam=True, announceDelay=100,
            force=False):
        """
        Method override; announces the single winning team
        unless 'announceWinningTeam' is False.  (useful for games where
        there is not a single most-important winner).
        """
        # announce win (but only for the first finish() call)
        # (also don't announce in co-op sessions; we leave that up to them)
        if not isinstance(self.getSession(), bs.CoopSession):
            doAnnounce = not self.hasEnded()
            bs.GameActivity.end(
                self, results, delay=2000+announceDelay, force=force)
            # need to do this *after* end end call so that results is valid
            if doAnnounce:
                self.getSession().announceGameResults(
                    self, results, delay=announceDelay,
                    announceWinningTeam=announceWinningTeam)

        # for co-op we just pass this up the chain with a delay added
        # (in most cases)
        # (team games expect a delay for the announce portion in teams/ffa
        # mode so this keeps it consistent)
        else:
            # dont want delay on restarts..
            if (type(results) is dict
                    and 'outcome' in results
                    and results['outcome'] == 'restart'):
                delay = 0
            else:
                delay = 2000
                bs.gameTimer(100, bs.Call(
                    bs.playSound, bs.getSound("boxingBell")))
            bs.GameActivity.end(self, results, delay=delay, force=force)


class TeamBaseSession(bs.Session):
    """
    category: Game Flow Classes

    Common base class for bs.TeamsSession and bs.FreeForAllSession.
    Free-for-all-mode is essentially just teams-mode with each bs.Player having
    their own bs.Team, so there is much overlap in functionality.
    """

    def __init__(self):
        """
        Sets up playlists and launches a bs.Activity to accept joiners.
        """

        mp = self.getMaxPlayers()
        bsConfig = bs.getConfig()

        if self._useTeams:
            teamNames = bsConfig.get('Custom Team Names', gDefaultTeamNames)
            teamColors = bsConfig.get('Custom Team Colors', gDefaultTeamColors)
        else:
            teamNames = None
            teamColors = None

        bs.Session.__init__(self,
                            teamNames=teamNames, teamColors=teamColors,
                            useTeamColors=self._useTeams,
                            minPlayers=1, maxPlayers=mp)

        self._seriesLength = gTeamSeriesLength
        self._ffaSeriesLength = gFFASeriesLength

        showTutorial = bsConfig.get('Show Tutorial', True)

        if showTutorial:
            # get this loading..
            self._tutorialActivityInstance = bs.newActivity(
                bsTutorial.TutorialActivity)
        else:
            self._tutorialActivityInstance = None

        # TeamGameActivity uses this to display a help overlay on
        # the first activity only
        self._haveShownControlsHelpOverlay = False

        try:
            self._playlistName = bs.getConfig()[self._playlistSelectionVar]
        except Exception:
            self._playlistName = '__default__'
        try:
            self._playlistRandomize = bs.getConfig()[self._playlistRandomizeVar]
        except Exception:
            self._playlistRandomize = False

        # which game activity we're on
        self._gameNumber = 0

        try:
            playlists = bs.getConfig()[self._playlistsVar]
        except Exception:
            playlists = {}

        if (self._playlistName != '__default__'
                and self._playlistName in playlists):
            # (make sure to copy this, as we muck with it in place once we've
            # got it and we dont want that to affect our config)
            playlist = copy.deepcopy(playlists[self._playlistName])
        else:
            if self._useTeams:
                playlist = bsUtils._getDefaultTeamsPlaylist()
            else:
                playlist = bsUtils._getDefaultFreeForAllPlaylist()

        # resolve types and whatnot to get our final playlist
        playlistResolved = bsUtils._filterPlaylist(
            playlist, sessionType=type(self),
            addResolvedType=True)

        if not playlistResolved:
            raise Exception("playlist contains no valid games")

        self._playlist = ShuffleList(
            playlistResolved, shuffle=self._playlistRandomize)

        # get a game on deck ready to go
        self._currentGameSpec = None
        self._nextGameSpec = self._playlist.pullNext()
        self._nextGame = self._nextGameSpec['resolvedType']

        # go ahead and instantiate the next game we'll
        # use so it has lots of time to load
        self._instantiateNextGame()

        # start in our custom join screen
        self.setActivity(bs.newActivity(TeamJoiningActivity))

    def getNextGameDescription(self):
        'Returns a description of the next game on deck'
        return self._nextGameSpec['resolvedType'].getConfigDisplayString(
            self._nextGameSpec)

    def getGameNumber(self):
        'Returns which game in the series is currently being played.'
        return self._gameNumber

    def onTeamJoin(self, team):
        team.sessionData['previousScore'] = team.sessionData['score'] = 0

    def getMaxPlayers(self):
        """
        Return the max number of bs.Players allowed to join the game at once.
        """
        if self._useTeams:
            try:
                return bs.getConfig()['Team Game Max Players']
            except Exception:
                return 8
        else:
            try:
                return bs.getConfig()['Free-for-All Max Players']
            except Exception:
                return 8

    def _instantiateNextGame(self):
        self._nextGameInstance = bs.newActivity(
            self._nextGameSpec['resolvedType'],
            self._nextGameSpec['settings'])

    def onPlayerRequest(self, player):
        return bs.Session.onPlayerRequest(self, player)

    def onActivityEnd(self, activity, results):

        # if we have a tutorial to show,
        # thats the first thing we do no matter what
        if self._tutorialActivityInstance is not None:
            self.setActivity(self._tutorialActivityInstance)
            self._tutorialActivityInstance = None

        # if we're leaving the tutorial activity,
        # pop a transition activity to transition
        # us into a round gracefully (otherwise we'd
        # snap from one terrain to another instantly)
        elif isinstance(activity, bsTutorial.TutorialActivity):
            self.setActivity(bs.newActivity(bsGame.TransitionActivity))

        # if we're in a between-round activity or a restart-activity,
        # hop into a round
        elif (isinstance(activity, bsGame.JoiningActivity)
              or isinstance(activity, bsGame.TransitionActivity)
              or isinstance(activity, bsGame.ScoreScreenActivity)):

            # if we're coming from a series-end activity, reset scores
            if isinstance(activity, TeamSeriesVictoryScoreScreenActivity):
                self.scoreSet.reset()
                self._gameNumber = 0
                for team in self.teams:
                    team.sessionData['score'] = 0
            # otherwise just set accum (per-game) scores
            else:
                self.scoreSet.resetAccum()

            nextGame = self._nextGameInstance

            self._currentGameSpec = self._nextGameSpec
            self._nextGameSpec = self._playlist.pullNext()
            self._gameNumber += 1

            # instantiate the next now so they have plenty of time to load
            self._instantiateNextGame()

            # (re)register all players and wire the score-set to our next
            # activity
            for p in self.players:
                # ..but only ones who have completed joining
                if p.getTeam() is not None:
                    self.scoreSet.registerPlayer(p)
            self.scoreSet.setActivity(nextGame)

            # now flip the current activity
            self.setActivity(nextGame)

        # if we're leaving a round, go to the score screen
        else:
            # teams mode
            if self._useTeams:
                winners = results._getWinners()
                # if everyone has the same score, call it a draw
                if len(winners) < 2:
                    self.setActivity(bs.newActivity(DrawScoreScreenActivity))
                else:
                    winner = winners[0]['teams'][0]
                    winner.sessionData['score'] += 1
                    # if a team has won, show final victory screen...
                    if winner.sessionData['score'] >= (
                            self._seriesLength - 1) / 2 + 1:
                        self.setActivity(
                            bs.newActivity(
                                TeamSeriesVictoryScoreScreenActivity,
                                {'winner': winner}))
                    else:
                        self.setActivity(
                            bs.newActivity(
                                TeamVictoryScoreScreenActivity,
                                {'winner': winner}))
            # free-for-all mode
            else:
                winners = results._getWinners()

                # if there's multiple players and everyone has the same score,
                # call it a draw
                if len(self.players) > 1 and len(winners) < 2:
                    self.setActivity(bs.newActivity(
                        DrawScoreScreenActivity,
                        {'results': results}))
                else:
                    # award different point amounts based on number of players
                    pointAwards = self._getFFAPointAwards()

                    for i, winner in enumerate(winners):
                        for team in winner['teams']:
                            points = pointAwards[i] if i in pointAwards else 0
                            team.sessionData['previousScore'] = \
                                team.sessionData['score']
                            team.sessionData['score'] += points

                    seriesWinners = [team for team in self.teams
                                     if team.sessionData['score']
                                     >= self._ffaSeriesLength]
                    seriesWinners.sort(
                        reverse=True, key=lambda
                        team: (team.sessionData['score']))
                    if len(seriesWinners) == 1 or (
                            len(seriesWinners) > 1
                            and seriesWinners[0].sessionData['score'] !=
                            seriesWinners[1].sessionData['score']):
                        self.setActivity(
                            bs.newActivity(
                                TeamSeriesVictoryScoreScreenActivity,
                                {'winner': seriesWinners[0]}))
                    else:
                        self.setActivity(
                            bs.newActivity(
                                FreeForAllVictoryScoreScreenActivity,
                                {'results': results}))

    def announceGameResults(self, activity, results, delay,
                            announceWinningTeam=True):
        """
        Show game results at the end of a game
        (before transitioning to a score screen).
        This will include a zoom-text of 'BLUE WINS'
        or whatnot, along with a possible audio
        announcement of the same.
        """

        bs.gameTimer(delay, bs.Call(bs.playSound, bs.getSound("boxingBell")))
        if announceWinningTeam:
            winningTeam = results._getWinningTeam()
            if winningTeam is not None:
                # have all players celebrate
                for player in winningTeam.players:
                    try:
                        player.actor.node.handleMessage('celebrate', 10000)
                    except Exception:
                        pass
                activity.cameraFlash()

                # some languages say "FOO WINS" different for teams vs players
                if isinstance(self, bs.FreeForAllSession):
                    winsResource = 'winsPlayerText'
                else:
                    winsResource = 'winsTeamText'
                winsText = bs.Lstr(resource=winsResource, subs=[
                                   ('${NAME}', winningTeam.name)])
                activity.showZoomMessage(
                    winsText, scale=0.85, color=bsUtils.getNormalizedColor(
                        winningTeam.color))


class FreeForAllSession(TeamBaseSession):
    """
    category: Game Flow Classes

    bs.Session type for free-for-all mode games.
    """
    _useTeams = False
    _playlistSelectionVar = 'Free-for-All Playlist Selection'
    _playlistRandomizeVar = 'Free-for-All Playlist Randomize'
    _playlistsVar = 'Free-for-All Playlists'

    def _getFFAPointAwards(self):
        """
        Returns the number of points awarded for different
        rankings based on the current number of players.
        """
        if len(self.players) == 1:
            pointAwards = {}
        elif len(self.players) == 2:
            pointAwards = {0: 6}
        elif len(self.players) == 3:
            pointAwards = {0: 6, 1: 3}
        elif len(self.players) == 4:
            pointAwards = {0: 8, 1: 4, 2: 2}
        elif len(self.players) == 5:
            pointAwards = {0: 8, 1: 4, 2: 2}
        elif len(self.players) == 6:
            pointAwards = {0: 8, 1: 4, 2: 2}
        else:
            pointAwards = {0: 8, 1: 4, 2: 2, 3: 1}
        return pointAwards

    def __init__(self):
        bsInternal._incrementAnalyticsCount('Free-for-all session start')
        TeamBaseSession.__init__(self)


class TeamsSession(TeamBaseSession):
    """
    category: Game Flow Classes

    bs.Session type for teams mode games.
    """
    _useTeams = True
    _playlistSelectionVar = 'Team Tournament Playlist Selection'
    _playlistRandomizeVar = 'Team Tournament Playlist Randomize'
    _playlistsVar = 'Team Tournament Playlists'

    def __init__(self):
        bsInternal._incrementAnalyticsCount('Teams session start')
        TeamBaseSession.__init__(self)
