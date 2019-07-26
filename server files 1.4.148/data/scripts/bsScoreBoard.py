import bs
import bsUtils
import weakref

class _Entry(object):

    def __init__(self, scoreboard, team, doCover, scale, label, flashLength):

        self._scoreboard = weakref.ref(scoreboard)
        self._doCover = doCover
        self._scale = scale
        self._flashLength = flashLength
        self._width = 140.0*self._scale
        self._height = 32.0*self._scale
        self._barWidth = 2.0*self._scale
        self._barHeight = 32.0*self._scale
        self._barTex = self._backingTex = bs.getTexture('bar')
        self._coverTex = bs.getTexture('uiAtlas')
        self._model = bs.getModel('meterTransparent')

        safeTeamColor = bs.getSafeColor(team.color, targetIntensity=1.0)

        vr = bs.getEnvironment()['vrMode']

        if self._doCover:
            if vr:
                self._backingColor = [0.1+c*0.1 for c in safeTeamColor]
            else:
                self._backingColor = [0.05+c*0.17 for c in safeTeamColor]
        else:
            self._backingColor = [0.05+c*0.1 for c in safeTeamColor]

        self._backing = bs.NodeActor(bs.newNode('image', attrs={
            'scale': (self._width, self._height),
            'opacity': (0.8 if vr else 0.8) if self._doCover else 0.5,
            'color': self._backingColor,
            'vrDepth': -3,
            'attach': 'topLeft',
            'texture': self._backingTex}))

        self._barColor = safeTeamColor
        self._bar = bs.NodeActor(bs.newNode('image', attrs={
            'opacity': 0.7,
            'color': self._barColor,
            'attach': 'topLeft',
            'texture': self._barTex}))

        self._barScale = bs.newNode('combine', owner=self._bar.node, attrs={
            'size': 2,
            'input0': self._barWidth,
            'input1': self._barHeight})

        self._barScale.connectAttr('output', self._bar.node, 'scale')

        self._barPosition = bs.newNode('combine', owner=self._bar.node, attrs={
            'size': 2,
            'input0': 0,
            'input1': 0})

        self._barPosition.connectAttr('output', self._bar.node, 'position')

        self._coverColor = safeTeamColor

        if self._doCover:
            self._cover = bs.NodeActor(bs.newNode('image', attrs={
                'scale': (self._width*1.15, self._height*1.6),
                'opacity': 1.0,
                'color': self._coverColor,
                'vrDepth': 2,
                'attach': 'topLeft',
                'texture': self._coverTex,
                'modelTransparent': self._model}))

        c = safeTeamColor
        self._scoreText = bs.NodeActor(bs.newNode('text', attrs={
            'hAttach': 'left', 'vAttach': 'top', 'hAlign': 'right',
            'vAlign': 'center', 'maxWidth': 130.0 *
            (1.0 - scoreboard._scoreSplit),
            'vrDepth': 2, 'scale': self._scale * 0.9, 'text': '',
            'shadow': 1.0 if vr else 0.5,
            'flatness': (1.0 if vr else 0.5)
            if self._doCover else 1.0, 'color': c}))

        c = safeTeamColor

        if label is not None:
            teamNameLabel = label
        else:
            teamNameLabel = team.name

            # we do our own clipping here; should probably try to tap into some
            # existing functionality
            if type(teamNameLabel) is bs.Lstr:

                # hmmm; if the team-name is a non-translatable value lets go
                # ahead and clip it otherwise we leave it as-is so
                # translation can occur..
                if teamNameLabel.isFlatValue():
                    v = teamNameLabel.evaluate()
                    # in python < 3.5 some unicode chars can have length 2,
                    # so we need to convert to raw int vals for safer trimming
                    vChars = bs.uniToInts(v)
                    if len(vChars) > 10:
                        teamNameLabel = bs.Lstr(
                            value=bs.uniFromInts(vChars[:10])+'...')
            else:
                # in python < 3.5 some unicode chars can have length 2,
                # so we need to convert to raw int vals for safe trimming
                teamNameLabelChars = bs.uniToInts(teamNameLabel)
                if len(teamNameLabelChars) > 10:
                    teamNameLabel = bs.uniFromInts(
                        teamNameLabelChars[:10])+'...'
                teamNameLabel = bs.Lstr(value=teamNameLabel)

        self._nameText = bs.NodeActor(bs.newNode('text', attrs={
            'hAttach': 'left',
            'vAttach': 'top',
            'hAlign': 'left',
            'vAlign': 'center',
            'vrDepth': 2,
            'scale': self._scale*0.9,
            'shadow': 1.0 if vr else 0.5,
            'flatness': (1.0 if vr else 0.5) if self._doCover else 1.0,
            'maxWidth': 130*scoreboard._scoreSplit,
            'text': teamNameLabel,
            'color': c+(1.0,)}))

        self._score = None

    def flash(self, countdown, extraFlash):
        self._flashTimer = bs.Timer(
            100, bs.WeakCall(self._doFlash),
            repeat=True)
        if countdown:
            self._flashCounter = 10
        else:
            self._flashCounter = int(20.0*self._flashLength)
        if extraFlash:
            self._flashCounter *= 4
        self._setFlashColors(True)

    def _setPosition(self, p):
        # abort if we've been killed
        if not self._backing.node.exists():
            return
        self._pos = tuple(p)
        self._backing.node.position = (p[0]+self._width/2, p[1]-self._height/2)
        if self._doCover:
            self._cover.node.position = (
                p[0]+self._width/2, p[1]-self._height/2)
        self._barPosition.input0 = self._pos[0]+self._barWidth/2
        self._barPosition.input1 = self._pos[1]-self._barHeight/2
        self._scoreText.node.position = (
            self._pos[0]+self._width-7.0*self._scale,
            self._pos[1]-self._barHeight+16.0*self._scale)
        self._nameText.node.position = (
            self._pos[0] + 7.0 * self._scale, self._pos[1] - self._barHeight +
            16.0 * self._scale)

    def _setFlashColors(self, f):
        self._flashColors = f

        def _safeSetAttr(node, attr, val):
            if node.exists():
                setattr(node, attr, val)
        if f:
            s = 2.0
            _safeSetAttr(self._backing.node, "color",
                         (self._backingColor[0] * s, self._backingColor[1] * s,
                          self._backingColor[2] * s))
            _safeSetAttr(
                self._bar.node, "color",
                (self._barColor[0] * s, self._barColor[1] * s, self._barColor
                 [2] * s))
            if self._doCover:
                _safeSetAttr(self._cover.node, "color",
                             (self._coverColor[0] * s, self._coverColor[1] * s,
                              self._coverColor[2] * s))
        else:
            _safeSetAttr(self._backing.node, "color", self._backingColor)
            _safeSetAttr(self._bar.node, "color", self._barColor)
            if self._doCover:
                _safeSetAttr(self._cover.node, "color", self._coverColor)

    def _doFlash(self):
        if self._flashCounter <= 0:
            self._setFlashColors(False)
        else:
            self._flashCounter -= 1
            self._setFlashColors(not self._flashColors)

    def setValue(
            self, score, maxScore=None, countdown=False, flash=True,
            showValue=True):

        # if we have no score yet, just set it.. otherwise compare and see if we
        # should flash
        if self._score is None:
            self._score = score
        else:
            if score > self._score or (countdown and score < self._score):
                extraFlash = (maxScore is not None
                              and score >= maxScore
                              and not countdown) or (countdown and score == 0)
                if flash:
                    self.flash(countdown, extraFlash)
            self._score = score

        if maxScore is None:
            self._barWidth = 0.0
        else:
            if countdown:
                self._barWidth = max(
                    2.0 * self._scale, self._width *
                    (1.0 - (float(score) / maxScore)))
            else:
                self._barWidth = max(
                    2.0 * self._scale, self._width *
                    (min(1.0, float(score) / maxScore)))

        curWidth = self._barScale.input0
        bsUtils.animate(self._barScale, 'input0', {
                        0: curWidth, 250: self._barWidth})
        self._barScale.input1 = self._barHeight
        curX = self._barPosition.input0
        bsUtils.animate(
            self._barPosition, 'input0',
            {0: curX, 250: self._pos[0] + self._barWidth / 2})
        self._barPosition.input1 = self._pos[1]-self._barHeight/2
        if showValue:
            self._scoreText.node.text = str(score)
        else:
            self._scoreText.node.text = ''


class _EntryProxy(object):
    """Encapsulates adding/removing of a scoreboard Entry"""

    def __init__(self, scoreboard, team):
        self._scoreboard = weakref.ref(scoreboard)
        # have to store ID here instead of a weak-ref since the team will be
        # dead when we die and need to remove it
        self._teamID = team.getID()

    def __del__(self):
        sb = self._scoreboard()
        # remove our team from the scoreboard if its still around
        if sb is not None:
            sb._removeTeam(self._teamID)


class ScoreBoard(object):
    """
    category: Game Flow Classes

    A display for player or team scores during the game.
    """

    def __init__(self, label=None, scoreSplit=0.7):
        """
        Instantiate a score-board.
        Label can be something like 'points' and will
        show up on boards if provided.
        """
        self._flatTex = bs.getTexture("null")
        self._entries = {}
        self._label = label
        self._scoreSplit = scoreSplit

        # for free-for-all we go simpler since we have one per player
        if isinstance(bs.getSession(), bs.FreeForAllSession):
            self._doCover = False
            self._spacing = 35.0
            self._pos = (17, -65)
            self._scale = 0.8
            self._flashLength = 0.5
        else:
            self._doCover = True
            self._spacing = 50.0
            self._pos = (20, -70)
            self._scale = 1.0
            self._flashLength = 1.0

    def setTeamValue(
            self, team, score, maxScore=None, countdown=False, flash=True,
            showValue=True):
        """
        Update the score-board display for the given team.
        """
        if not team.getID() in self._entries:
            self._addTeam(team)
            # create a proxy in the team which will kill our entry when it dies
            # (for convenience)
            if '_scoreBoardEntry' in team.gameData:
                raise Exception("existing _EntryProxy found")
            team.gameData['_scoreBoardEntry'] = _EntryProxy(self, team)
        # now set the entry..
        self._entries[team.getID()].setValue(score=score, maxScore=maxScore,
                                             countdown=countdown, flash=flash,
                                             showValue=showValue)

    def _addTeam(self, team):
        if team.getID() in self._entries:
            raise Exception('Duplicate team add')
        self._entries[team.getID()] = _Entry(self, team, doCover=self._doCover,
                                             scale=self._scale,
                                             label=self._label,
                                             flashLength=self._flashLength)
        self._updateTeams()

    def _removeTeam(self, teamID):
        del self._entries[teamID]
        self._updateTeams()

    def _updateTeams(self):
        p = list(self._pos)
        for e in self._entries.values():
            e._setPosition(p)
            p[1] -= self._spacing*self._scale
