import bs
import bsUtils
import random
import weakref
import copy
import bsUI
import bsAchievement
import bsGame
import bsInternal
import bsTutorial

# team info
gTeamColors = ((0.2, 0.4, 1.6),)
gTeamNames = ("Good Guys",)

_gCampaigns = {}


def _registerCampaign(c):
    _gCampaigns[c._name] = c


def getCampaign(name): return _gCampaigns[name]


class Level(object):
    """
    category: Game Flow Classes

    Represents a distinct named co-op game/map/settings combination.
    """

    def __init__(self, name, gameType, settings, previewTexName,
                 displayName=None):
        """
        Initializes a Level object with the provided values.
        """
        self._name = name
        self._gameType = gameType
        self._settings = settings
        self._previewTexName = previewTexName
        self._displayName = displayName
        self._campaign = None
        self._index = None
        self._scoreVersionString = None

    def getName(self):
        'Returns the unique name for this Level.'
        return self._name

    def getSettings(self):
        'Returns the settings for this Level.'
        settings = copy.deepcopy(self._settings)
        # so the game knows what the level is called.. (hmm can we take
        # this out?..)
        settings['name'] = self._name
        return settings

    def getPreviewTexName(self):
        'Returns the preview texture name for this Level.'
        return self._previewTexName

    def getPreviewTex(self):
        'Loads/returns the preview Texture for this Level.'
        return bs.getTexture(self._previewTexName)

    def getDisplayString(self):
        'Returns a bs.Lstr representing the name of this Level'
        return bs.Lstr(
            translate=('coopLevelNames', self._displayName
                       if self._displayName is not None else self._name),
            subs=[('${GAME}', self._gameType.getDisplayString(
                self._settings))])

    def getGameType(self):
        'Returns the game-type for this Level.'
        return self._gameType

    def getCampaign(self):
        'Returns the campaign this Level is associated with, or None otherwise.'
        return None if self._campaign is None else self._campaign()

    def getIndex(self):
        """
        Returns the order this Level is at in its Campaign. 
        Raises an Exception if not a Campaign Level
        """
        if self._index is None:
            raise Exception("Level is not part of a campaign")
        return self._index

    def getComplete(self):
        'Returns whether this Level has been completed.'
        config = self._getConfigDict()
        try:
            return config['Complete']
        except Exception:
            return False

    def setComplete(self, val):
        'Set whether or not this level is complete.'
        oldVal = self.getComplete()
        if val != oldVal:
            config = self._getConfigDict()
            config['Complete'] = val

    def getHighScores(self):
        'Returns the current high scores for this Level.'
        config = self._getConfigDict()
        highScoresKey = 'High Scores'+self.getScoreVersionString()
        if not highScoresKey in config:
            return {}
        return copy.deepcopy(config[highScoresKey])

    def setHighScores(self, highScores):
        'Sets high scores for this level.'
        config = self._getConfigDict()
        highScoresKey = 'High Scores'+self.getScoreVersionString()
        config[highScoresKey] = highScores

    def getScoreVersionString(self):
        """
        Returns the score version string for this Level.
        If a Level's gameplay changes significantly, its version string
        can be changed to separate its high score lists/etc. from the old.
        """
        if self._scoreVersionString is None:
            s = self._gameType.getResolvedScoreInfo()['scoreVersion']
            if s != '':
                s = ' '+s
            self._scoreVersionString = s
        return self._scoreVersionString

    def getRating(self):
        'Returns the current rating for this Level.'
        config = self._getConfigDict()
        try:
            return config['Rating']
        except Exception:
            return 0.0

    def submitRating(self, rating):
        'Submits a rating for this Level, replacing the old if it is higher.'
        oldRating = self.getRating()
        config = self._getConfigDict()
        config['Rating'] = max(oldRating, rating)

    def _getConfigDict(self):
        campaign = self.getCampaign()
        if campaign is None:
            raise Exception("level is not in a campaign")
        campaignConfig = campaign._getConfigDict()
        try:
            config = campaignConfig[self._name]
        except Exception:
            config = campaignConfig[self._name] = {
                'Rating': 0.0, 'Complete': False}
        return config

    # for transition away from raw dictionaries...
    # should take this out soon once we're sure this is not getting called..
    def __getitem__(self, name):
        global gFooBar
        if not gFooBar:
            import traceback
            print 'FIXME; accessing level as a dict ('+name+')'
            traceback.print_stack()
            gFooBar = True
        if name == 'name':
            return self._name
        elif name == 'gameType':
            return self._gameType
        elif name == 'settings':
            return self._settings
        elif name == 'previewTex':
            return self._previewTexName
        elif name == 'displayName':
            return self._displayName
        elif name == 'index':
            return self.getIndex()
        elif name == 'Rating':
            return self.getRating()
        elif name == 'Complete':
            return self.getComplete()
        else:
            raise Exception("invalid item: "+name)


gFooBar = False


class Campaign(object):

    def __init__(self, name, sequential=True):
        self._name = name
        self._levels = []
        self._sequential = sequential

    def getName(self):
        return self._name

    def isSequential(self):
        return self._sequential

    def addLevel(self, level):
        if level.getCampaign() is not None:
            raise Exception("level already belongs to a campaign")
        level._index = len(self._levels)
        self._levels.append(level)
        level._campaign = weakref.ref(self)

    def getLevels(self):
        return self._levels

    def getLevel(self, name):
        for l in self._levels:
            if l._name == name:
                return l
        raise Exception(
            "Level '"+name+"' not found in campaign '"+self.getName()+"'")

    def reset(self):
        self._getConfigDict()  # make sure path exists..
        bs.getConfig()['Campaigns'][self._name] = {}
        bs.writeConfig()

    # FIXME should these give/take levels instead of level names?..
    def setSelectedLevel(self, levelName):
        self._getConfigDict()['Selection'] = levelName
        bs.writeConfig()

    def getSelectedLevel(self):
        try:
            return self._getConfigDict()['Selection']
        except Exception:
            return self._levels[0]['name']

    def _getConfigDict(self):
        if not 'Campaigns' in bs.getConfig():
            bs.getConfig()['Campaigns'] = {}
        if not self._name in bs.getConfig()['Campaigns']:
            bs.getConfig()['Campaigns'][self._name] = {}
        return bs.getConfig()['Campaigns'][self._name]


class CoopScoreScreen(bs.Activity):

    def __init__(self, settings={}):
        bs.Activity.__init__(self, settings=settings)
        self._transitionTime = 500  # keeps prev activity alive while we fade in
        self._inheritsTint = True
        self._inheritsCameraVROffset = True
        self._inheritsMusic = True
        self._useFixedVROverlay = True

        self._tournamentTimeRemaining = None
        self._tournamentTimeRemainingText = None

        self._doNewRating = \
            True if self.getSession()._tournamentID is not None else False

        # self._goldTex = bs.getTexture('medalGold')
        # self._silverTex = bs.getTexture('medalSilver')
        # self._bronzeTex = bs.getTexture('medalBronze')

        self.scoreDisplaySound = bs.getSound("scoreHit01")
        self.scoreDisplaySoundSmall = bs.getSound("scoreHit02")
        self.drumRollSound = bs.getSound('drumRoll')
        self.cymbalSound = bs.getSound('cymbal')
        # these get used in UI bits so need to load them in the UI context
        with bs.Context('UI'):
            self._replayIconTexture = bs.getTexture('replayIcon')
            self._menuIconTexture = bs.getTexture('menuIcon')
            self._nextLevelIconTexture = bs.getTexture('nextLevelIcon')

        self._haveAchievements = \
            True if bsAchievement.getAchievementsForCoopLevel(
                settings['campaign'].getName()+":"+settings['level']) else False

        self._accountType = bsInternal._getAccountType(
        ) if bsInternal._getAccountState() == 'SIGNED_IN' else None

        with bs.Context('UI'):
            if self._accountType == 'Game Center':
                self._gameServiceIconColor = (1, 1, 1)
                self._gameServiceAchievementsTexture = \
                    self._gameServiceLeaderboardsTexture = \
                        bs.getTexture('gameCenterIcon')
                self._accountHasAchievements = True
            elif self._accountType == 'Game Circle':
                self._gameServiceIconColor = (1, 1, 1)
                self._gameServiceAchievementsTexture = \
                    self._gameServiceLeaderboardsTexture = \
                        bs.getTexture('gameCircleIcon')
                self._accountHasAchievements = True
            elif self._accountType == 'Google Play':
                self._gameServiceIconColor = (0.8, 1.0, 0.6)
                self._gameServiceAchievementsTexture = bs.getTexture(
                    'googlePlayAchievementsIcon')
                self._gameServiceLeaderboardsTexture = bs.getTexture(
                    'googlePlayLeaderboardsIcon')
                self._accountHasAchievements = True
            else:
                self._gameServiceIconColor = \
                    self._gameServiceAchievementsTexture = \
                        self._gameServiceLeaderboardsTexture = None
                self._accountHasAchievements = False

        self._cashRegisterSound = bs.getSound('cashRegister')
        self._gunCockingSound = bs.getSound('gunCocking')
        self._dingSound = bs.getSound('ding')
        self._scoreLink = None
        self._rootUI = None

    def __del__(self):
        bs.Activity.__del__(self)
        # if our UI is still up, kill it
        if self._rootUI is not None and self._rootUI.exists():
            with bs.Context('UI'):
                bs.containerWidget(edit=self._rootUI, transition='outLeft')

    def onTransitionIn(self):
        bsInternal._setAnalyticsScreen('Coop Score Screen')
        bs.Activity.onTransitionIn(self)
        self._background = bsUtils.Background(
            fadeTime=450, startFaded=False, showLogo=True)

    def _uiMenu(self):

        if bsUI._showOffer():
            return

        bs.containerWidget(edit=self._rootUI, transition='outLeft')
        with bs.Context(self):
            bs.gameTimer(100, bs.Call(bs.WeakCall(self.getSession().end)))

    def _uiRestart(self):

        if bsUI._showOffer():
            return

        # if we're in a tournament and it looks like there's no time left,
        # disallow...
        if self.getSession()._tournamentID is not None:
            if self._tournamentTimeRemaining is None:
                bs.screenMessage(
                    bs.Lstr(resource='tournamentCheckingStateText'),
                    color=(1, 0, 0))
                bs.playSound(bs.getSound('error'))
                return
            if self._tournamentTimeRemaining <= 0:
                bs.screenMessage(
                    bs.Lstr(resource='tournamentEndedText'),
                    color=(1, 0, 0))
                bs.playSound(bs.getSound('error'))
                return

        # if there are currently fewer players than our session min,
        # don't allow..
        if len(self.players) < self.getSession()._minPlayers:
            bs.screenMessage(
                bs.Lstr(resource='notEnoughPlayersRemainingText'),
                color=(1, 0, 0))
            bs.playSound(bs.getSound('error'))
            return
        self._campaign.setSelectedLevel(self._level)

        # if this is a tournament, go back to the tournament-entry UI
        # otherwise just hop back in
        tournamentID = self.getSession()._tournamentID
        if tournamentID is not None:
            bsUI.TournamentEntryWindow(
                tournamentID=tournamentID,
                tournamentActivity=self,
                position=self._restartButton.getScreenSpaceCenter())
        else:
            bs.containerWidget(edit=self._rootUI, transition='outLeft')
            self._canShowAdOnDeath = True
            with bs.Context(self):
                self.end({'outcome': 'restart'})

    def _uiNext(self):

        if bsUI._showOffer():
            return

        # if we didn't just complete this level but are choosing
        # to play the next one, set it as current
        # (this won't happen otherwise)
        if self._isComplete and self._isMoreLevels and not self._newlyComplete:
            self._campaign.setSelectedLevel(self._nextLevelName)
        bs.containerWidget(edit=self._rootUI, transition='outLeft')
        with bs.Context(self):
            self.end({'outcome': 'nextLevel'})

    def _uiGC(self):
        bsInternal._showOnlineScoreUI(
            'leaderboard', game=self._gameNameStr,
            gameVersion=self._gameConfigStr)

    def _uiShowAchievements(self):
        bsInternal._showOnlineScoreUI('achievements')

    def _uiWorldsBest(self):
        if self._scoreLink is None:
            bs.playSound(bs.getSound('error'))
            bs.screenMessage(
                bs.Lstr(resource='scoreListUnavailableText'),
                color=(1, 0.5, 0))
        else:
            bs.openURL(self._scoreLink)

    def _uiError(self):
        with bs.Context(self):
            self._nextLevelError = bsUtils.Text(
                bs.Lstr(resource='completeThisLevelToProceedText'),
                flash=True, maxWidth=360, scale=0.54, hAlign='center',
                color=(0.5, 0.7, 0.5, 1),
                position=(300, -235))
            bs.playSound(bs.getSound('error'))
            bs.gameTimer(2000, bs.WeakCall(
                self._nextLevelError.handleMessage,
                bs.DieMessage()))

    def _shouldShowWorldsBestButton(self):
        # link is too complicated to display with no browser
        return bs.isBrowserLikelyAvailable()

    def requestUI(self):
        # we don't want to just show our UI in case the user already has the
        # main menu up so instead we add a callback for when the menu goes away;
        # if we're still alive, we'll come up then
        # if there's no menu this gets called immediately
        bsUI.addMainMenuCloseCallback(bs.WeakCall(self.showUI))

    def showUI(self):
        delay = 700 if (self._score is not None) else 0

        # if there's no players left in the game, lets not show the UI
        # (that would allow restarting the game with zero players, etc)

        # hmm shouldnt need this try/except here i dont think..
        try:
            players = self.players
        except Exception as e:
            print ('EXC bsCoopGame showUI cant get '
                   'self.players; shouldnt happen:'), e
            players = []
        if len(players) == 0:
            return

        d = self._rootUI = bs.containerWidget(size=(0, 0), transition='inRight')

        hOffs = 7
        vOffs = -280

        # we wanna prevent controllers users from popping up browsers
        # or game-center widgets in cases where they cant easily get back
        # to the game (like on mac)
        canSelectExtraButtons = True if bs.getEnvironment(
        )['platform'] == 'android' else False

        bsInternal._setUIInputDevice(None)  # menu is up for grabs

        if self._showFriendScores:
            gcButton = bs.buttonWidget(
                parent=d, color=(0.45, 0.4, 0.5),
                position=(hOffs - 520, vOffs + 480),
                size=(300, 60),
                label=bs.Lstr(resource='topFriendsText'),
                onActivateCall=bs.WeakCall(self._uiGC),
                transitionDelay=delay + 500,
                icon=self._gameServiceLeaderboardsTexture,
                iconColor=self._gameServiceIconColor, autoSelect=True,
                selectable=canSelectExtraButtons)

        if self._haveAchievements and self._accountHasAchievements:
            gcButton = bs.buttonWidget(
                parent=d, color=(0.45, 0.4, 0.5),
                position=(hOffs - 520, vOffs + 450 - 235 + 40),
                size=(300, 60),
                label=bs.Lstr(resource='achievementsText'),
                onActivateCall=bs.WeakCall(self._uiShowAchievements),
                transitionDelay=delay + 1500,
                icon=self._gameServiceAchievementsTexture,
                iconColor=self._gameServiceIconColor, autoSelect=True,
                selectable=canSelectExtraButtons)

        if self._shouldShowWorldsBestButton():
            gcButton = bs.buttonWidget(
                parent=d, color=(0.45, 0.4, 0.5),
                position=(160, vOffs + 480),
                size=(350, 62),
                label=bs.Lstr(resource='tournamentStandingsText')
                if self.getSession()._tournamentID is not None else bs.Lstr(
                    resource='worldsBestScoresText')
                if self._scoreType == 'points' else bs.Lstr(
                    resource='worldsBestTimesText'), autoSelect=True,
                onActivateCall=bs.WeakCall(self._uiWorldsBest),
                transitionDelay=delay + 1900, selectable=canSelectExtraButtons)
        else:
            pass

        showNextButton = (True if self._isMoreLevels
                          and not bsUtils.gRunningKioskModeGame else False)

        if not showNextButton:
            hOffs += 70

        menuButton = bs.buttonWidget(
            parent=d, autoSelect=True, position=(hOffs - 130 - 60, vOffs),
            size=(110, 85),
            label='', onActivateCall=bs.WeakCall(self._uiMenu))
        i = bs.imageWidget(
            parent=d, drawController=menuButton,
            position=(hOffs - 130 - 60 + 22, vOffs + 14),
            size=(60, 60),
            texture=self._menuIconTexture, opacity=0.8)
        self._restartButton = restartButton = bs.buttonWidget(
            parent=d, autoSelect=True, position=(hOffs - 60, vOffs),
            size=(110, 85),
            label='', onActivateCall=bs.WeakCall(self._uiRestart))
        i = bs.imageWidget(
            parent=d, drawController=restartButton,
            position=(hOffs - 60 + 19, vOffs + 7),
            size=(70, 70),
            texture=self._replayIconTexture, opacity=0.8)

        # our 'next' button is disabled if we havn't unlocked the next
        # level yet and invisible if there is none
        if showNextButton:
            if self._isComplete:
                call = bs.WeakCall(self._uiNext)
                buttonSound = True
                imageOpacity = 0.8
                color = None
            else:
                call = bs.WeakCall(self._uiError)
                buttonSound = False
                imageOpacity = 0.2
                color = (0.3, 0.3, 0.3)
            nextButton = bs.buttonWidget(
                parent=d, autoSelect=True, position=(hOffs + 130 - 60, vOffs),
                size=(110, 85),
                label='', onActivateCall=call, color=color,
                enableSound=buttonSound)
            i = bs.imageWidget(
                parent=d, drawController=nextButton,
                position=(hOffs + 130 - 60 + 12, vOffs + 5),
                size=(80, 80),
                texture=self._nextLevelIconTexture, opacity=imageOpacity)

        xOffsExtra = 0 if showNextButton else -100
        self._cornerButtonOffs = (hOffs + 300 + 100 + xOffsExtra, vOffs+560)

        if bsUtils.gRunningKioskModeGame:
            self._powerRankingButtonInstance = None
            self._storeButtonInstance = None
        else:
            self._powerRankingButtonInstance = bsUI.PowerRankingButton(
                parent=d,
                position=(hOffs + 300 + 100 + xOffsExtra, vOffs + 560),
                size=(100, 60),
                scale=0.9, color=(0.4, 0.4, 0.9),
                textColor=(0.9, 0.9, 2.0),
                transitionDelay=0, smoothUpdateDelay=5000)
            self._storeButtonInstance = bsUI.StoreButton(
                parent=d,
                position=(hOffs + 400 + 100 + xOffsExtra, vOffs + 560),
                showTickets=True, saleScale=0.85, size=(100, 60),
                scale=0.9, buttonType='square', color=(0.35, 0.25, 0.45),
                textColor=(0.9, 0.7, 1.0),
                transitionDelay=0)

        bs.containerWidget(
            edit=d, selectedChild=nextButton
            if(self._newlyComplete and self._victory and showNextButton) else
            restartButton, onCancelCall=menuButton.activate)

        self._updateCornerButtonPositions()
        self._updateCornerButtonPositionsTimer = bs.Timer(1000, bs.WeakCall(
            self._updateCornerButtonPositions), repeat=True, timeType='real')

    def _updateCornerButtonPositions(self):
        offs = -55 if bsInternal._isPartyIconVisible() else 0
        posX = self._cornerButtonOffs[0] + offs
        posY = self._cornerButtonOffs[1]
        if self._powerRankingButtonInstance is not None:
            self._powerRankingButtonInstance.setPosition((posX, posY))
        if self._storeButtonInstance is not None:
            self._storeButtonInstance.setPosition((posX+100, posY))

    def onBegin(self):

        bs.Activity.onBegin(self)

        self._playerInfo = self.settings['playerInfo']
        self._score = self.settings['score']
        self._failMessage = self.settings['failMessage']

        self._beginTime = bs.getGameTime()

        if 'scoreOrder' in self.settings:
            if not self.settings['scoreOrder'] in ['increasing', 'decreasing']:
                raise Exception(
                    "Invalid score order: "+self.settings['scoreOrder'])
            self._scoreOrder = self.settings['scoreOrder']
        else:
            self._scoreOrder = 'increasing'

        if 'scoreType' in self.settings:
            if not self.settings['scoreType'] in ['points', 'time']:
                raise Exception(
                    "Invalid score type: "+self.settings['scoreType'])
            self._scoreType = self.settings['scoreType']
        else:
            self._scoreType = 'points'

        self._campaign = self.settings['campaign']
        self._level = self.settings['level']

        self._gameNameStr = self._campaign.getName()+":"+self._level
        self._gameConfigStr = str(
            len(self._playerInfo)) + "p" + self._campaign.getLevel(
            self._level).getScoreVersionString().replace(
            ' ', '_')

        # if game-center/etc scores are available we show our friends' scores
        # otherwise we show our local high scores
        self._showFriendScores = bsInternal._gameServiceHasLeaderboard(
            self._gameNameStr, self._gameConfigStr)

        try:
            self._oldBestRank = self._campaign.getLevel(self._level).getRating()
        except Exception:
            self._oldBestRank = 0.0

        # calc whether the level is complete and other stuff
        victory = (self.settings['outcome'] == 'victory')
        levels = self._campaign.getLevels()
        # HACK; on easy mode we disregard the last level; it's just a
        # placeholder to tell the user to play hard mode
        level = self._campaign.getLevel(self._level)
        self._victory = victory
        self._wasComplete = level.getComplete()
        self._isComplete = (self._wasComplete or victory)
        self._newlyComplete = (self._isComplete and not self._wasComplete)
        self._isMoreLevels = (level.getIndex() < len(
            levels)-1) and self._campaign.isSequential()

        # any time we complete a level, set the next one as unlocked
        if self._isComplete and self._isMoreLevels:

            bsInternal._addTransaction({'type': 'COMPLETE_LEVEL',
                                        'campaign': self._campaign.getName(),
                                        'level': self.settings['level']})

            self._nextLevelName = levels[level.getIndex()+1].getName()

            # if this is the first time we completed it, set the next one
            # as current
            if self._newlyComplete:
                bs.getConfig()['Selected Coop Game'] = self._campaign.getName(
                )+":"+self._nextLevelName
                bs.writeConfig()
                self._campaign.setSelectedLevel(self._nextLevelName)

        bs.gameTimer(1000, bs.WeakCall(self.requestUI))

        if (self._isComplete and self._victory and self._isMoreLevels
                and not bsUtils.gRunningKioskModeGame):
            bsUtils.Text(
                bs.Lstr(
                    value='${A}:\n',
                    subs=[('${A}', bs.Lstr(resource='levelUnlockedText'))])
                if self._newlyComplete else bs.Lstr(
                    value='${A}:\n',
                    subs=[('${A}', bs.Lstr(resource='nextLevelText'))]),
                transition='inRight', transitionDelay=5200,
                flash=self._newlyComplete, scale=0.54, hAlign='center',
                maxWidth=270, color=(0.5, 0.7, 0.5, 1),
                position=(270, -235)).autoRetain()
            bsUtils.Text(
                bs.Lstr(translate=('coopLevelNames', self._nextLevelName)),
                transition='inRight', transitionDelay=5200,
                flash=self._newlyComplete, scale=0.7, hAlign='center',
                maxWidth=205, color=(0.5, 0.7, 0.5, 1),
                position=(270, -255)).autoRetain()
            if self._newlyComplete:
                bs.gameTimer(5200, bs.Call(
                    bs.playSound, self._cashRegisterSound))
                bs.gameTimer(5200, bs.Call(bs.playSound, self._dingSound))

        offsX = -195
        if len(self._playerInfo) > 1:
            pstr = bs.Lstr(
                value='- ${A} -',
                subs=[('${A}', bs.Lstr(
                    resource='multiPlayerCountText',
                    subs=[('${COUNT}', str(len(self._playerInfo)))]))])
        else:
            pstr = bs.Lstr(
                value='- ${A} -',
                subs=[('${A}', bs.Lstr(resource='singlePlayerCountText'))])
        bsUtils.ZoomText(
            self._campaign.getLevel(self._level).getDisplayString(),
            maxWidth=800, flash=False, trail=False, color=(0.5, 1, 0.5, 1),
            hAlign='center', scale=0.4, position=(0, 292),
            jitter=1.0).autoRetain()
        bsUtils.Text(pstr,
                     maxWidth=300,
                     transition='fadeIn',
                     scale=0.7,
                     hAlign='center',
                     vAlign='center',
                     color=(0.5, 0.7, 0.5, 1),
                     position=(0, 230)).autoRetain()

        t = bsUtils.Text(
            bs.Lstr(
                resource='waitingForHostText',
                subs=[('${HOST}', bsInternal._getAccountDisplayString())]),
            maxWidth=300, transition='fadeIn', transitionDelay=8000, scale=0.85,
            hAlign='center', vAlign='center', color=(1, 1, 0, 1),
            position=(0, -230)).autoRetain()
        t.node.clientOnly = True

        if self._score is not None:
            bs.gameTimer(350, bs.Call(
                bs.playSound, self.scoreDisplaySoundSmall))

        # vestigial remain.. this stuff should just be instance vars
        self._showInfo = {}

        if self._score is not None:
            bs.gameTimer(800, bs.WeakCall(self._showScoreVal, offsX))
        else:
            bs.gameTimer(1, bs.WeakCall(self._showFail))

        self._nameStr = nameStr = u', '.join(
            [p['name'] for p in self._playerInfo])

        if self._showFriendScores:
            self._friendsLoadingStatus = bsUtils.Text(
                bs.Lstr(
                    value='${A}...',
                    subs=[('${A}', bs.Lstr(resource='loadingText'))]),
                position=(-405, 150 + 30),
                color=(1, 1, 1, 0.4),
                transition='fadeIn', scale=0.7, transitionDelay=2000)
        self._scoreLoadingStatus = bsUtils.Text(
            bs.Lstr(
                value='${A}...',
                subs=[('${A}', bs.Lstr(resource='loadingText'))]),
            position=(280, 150 + 30),
            color=(1, 1, 1, 0.4),
            transition='fadeIn', scale=0.7, transitionDelay=2000)

        if self._score is not None:
            bs.gameTimer(400, bs.WeakCall(self._playDrumRoll))

        # add us to high scores, filter, and store
        ourHighScoresAll = self._campaign.getLevel(self._level).getHighScores()
        try:
            ourHighScores = ourHighScoresAll[unicode(
                len(self._playerInfo))+u" Player"]
        except Exception:
            ourHighScores = ourHighScoresAll[unicode(
                len(self._playerInfo))+u" Player"] = []

        if self._score is not None:
            ourScore = [self._score, {'players': self._playerInfo}]
            ourHighScores.append(ourScore)
        else:
            ourScore = None

        try:
            ourHighScores.sort(
                reverse=True if self._scoreOrder == 'increasing' else False)
        except Exception:
            bs.printException('Error sorting scores')
            print 'ourHighScores:', ourHighScores

        del ourHighScores[10:]

        if self._score is not None:
            bsInternal._addTransaction({
                'type': 'SET_LEVEL_LOCAL_HIGH_SCORES',
                'campaign': self._campaign.getName(),
                'level': self._level,
                'scoreVersion': self._campaign.getLevel(
                    self._level).getScoreVersionString(),
                'scores': ourHighScoresAll})

        if bsInternal._getAccountState() != 'SIGNED_IN':
            # we expect this only in kiosk mode; complain otherwise..
            if not bsUtils.gRunningKioskModeGame:
                print 'got not-signed-in at score-submit; unexpected'
            if self._showFriendScores:
                bs.pushCall(bs.WeakCall(self._gotFriendScoreResults, None))
            bs.pushCall(bs.WeakCall(self._gotScoreResults, None))
        else:
            bsInternal._submitScore(
                self._gameNameStr, self._gameConfigStr, nameStr, self._score,
                bs.WeakCall(self._gotScoreResults),
                bs.WeakCall(self._gotFriendScoreResults)
                if self._showFriendScores else None, order=self._scoreOrder,
                tournamentID=self.getSession()._tournamentID,
                scoreType=self._scoreType, campaign=self._campaign.getName()
                if self._campaign is not None else None, level=self._level)

        # apply the transactions we've been adding locally..
        bsInternal._runTransactions()

        # if we're not doing the world's-best button, just show a title instead
        tsHeight = 300
        tsHOffs = 210
        vOffs = 40
        t = bsUtils.Text(
            bs.Lstr(resource='tournamentStandingsText')
            if self.getSession()._tournamentID is not None else bs.Lstr(
                resource='worldsBestScoresText')
            if self._scoreType == 'points' else bs.Lstr(
                resource='worldsBestTimesText'), maxWidth=210,
            position=(tsHOffs - 10, tsHeight / 2 + 25 + vOffs + 20),
            transition='inLeft', vAlign='center', scale=1.2,
            transitionDelay=2200).autoRetain()

        # if we've got a button on the server, only show this on clients..
        if self._shouldShowWorldsBestButton():
            t.node.clientOnly = True

        # if we have no friend scores, display local best scores
        if self._showFriendScores:
            # host has a button, so we need client-only text
            tsHeight = 300
            tsHOffs = -480
            vOffs = 40
            t = bsUtils.Text(bs.Lstr(resource='topFriendsText'),
                             maxWidth=210,
                             position=(tsHOffs-10, tsHeight/2+25+vOffs+20),
                             transition='inRight',
                             vAlign='center',
                             scale=1.2,
                             transitionDelay=1800).autoRetain()
            t.node.clientOnly = True
        else:

            tsHeight = 300
            tsHOffs = -480
            vOffs = 40
            t = bsUtils.Text(
                bs.Lstr(resource='yourBestScoresText')
                if self._scoreType == 'points' else bs.Lstr(
                    resource='yourBestTimesText'), maxWidth=210,
                position=(tsHOffs - 10, tsHeight / 2 + 25 + vOffs + 20),
                transition='inRight', vAlign='center', scale=1.2,
                transitionDelay=1800).autoRetain()

            displayScores = list(ourHighScores)

            displayCount = 5

            while len(displayScores) < displayCount:
                displayScores.append((0, None))

            showedOurs = False

            hOffsExtra = 85 if self._scoreType == 'points' else 130
            vOffsExtra = 20
            vOffsNames = 0
            scale = 1.0
            pCount = len(self._playerInfo)

            hOffsExtra -= 75
            if pCount > 1:
                hOffsExtra -= 20
            if pCount == 2:
                scale = 0.9
            elif pCount == 3:
                scale = 0.65
            elif pCount == 4:
                scale = 0.5

            times = []

            for i in range(displayCount):
                times.insert(
                    random.randrange(0, len(times) + 1),
                    (1900 + i * 50, 2300 + i * 50))

            for i in range(displayCount):
                score = displayScores[i][0]
                try:
                    nameStr = ', '.join([p['name']
                                         for p in displayScores[i][1]
                                         ['players']])
                except Exception:
                    nameStr = '-'
                if displayScores[i] == ourScore and not showedOurs:
                    flash = True
                    color0 = (0.6, 0.4, 0.1, 1.0)
                    color1 = (0.6, 0.6, 0.6, 1.0)
                    tDelay1 = 3700
                    tDelay2 = 3700
                    showedOurs = True
                else:
                    flash = False
                    color0 = (0.6, 0.4, 0.1, 1.0)
                    color1 = (0.6, 0.6, 0.6, 1.0)
                    tDelay1 = times[i][0]
                    tDelay2 = times[i][1]
                bsUtils.Text(
                    str(displayScores[i][0])
                    if self._scoreType == 'points' else bsUtils.getTimeString(
                        displayScores[i][0] * 10),
                    position=(tsHOffs + 20 + hOffsExtra,
                              vOffsExtra + tsHeight / 2
                              + -tsHeight * (i + 1) / 10 + vOffs + 11.0),
                    hAlign='right', vAlign='center', color=color0, flash=flash,
                    transition='inRight', transitionDelay=tDelay1).autoRetain()

                bsUtils.Text(bs.Lstr(value=nameStr),
                             position=(tsHOffs + 35 + hOffsExtra, vOffsExtra +
                                       tsHeight / 2 + -tsHeight * (i + 1) / 10 +
                                       vOffsNames + vOffs + 11.0),
                             maxWidth=80.0 + 100.0 * len(self._playerInfo),
                             vAlign='center', color=color1, flash=flash,
                             scale=scale, transition='inRight',
                             transitionDelay=tDelay2).autoRetain()

        # show achievements for this level
        tsHeight = -150
        tsHOffs = -480
        vOffs = 40

        # only make this if we dont have the button
        # (never want clients to see it so no need for client-only version, etc)
        if self._haveAchievements:
            if not self._accountHasAchievements:
                t = bsUtils.Text(bs.Lstr(resource='achievementsText'),
                                 position=(tsHOffs-10, tsHeight/2+25+vOffs+3),
                                 maxWidth=210,
                                 hostOnly=True,
                                 transition='inRight',
                                 vAlign='center',
                                 scale=1.2,
                                 transitionDelay=2800).autoRetain()

            achievements = bsAchievement.getAchievementsForCoopLevel(
                self._gameNameStr)
            h = -455
            v = -100
            tDelay = 0
            for a in achievements:
                a.createDisplay(h, v+vOffs, 3000+tDelay)
                v -= 55
                tDelay += 250

        bs.gameTimer(5000, bs.WeakCall(self._showTips))

    def _playDrumRoll(self):
        bs.NodeActor(bs.newNode('sound',
                                attrs={'sound': self.drumRollSound,
                                       'positional': False,
                                       'loop': False})).autoRetain()

    def _gotFriendScoreResults(self, results):

        # delay a bit if results come in too fast
        baseDelay = max(0, 1900-(bs.getGameTime()-self._beginTime))

        tsHeight = 300
        tsHOffs = -550
        vOffs = 30

        # report in case of error
        if results is None:
            self._friendsLoadingStatus = bsUtils.Text(
                bs.Lstr(resource='friendScoresUnavailableText'),
                maxWidth=330, position=(-475, 150 + vOffs),
                color=(1, 1, 1, 0.4),
                transition='fadeIn', transitionDelay=baseDelay + 800, scale=0.7)
            return

        self._friendsLoadingStatus = None

        # ok, it looks like we aren't able to reliably get a just-submitted
        # result returned in the score list, so we need to look for our score
        # in this list and replace it if ours is better or add ours otherwise.
        if self._score is not None:
            ourScoreEntry = [self._score, 'Me', True]
            for score in results:
                if score[2]:
                    if self._scoreOrder == 'increasing':
                        ourScoreEntry[0] = max(score[0], self._score)
                    else:
                        ourScoreEntry[0] = min(score[0], self._score)
                    results.remove(score)
                    break
            results.append(ourScoreEntry)
            results.sort(reverse=True if self._scoreOrder ==
                         'increasing' else False)
        # if we're not submitting our own score, we still want to change the
        # name of our own score to 'Me'
        else:
            for score in results:
                if score[2]:
                    score[1] = 'Me'
                    break

        hOffsExtra = 80 if self._scoreType == 'points' else 130
        vOffsExtra = 20
        vOffsNames = 0
        scale = 1.0

        # make sure there's at least 5..
        while len(results) < 5:
            results.append([0, '-', False])
        results = results[:5]

        times = []

        for i in range(len(results)):
            times.insert(random.randrange(0, len(times)+1),
                         (baseDelay+i*50, baseDelay+300+i*50))

        for i, t in enumerate(results):
            score = int(t[0])
            nameStr = t[1]
            isMe = t[2]
            # if self._showInfo['results']['rank'] == i+1:
            if isMe and score == self._score:
                flash = True
                color0 = (0.6, 0.4, 0.1, 1.0)
                color1 = (0.6, 0.6, 0.6, 1.0)
                tDelay1 = baseDelay+1000
                tDelay2 = baseDelay+1000
            else:
                flash = False
                if isMe:
                    color0 = (0.6, 0.4, 0.1, 1.0)
                    color1 = (0.9, 1.0, 0.9, 1.0)
                else:
                    color0 = (0.6, 0.4, 0.1, 1.0)
                    color1 = (0.6, 0.6, 0.6, 1.0)
                tDelay1 = times[i][0]
                tDelay2 = times[i][1]
            if nameStr != '-':
                bsUtils.Text(
                    str(score)
                    if self._scoreType == 'points' else bsUtils.getTimeString(
                            score * 10),
                    position=(tsHOffs + 20 + hOffsExtra, vOffsExtra +
                              tsHeight / 2 + -tsHeight * (i + 1) / 10 +
                              vOffs + 11.0),
                    hAlign='right', vAlign='center', color=color0,
                    flash=flash, transition='inRight',
                    transitionDelay=tDelay1).autoRetain()
            else:
                if isMe:
                    print 'Error: got empty nameStr on score result:', t

            bsUtils.Text(bs.Lstr(value=nameStr),
                         position=(tsHOffs + 35 + hOffsExtra, vOffsExtra +
                                   tsHeight / 2 + -tsHeight * (i + 1) / 10 +
                                   vOffsNames + vOffs + 11.0),
                         color=color1, maxWidth=160.0, vAlign='center',
                         flash=flash, scale=scale, transition='inRight',
                         transitionDelay=tDelay2).autoRetain()

    def _gotScoreResults(self, results):
        # we need to manually run this in the context of our activity
        # and only if we aren't shutting down.
        # (really should make the submitScore call handle that stuff itself)
        if self.isFinalized():
            return
        with bs.Context(self):

            # delay a bit if results come in too fast
            baseDelay = max(0, 2700-(bs.getGameTime()-self._beginTime))

            vOffs = 20

            if results is None:
                self._scoreLoadingStatus = bsUtils.Text(
                    bs.Lstr(resource='worldScoresUnavailableText'),
                    position=(230, 150 + vOffs),
                    color=(1, 1, 1, 0.4),
                    transition='fadeIn', transitionDelay=baseDelay + 300,
                    scale=0.7)
            else:
                self._scoreLink = results['link']
                if not self._scoreLink.startswith('http://'):
                    self._scoreLink = \
                        bsInternal._get_master_server_address()+"/"+self._scoreLink
                self._scoreLoadingStatus = None
                if 'tournamentSecondsRemaining' in results:
                    self._tournamentTimeRemaining = \
                        results['tournamentSecondsRemaining']
                    self._tournamentTimeRemainingTextTimer = bs.Timer(
                        1000, bs.WeakCall(
                            self._updateTournamentTimeRemainingText),
                        repeat=True, timeType='net')

            self._showInfo['results'] = results
            if results is not None:
                if results['tops'] != '':
                    self._showInfo['tops'] = results['tops']
                else:
                    self._showInfo['tops'] = []

            offsX = -195
            available = (self._showInfo['results'] is not None)

            if self._score is not None:
                bs.netTimer(1500+baseDelay,
                            bs.WeakCall(self._showWorldRank, offsX))

            tsHOffs = 200
            tsHeight = 300

            # show world tops
            if available:

                # show the number of games represented by this
                # list (except for in tournaments)
                if self.getSession()._tournamentID is None:
                    bsUtils.Text(
                        bs.Lstr(
                            resource='lastGamesText',
                            subs=[('${COUNT}',
                                   str(self._showInfo['results']['total']))]),
                        position=(tsHOffs - 35 + 95, tsHeight / 2 + 6 + vOffs),
                        color=(0.4, 0.4, 0.4, 1.0),
                        scale=0.7, transition='inRight',
                        transitionDelay=baseDelay + 300).autoRetain()
                else:
                    vOffs += 20

                hOffsExtra = 0
                vOffsNames = 0
                scale = 1.0
                pCount = len(self._playerInfo)
                if pCount > 1:
                    hOffsExtra -= 40
                if self._scoreType != 'points':
                    hOffsExtra += 60
                if pCount == 2:
                    scale = 0.9
                elif pCount == 3:
                    scale = 0.65
                elif pCount == 4:
                    scale = 0.5

                # make sure there's at least 10..
                while len(self._showInfo['tops']) < 10:
                    self._showInfo['tops'].append([0, '-'])

                times = []

                for i in range(len(self._showInfo['tops'])):
                    times.insert(random.randrange(0, len(times)+1),
                                 (baseDelay+i*50, baseDelay+400+i*50))

                for i, t in enumerate(self._showInfo['tops']):
                    score = int(t[0])
                    nameStr = t[1]

                    if self._nameStr == nameStr and self._score == score:
                        flash = True
                        color0 = (0.6, 0.4, 0.1, 1.0)
                        color1 = (0.6, 0.6, 0.6, 1.0)
                        tDelay1 = baseDelay+1000
                        tDelay2 = baseDelay+1000
                    else:
                        flash = False
                        if self._nameStr == nameStr:
                            color0 = (0.6, 0.4, 0.1, 1.0)
                            color1 = (0.9, 1.0, 0.9, 1.0)
                        else:
                            color0 = (0.6, 0.4, 0.1, 1.0)
                            color1 = (0.6, 0.6, 0.6, 1.0)
                        tDelay1 = times[i][0]
                        tDelay2 = times[i][1]

                    if nameStr != '-':
                        bsUtils.Text(
                            str(score) if self._scoreType == 'points'
                            else bsUtils.getTimeString(score * 10),
                            position=(tsHOffs + 20 + hOffsExtra,
                                      tsHeight / 2 + -tsHeight * (i + 1) / 10
                                      + vOffs + 11.0),
                            hAlign='right', vAlign='center', color=color0,
                            flash=flash, transition='inLeft',
                            transitionDelay=tDelay1).autoRetain()
                    bsUtils.Text(
                        bs.Lstr(value=nameStr),
                        position=(tsHOffs + 35 + hOffsExtra, tsHeight / 2
                                  + -tsHeight * (i + 1) / 10 + vOffsNames +
                                  vOffs + 11.0),
                        maxWidth=80.0 + 100.0 * len(self._playerInfo),
                        vAlign='center', color=color1, flash=flash,
                        scale=scale, transition='inLeft',
                        transitionDelay=tDelay2).autoRetain()

    def _showTips(self):
        bsUtils.TipsText(offsY=30).autoRetain()

    def _updateTournamentTimeRemainingText(self):
        if self._tournamentTimeRemaining is None:
            return
        self._tournamentTimeRemaining = max(
            0, self._tournamentTimeRemaining - 1)
        if self._tournamentTimeRemainingText is not None:
            val = bsUtils.getTimeString(
                self._tournamentTimeRemaining*1000, centi=False)
            self._tournamentTimeRemainingText.node.text = val

    def _showWorldRank(self, offsX):
        available = (self._showInfo['results'] is not None)
        if available:
            error = (self._showInfo['results']['error']
                     if 'error' in self._showInfo['results'] else None)
            rank = self._showInfo['results']['rank']
            total = self._showInfo['results']['total']
            rating = 10.0 if total == 1 else round(
                10.0 * (1.0 - (float(rank-1)/(total-1))), 1)
            playerRank = self._showInfo['results']['playerRank']
            bestPlayerRank = self._showInfo['results']['bestPlayerRank']
        else:
            error = False
            rating = None
            playerRank = None
            bestPlayerRank = None

        # if we've got tournament-seconds-remaining, show it..
        if self._tournamentTimeRemaining is not None:
            bsUtils.Text(bs.Lstr(resource='coopSelectWindow.timeRemainingText'),
                         position=(-360, -70-100),
                         color=(1, 1, 1, 0.7),
                         hAlign='center',
                         vAlign='center',
                         transition='fadeIn',
                         scale=0.8,
                         maxWidth=300,
                         transitionDelay=2000).autoRetain()
            self._tournamentTimeRemainingText = bsUtils.Text(
                '', position=(-360, -110 - 100),
                color=(1, 1, 1, 0.7),
                hAlign='center', vAlign='center', transition='fadeIn',
                scale=1.6, maxWidth=150, transitionDelay=2000)

        # if we're a tournament, show prizes..
        try:
            tournamentID = self.getSession()._tournamentID
            if tournamentID is not None:
                if tournamentID in bsUI.gTournamentInfo:
                    tourneyInfo = bsUI.gTournamentInfo[tournamentID]
                    pr1, pv1, pr2, pv2, pr3, pv3 = bsUI._getPrizeStrings(
                        tourneyInfo)
                    bsUtils.Text(bs.Lstr(
                        resource='coopSelectWindow.prizesText'),
                        position=(-360, -70 + 77),
                        color=(1, 1, 1, 0.7),
                        hAlign='center', vAlign='center',
                        transition='fadeIn', scale=1.0, maxWidth=300,
                        transitionDelay=2000).autoRetain()
                    vv = -107+70
                    for rng, val in ((pr1, pv1), (pr2, pv2), (pr3, pv3)):
                        bsUtils.Text(
                            rng, position=(-410 + 10, vv),
                            color=(1, 1, 1, 0.7),
                            hAlign='right', vAlign='center',
                            transition='fadeIn', scale=0.6, maxWidth=300,
                            transitionDelay=2000).autoRetain()
                        bsUtils.Text(
                            val,
                            position=(-390+10, vv),
                            color=(0.7, 0.7, 0.7, 1.0),
                            hAlign='left', vAlign='center',
                            transition='fadeIn', scale=0.8,
                            maxWidth=300, transitionDelay=2000).autoRetain()
                        vv -= 35
        except Exception:
            bs.printException("error showing prize ranges")

        if self._doNewRating:
            if error:
                bsUtils.ZoomText(bs.Lstr(resource='failText'),
                                 flash=True, trail=True,
                                 scale=1.0 if available else 0.333,
                                 tiltTranslate=0.11,
                                 hAlign='center',
                                 position=(190+offsX, -60),
                                 maxWidth=200,
                                 jitter=1.0).autoRetain()
                bsUtils.Text(bs.Lstr(translate=('serverResponses', error)),
                             position=(0, -140),
                             color=(1, 1, 1, 0.7),
                             hAlign='center',
                             vAlign='center',
                             transition='fadeIn',
                             scale=0.9,
                             maxWidth=400,
                             transitionDelay=1000).autoRetain()
            else:
                bsUtils.ZoomText(
                    (('#' + str(playerRank))
                     if playerRank is not None else bs.Lstr(
                         resource='unavailableText')),
                    flash=True, trail=True, scale=1.0 if available else 0.333,
                    tiltTranslate=0.11, hAlign='center',
                    position=(190 + offsX, -60),
                    maxWidth=200, jitter=1.0).autoRetain()

                bsUtils.Text(
                    bs.Lstr(
                        value='${A}:',
                        subs=[('${A}', bs.Lstr(resource='rankText'))]),
                    position=(0, 36),
                    maxWidth=300, transition='fadeIn', hAlign='center',
                    vAlign='center', transitionDelay=0).autoRetain()
                if bestPlayerRank is not None:
                    bsUtils.Text(
                        bs.Lstr(
                            resource='currentStandingText',
                            fallbackResource='bestRankText',
                            subs=[('${RANK}', str(bestPlayerRank))]),
                        position=(0, -155),
                        color=(1, 1, 1, 0.7),
                        hAlign='center', transition='fadeIn', scale=0.7,
                        transitionDelay=1000).autoRetain()
        else:
            bsUtils.ZoomText(
                (str(rating)
                 if available else bs.Lstr(resource='unavailableText')),
                flash=True, trail=True, scale=0.6 if available else 0.333,
                tiltTranslate=0.11, hAlign='center',
                position=(190 + offsX, -94),
                maxWidth=200, jitter=1.0).autoRetain()

            if available:
                if rating >= 9.5:
                    stars = 3
                elif rating >= 7.5:
                    stars = 2
                elif rating > 0.0:
                    stars = 1
                else:
                    stars = 0
                starTex = bs.getTexture('star')
                starX = 135+offsX
                for i in range(stars):
                    img = bs.NodeActor(bs.newNode('image', attrs={
                        'texture': starTex,
                        'position': (starX, -16),
                        'scale': (62, 62),
                        'opacity': 1.0,
                        'color': (2.2, 1.2, 0.3),
                        'absoluteScale': True})).autoRetain()

                    bsUtils.animate(img.node, 'opacity', {150: 0, 400: 1})
                    starX += 60
                for i in range(3-stars):
                    img = bs.NodeActor(bs.newNode('image', attrs={
                        'texture': starTex,
                        'position': (starX, -16),
                        'scale': (62, 62),
                        'opacity': 1.0,
                        'color': (0.3, 0.3, 0.3),
                        'absoluteScale': True})).autoRetain()

                    bsUtils.animate(img.node, 'opacity', {150: 0, 400: 1})
                    starX += 60

                def foo(count, x, offsY, score):
                    bsUtils.Text(
                        score + ' =', position=(x, -64 + offsY),
                        color=(0.6, 0.6, 0.6, 0.6),
                        hAlign='center', vAlign='center', transition='fadeIn',
                        scale=0.4, transitionDelay=1000).autoRetain()
                    stx = x + 20
                    for i in range(count):
                        img = bs.NodeActor(bs.newNode('image', attrs={
                            'texture': starTex,
                            'position': (stx, -64+offsY),
                            'scale': (12, 12),
                            'opacity': 0.7,
                            'color': (2.2, 1.2, 0.3),
                            'absoluteScale': True})).autoRetain()

                        bsUtils.animate(img.node, 'opacity',
                                        {1000: 0, 1500: 0.5})
                        stx += 13.0

                foo(1, -44-30, -112, '0.0')
                foo(2, 10-30, -112, '7.5')
                foo(3, 77-30, -112, '9.5')

            try:
                bestRank = self._campaign.getLevel(self._level).getRating()
            except Exception:
                bestRank = 0.0

            if available:
                bsUtils.Text(
                    bs.Lstr(
                        resource='outOfText',
                        subs=[('${RANK}',
                               str(int(self._showInfo['results']['rank']))),
                              ('${ALL}',
                               str(self._showInfo['results']['total']))]),
                    position=(0, -155 if self._newlyComplete else -145),
                    color=(1, 1, 1, 0.7),
                    hAlign='center', transition='fadeIn', scale=0.55,
                    transitionDelay=1000).autoRetain()

            newBest = (bestRank > self._oldBestRank and bestRank > 0.0)
            wasString = ('' if self._oldBestRank is None
                         else bs.Lstr(value=' ${A}', subs=[
                                 ('${A}', bs.Lstr(resource='scoreWasText')),
                                 ('${COUNT}', str(self._oldBestRank))]))
            if not self._newlyComplete:
                bsUtils.Text(bs.Lstr(
                    value='${A}${B}',
                    subs=[('${A}', bs.Lstr(
                        resource='newPersonalBestText')),
                        ('${B}', wasString)])
                    if newBest else bs.Lstr(
                    resource='bestRatingText',
                    subs=[('${RATING}', str(bestRank))]),
                    position=(0, -165),
                    color=(1, 1, 1, 0.7),
                    flash=newBest, hAlign='center',
                    transition='inRight' if newBest else 'fadeIn',
                    scale=0.5, transitionDelay=1000).autoRetain()

            bsUtils.Text(
                bs.Lstr(
                    value='${A}:',
                    subs=[('${A}', bs.Lstr(resource='ratingText'))]),
                position=(0, 36),
                maxWidth=300, transition='fadeIn', hAlign='center',
                vAlign='center', transitionDelay=0).autoRetain()

        bs.gameTimer(350, bs.Call(bs.playSound, self.scoreDisplaySound))
        if not error:
            bs.gameTimer(350, bs.Call(bs.playSound, self.cymbalSound))

    def _showFail(self):
        bsUtils.ZoomText(bs.Lstr(resource='failText'),
                         maxWidth=300,
                         flash=False, trail=True,
                         hAlign='center',
                         tiltTranslate=0.11,
                         position=(0, 40),
                         jitter=1.0).autoRetain()
        if self._failMessage is not None:
            bsUtils.Text(self._failMessage,
                         hAlign='center',
                         position=(0, -130),
                         maxWidth=300,
                         color=(1, 1, 1, 0.5),
                         transition='fadeIn',
                         transitionDelay=1000).autoRetain()
        bs.gameTimer(350, bs.Call(bs.playSound, self.scoreDisplaySound))

    def _showScoreVal(self, offsX):
        bsUtils.ZoomText(
            (str(self._score)
             if self._scoreType == 'points' else bsUtils.getTimeString(
                 self._score * 10)),
            maxWidth=300, flash=True, trail=True, scale=1.0
            if self._scoreType == 'points' else 0.6, hAlign='center',
            tiltTranslate=0.11, position=(190 + offsX, 115),
            jitter=1.0).autoRetain()
        bsUtils.Text(
            bs.Lstr(
                value='${A}:',
                subs=[('${A}', bs.Lstr(resource='finalScoreText'))])
            if self._scoreType == 'points' else bs.Lstr(
                value='${A}:',
                subs=[('${A}', bs.Lstr(resource='finalTimeText'))]),
            maxWidth=300, position=(0, 200),
            transition='fadeIn', hAlign='center', vAlign='center',
            transitionDelay=0).autoRetain()
        bs.gameTimer(350, bs.Call(bs.playSound, self.scoreDisplaySound))


class CoopGameActivity(bs.GameActivity):
    """
    category: Game Flow Classes

    Base class for cooperative-mode games.
    """

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.CoopSession) else False

    def onBegin(self):
        bs.GameActivity.onBegin(self)

        # show achievements remaining..
        if not bsUtils.gRunningKioskModeGame:
            bs.gameTimer(3800, bs.WeakCall(self._showRemainingAchievements))

        # ..and preload their images in case we get some
        bs.gameTimer(2000, bs.WeakCall(self._preloadAchievements))

        # ..also lets ask the server for a 'time-to-beat' value
        levelName = self._getCoopLevelName()
        configStr = (str(len(self.players))+"p"
                     +self.getSession()._campaign.getLevel(
                         self.settings['name']).getScoreVersionString()
                     .replace(' ', '_'))
        bsInternal._getScoresToBeat(levelName, configStr,
                                    bs.WeakCall(self._onGotScoresToBeat))

    def _onGotScoresToBeat(self, score):
        pass

    def _showStandardScoresToBeatUI(self, scores):
        displayType = self._getScoreType()
        if scores is not None:
            # sort by originating date so that the most recent is first
            scores.sort(reverse=True, key=lambda score: score['time'])
            # now make a display for the most recent challenge
            for score in scores:
                if score['type'] == 'scoreChallenge':
                    t = bs.NodeActor(bs.newNode('text', attrs={
                        'vAttach': 'top',
                        'hAttach': ('center' if displayType == 'time'
                                    else 'left'),
                        'hAlign': 'center' if displayType == 'time' else 'left',
                        'color': (0.7, 0.4, 1, 1),
                        'shadow': 0.5,
                        'flatness': 1.0,
                        'position': ((20, -70) if displayType == 'time'
                                     else (20, -130)),
                        'scale': 0.6,
                        'text': score['player']+':  '+(
                            bsUtils.getTimeString(int(score['value'])*10
                            ).evaluate() if displayType == 'time'
                            else str(score['value']))})).autoRetain()

                    bsUtils.animate(t.node, 'scale', {
                                    1000: 0.0, 1100: 0.7, 1200: 0.6})
                    break

    # FIXME: this is now redundant with bsGame.getScoreInfo(); need to kill this
    def _getScoreType(self):
        return 'points'

    def _getCoopLevelName(self):
        return self.getSession()._campaign.getName() + ":" + str(self.settings
                                                                 ['name'])

    def celebrate(self, duration):
        """
        Tells all existing player-controlled characters to celebrate; can
        be useful in co-op games when the good guys score or complete a wave.
        """
        for player in self.players:
            try:
                player.actor.node.handleMessage('celebrate', duration)
            except Exception:
                pass

    def _preloadAchievements(self):
        achievements = bsAchievement.getAchievementsForCoopLevel(
            self._getCoopLevelName())
        for a in achievements:
            a.getIconTexture(True)

    def _showRemainingAchievements(self):
        tsHeight = -450
        tsHOffs = 30
        vOffs = -200
        achievements = [
            a
            for a in bsAchievement.getAchievementsForCoopLevel(
                self._getCoopLevelName()) if not a.isComplete()]
        vr = bs.getEnvironment()['vrMode']
        if len(achievements) > 0:
            bsUtils.Text(
                bs.Lstr(resource='achievementsRemainingText'),
                hostOnly=True, position=(tsHOffs - 10 + 40, vOffs - 10),
                transition='fadeIn', scale=1.1, hAttach="left", vAttach="top",
                color=(1, 1, 1.2, 1) if vr else(0.8, 0.8, 1.0, 1.0),
                flatness=1.0 if vr else 0.6, shadow=1.0 if vr else 0.5,
                transitionDelay=0, transitionOutDelay=1300
                if self._isSlowMotion else 4000).autoRetain()
            h = 70
            v = -50
            tDelay = 0
            for a in achievements:
                tDelay += 50
                a.createDisplay(
                    h + 40, v + vOffs, 0 + tDelay, outDelay=1300
                    if self._isSlowMotion else 4000, style='inGame')
                v -= 55

    def spawnPlayerSpaz(self, player, position, angle=None):
        "Spawn and wire up a standard player spaz"

        spaz = bs.GameActivity.spawnPlayerSpaz(self, player, position, angle)

        # deaths are noteworthy in co-op games
        spaz.playBigDeathSound = True
        return spaz

    def _awardAchievement(self, achievement, sound=True):
        """
        Award an achievement; returns True if a banner will be shown;
        False otherwise
        """

        # cache these for efficiency
        if not hasattr(self, '_achievementsAwarded'):
            self._achievementsAwarded = set()

        if achievement in self._achievementsAwarded:
            return

        a = bsAchievement.getAchievement(achievement)

        # if we're in the easy campaign and this achievement is hard-mode-only,
        # ignore it
        try:
            if (a.isHardModeOnly()
                    and self.getSession()._campaign.getName() == 'Easy'):
                return
        except Exception:
            bs.printException()

        # if we havnt awarded this one, check to see if we've got it;
        # if not, set it through the game service *and* add a transaction for it
        if not a.isComplete():
            self._achievementsAwarded.add(achievement)

            # report new achievements to the game-service..
            bsInternal._reportAchievement(achievement)

            # and to our account..
            bsInternal._addTransaction({'type': 'ACHIEVEMENT',
                                        'name': achievement})

            # now bring up a celebration banner
            a.announceCompletion(sound=sound)

            # bsInternal._runTransactions()

    def fadeToRed(self):
        """
        Fades the screen to red; useful when the good guys have lost.
        """
        cExisting = bs.getSharedObject('globals').tint
        c = bs.newNode(
            "combine",
            attrs={'input0': cExisting[0],
                   'input1': cExisting[1],
                   'input2': cExisting[2],
                   'size': 3})
        bs.animate(c, 'input1', {0: cExisting[1], 2000: 0})
        bs.animate(c, 'input2', {0: cExisting[2], 2000: 0})
        c.connectAttr('output', bs.getSharedObject('globals'), 'tint')

    def setupLowLifeWarningSound(self):
        """
        Sets up the activity to play a beeping noise
        whenever any players are close to death.
        """

        self._lifeWarningBeep = None
        self._lifeWarningBeepTimer = bs.Timer(
            1000, bs.WeakCall(self._updateLifeWarning), repeat=True)

    def _updateLifeWarning(self):
        # beep continuously if anyone is close to death
        shouldBeep = False
        for player in self.players:
            if player.isAlive():
                # fixme - should abstract this instead of
                # reading hitPoints directly
                if getattr(player.actor, 'hitPoints', 999) < 200:
                    shouldBeep = True
                    break
        if shouldBeep and self._lifeWarningBeep is None:
            try:
                warnBeepsSound = self._warnBeepsSound
            except Exception:
                warnBeepsSound = self._warnBeepsSound = bs.getSound('warnBeeps')
            self._lifeWarningBeep = bs.NodeActor(bs.newNode(
                'sound', attrs={'sound': warnBeepsSound,
                                'positional': False, 'loop': True}))
        if self._lifeWarningBeep is not None and not shouldBeep:
            self._lifeWarningBeep = None


class CoopJoiningActivity(bsGame.JoiningActivity):
    def __init__(self, settings={}):
        bsGame.JoiningActivity.__init__(self, settings)

        session = bs.getSession()

        # lets show a list of scores-to-beat for 1 player at least..
        levelNameFull = session._campaign.getName(
        )+":"+session._campaignInfo['level']
        configStr = "1p" + session._campaign.getLevel(
            session._campaignInfo['level']).getScoreVersionString().replace(
            ' ', '_')
        bsInternal._getScoresToBeat(levelNameFull, configStr, bs.WeakCall(
            self._onGotScoresToBeat))

    def onTransitionIn(self):
        bsGame.JoiningActivity.onTransitionIn(self)

        bsUtils.Text(
            self.getSession()._campaign.getLevel(
                self.getSession()._campaignInfo['level']).getDisplayString(),
            scale=1.3, hAttach='center', hAlign='center', vAttach='top',
            transition='fadeIn', transitionDelay=400, color=(1, 1, 1, 0.6),
            position=(0, -95)).autoRetain()

        bsUtils.ControlsHelpOverlay(delay=1000).autoRetain()

    def _onGotScoresToBeat(self, scores):

        # sort by originating date so that the most recent is first
        if scores is not None:
            scores.sort(reverse=True, key=lambda score: score['time'])

        # we only show achievements and challenges for CoopGameActivities:
        if isinstance(self.getSession()._currentGameInstance, CoopGameActivity):

            scoreType = self.getSession()._currentGameInstance._getScoreType()

            if scores is not None:
                achievementChallenges = [
                    a for a in scores if a['type'] == 'achievementChallenge']
                scoreChallenges = [
                    a for a in scores if a['type'] == 'scoreChallenge']
            else:
                achievementChallenges = scoreChallenges = []

            delay = 1000
            vpos = -140
            spacing = 25
            delayInc = 100

            def _addT(text, hOffs=0, scale=1.0, color=(1, 1, 1, 0.46)):
                bsUtils.Text(text, scale=scale * 0.76, hAlign='left',
                             hAttach='left', vAttach='top', transition='fadeIn',
                             transitionDelay=delay, color=color,
                             position=(60 + hOffs, vpos)).autoRetain()

            if scoreChallenges:
                _addT(bs.Lstr(value='${A}:',
                              subs=[('${A}',
                                     bs.Lstr(resource='scoreChallengesText'))]),
                      scale=1.1)
                delay += delayInc
                vpos -= spacing
                for s in scoreChallenges:
                    _addT(str(s['value'] if scoreType == 'points'
                              else bsUtils.getTimeString(int(s['value'])*10
                              ).evaluate())+'  (1 player)',
                          hOffs=30,
                          color=(0.9, 0.7, 1.0, 0.8))
                    delay += delayInc
                    vpos -= 0.6*spacing
                    _addT(s['player'], hOffs=40,
                          color=(0.8, 1, 0.8, 0.6),
                          scale=0.8)
                    delay += delayInc
                    vpos -= 1.2*spacing
                vpos -= 0.5*spacing

            if achievementChallenges:
                _addT(
                    bs.Lstr(
                        value='${A}:',
                        subs=[('${A}', bs.Lstr(
                            resource='achievementChallengesText'))]),
                    scale=1.1)
                delay += delayInc
                vpos -= spacing
                for s in achievementChallenges:
                    _addT(str(s['value']), hOffs=30, color=(0.9, 0.7, 1.0, 0.8))
                    delay += delayInc
                    vpos -= 0.6*spacing
                    _addT(s['player'], hOffs=40, color=(
                        0.8, 1, 0.8, 0.6), scale=0.8)
                    delay += delayInc
                    vpos -= 1.2*spacing
                vpos -= 0.5*spacing

            # now list our remaining achievements for this level
            levelName = self.getSession()._campaign.getName(
            )+":"+self.getSession()._campaignInfo['level']
            tsHeight = -450
            tsHOffs = 60

            if not bsUtils.gRunningKioskModeGame:

                achievements = [
                    a
                    for a in bsAchievement.getAchievementsForCoopLevel(
                        levelName) if not a.isComplete()]
                haveAchievements = True if achievements else False
                achievements = [a for a in achievements if not a.isComplete()]

                vr = bs.getEnvironment()['vrMode']

                if haveAchievements:
                    bsUtils.Text(
                        bs.Lstr(resource='achievementsRemainingText'),
                        hostOnly=True, position=(tsHOffs - 10, vpos),
                        transition='fadeIn', scale=1.1 * 0.76, hAttach="left",
                        vAttach="top", color=(1, 1, 1.2, 1)
                        if vr else(0.8, 0.8, 1, 1), shadow=1.0, flatness=1.0
                        if vr else 0.6, transitionDelay=delay).autoRetain()
                    h = tsHOffs+50
                    vpos -= 35
                    for a in achievements:
                        delay += 50
                        a.createDisplay(h, vpos, delay, style='inGame')
                        vpos -= 55

                    if len(achievements) == 0:
                        bsUtils.Text(
                            bs.Lstr(resource='noAchievementsRemainingText'),
                            hostOnly=True, position=(tsHOffs + 15, vpos + 10),
                            transition='fadeIn', scale=0.7, hAttach="left",
                            vAttach="top", color=(1, 1, 1, 0.5),
                            transitionDelay=delay + 500).autoRetain()


class CoopSession(bs.Session):
    """
    category: Game Flow Classes

    A bs.Session which runs cooperative-mode games.
    These generally consist of 1-4 players against
    the computer and include functionality such as
    high score lists.
    """

    def __init__(self):
        """
        Instantiate a co-op mode session.
        """

        bsInternal._incrementAnalyticsCount('Co-op session start')

        # if they passed in explicit min/max, honor that..
        # otherwise defer to user overrides or defaults..
        if 'minPlayers' in bsUI.gCoopSessionArgs:
            minPlayers = bsUI.gCoopSessionArgs['minPlayers']
        else:
            minPlayers = 1
        if 'maxPlayers' in bsUI.gCoopSessionArgs:
            maxPlayers = bsUI.gCoopSessionArgs['maxPlayers']
        else:
            try:
                maxPlayers = bs.getConfig()['Coop Game Max Players']
            except Exception:
                # old pref value..
                try:
                    maxPlayers = bs.getConfig()['Challenge Game Max Players']
                except Exception:
                    maxPlayers = 4
        bs.Session.__init__(self, teamNames=gTeamNames, teamColors=gTeamColors,
                            useTeamColors=False, minPlayers=minPlayers,
                            maxPlayers=maxPlayers, allowMidActivityJoins=False)

        self._tournamentID = (bsUI.gCoopSessionArgs['tournamentID']
                              if 'tournamentID' in bsUI.gCoopSessionArgs
                              else None)

        # fixme; could be nice to pass this in as actual args..
        self._campaignInfo = {}
        self._campaignInfo['campaign'] = bsUI.gCoopSessionArgs['campaign']
        self._campaignInfo['level'] = bsUI.gCoopSessionArgs['level']

        self._campaign = getCampaign(self._campaignInfo['campaign'])

        self._ranTutorialActivity = False
        self._tutorialActivity = None
        self._customMenuUI = []

        # start our joining screen..
        self.setActivity(bs.newActivity(CoopJoiningActivity))

        self._nextGameInstance = None
        self._nextGameName = None
        self._updateOnDeckGameInstances()

    def _updateOnDeckGameInstances(self):

        # instantiates levels we might be running soon
        # so they have time to load..

        # build an instance for the current level...
        l = self._campaign.getLevel(self._campaignInfo['level'])
        gameType = l.getGameType()
        settings = l.getSettings()

        # make sure all settings the game expects are present..
        neededSettings = gameType.getSettings(type(self))
        for settingName, setting in neededSettings:
            if settingName not in settings:
                settings[settingName] = setting['default']

        self._currentGameInstance = bs.newActivity(gameType, settings)

        # find the next level and build an instance for it too...
        levels = self._campaign.getLevels()
        level = self._campaign.getLevel(self._campaignInfo['level'])

        if level.getIndex() < len(levels)-1:
            nextLevel = levels[level.getIndex()+1]
        else:
            nextLevel = None
        if nextLevel:
            gameType = nextLevel.getGameType()
            settings = nextLevel.getSettings()

            # make sure all settings the game expects are present..
            neededSettings = gameType.getSettings(type(self))
            for settingName, setting in neededSettings:
                if settingName not in settings:
                    settings[settingName] = setting['default']

            # we wanna be in the activity's context while taking it down..
            self._nextGameInstance = bs.newActivity(gameType, settings)
            self._nextGameName = nextLevel.getName()
        else:
            self._nextGameInstance = None
            self._nextGameName = None

        # if our current level is 'onslaught training', instantiate our tutorial
        # so its ready to go.. (if we havnt run it yet)
        if (self._campaignInfo['level'] == 'Onslaught Training'
            and self._tutorialActivity is None
                and not self._ranTutorialActivity):
            self._tutorialActivity = bs.newActivity(bsTutorial.TutorialActivity)

    def getCustomMenuEntries(self):
        return self._customMenuUI

    def onPlayerLeave(self, player):
        bs.Session.onPlayerLeave(self, player)

        # if all our players leave we wanna quit out of the session
        bs.gameTimer(2000, bs.WeakCall(self._endSessionIfEmpty))

    def _endSessionIfEmpty(self):

        activity = self.getActivity()

        if activity is None:
            return  # hmm what should we do in this case?...

        # if theres still players in the current activity, we're good..
        if len(activity.players) > 0:
            return

        # if there's *no* players left in the current activity but there *is*
        # in the session, restart the activity to pull them into the game
        # (or quit if they're just in the lobby)
        elif (activity is not None and len(activity.players) == 0
              and len(self.players) > 0):
            # special exception for tourney games; don't auto-restart these!
            if self._tournamentID is not None:
                self.end()
            else:
                # dont restart joining activities; this probably means theres
                # someone with a chooser up in that case
                if not activity._isJoiningActivity:
                    self.restart()

        # hmm; no players anywhere.. lets just end the session..
        else:
            self.end()  # end the session

    def _onTournamentRestartMenuPress(self, resumeCallback):
        activity = self.getActivity()
        if activity is not None and not activity.isFinalized():
            bsUI.TournamentEntryWindow(tournamentID=self._tournamentID,
                                       tournamentActivity=activity,
                                       onCloseCall=resumeCallback)

    def restart(self):
        """
        Restarts the current game activity.
        """
        # tell the current activity to end with a 'restart' outcome
        # we use 'force' so that we apply even if end has already been called
        # (but is in its delay period)

        # make an exception if there's no players left.. otherwise this
        # can override the default session end that occurs in that case
        if len(self.players) < 1:
            return
        # we may call this from the UI context so make sure we run
        # in the activity's context..
        activity = self.getActivity()
        if activity is not None and not activity.isFinalized():
            activity._canShowAdOnDeath = True
            with bs.Context(activity):
                activity.end(results={'outcome': 'restart'}, force=True)

    def onActivityEnd(self, activity, results):
        """
        Method override for co-op sessions;
        jumps between co-op games and score screens.
        """

        # if we're running a TeamGameActivity we'll have a TeamGameResults
        # as results... otherwise its an old CoopGameActivity so its giving
        # us a dict of random stuff..
        if isinstance(results, bs.TeamGameResults):
            outcome = 'defeat'  # this can't be 'beaten'
        else:
            try:
                outcome = results['outcome']
            except Exception:
                outcome = ''

        # if at any point we have no in-game players, quit out of the session
        # (this can happen if someone leaves in the tutorial for instance)
        activePlayers = [p for p in self.players if p.getTeam() is not None]
        if len(activePlayers) == 0:
            self.end()
            return

        # if we're in a between-round activity or a restart-activity,
        # hop into a round
        if (isinstance(activity, bsGame.JoiningActivity)
            or isinstance(activity, CoopScoreScreen)
                or isinstance(activity, bsGame.TransitionActivity)):

            if outcome == 'nextLevel':
                if self._nextGameInstance is None:
                    raise Exception()
                self._campaignInfo['level'] = self._nextGameName
                nextGame = self._nextGameInstance
            else:
                nextGame = self._currentGameInstance

            # special case: if we're coming from a joining-activity
            # and will be going into onslaught-training, show the
            # tutorial first..
            if (isinstance(activity, bsGame.JoiningActivity)
                and self._campaignInfo['level'] == 'Onslaught Training'
                    and not bsUtils.gRunningKioskModeGame):
                if self._tutorialActivity is None:
                    raise Exception(
                        "_tutorialActivity not ready when it should be")
                self.setActivity(self._tutorialActivity)
                self._tutorialActivity = None
                self._ranTutorialActivity = True
                self._customMenuUI = []

            # normal case; launch the next round
            else:

                # do a full reset on our score-set and point it at our new
                # activity
                self.scoreSet.reset()
                for p in self.players:
                    # skip players that are still choosing a team
                    if p.getTeam() is not None:
                        self.scoreSet.registerPlayer(p)
                self.scoreSet.setActivity(nextGame)

                # now flip the current activity
                self.setActivity(nextGame)

                if not bs.getEnvironment()['kioskMode']:
                    if self._tournamentID is not None:
                        self._customMenuUI = [
                            {'label': bs.Lstr(resource='restartText'),
                             'resumeOnCall': False, 'call': bs.WeakCall(
                                 self._onTournamentRestartMenuPress)}]
                    else:
                        self._customMenuUI = [
                            {'label': bs.Lstr(resource='restartText'),
                             'call': bs.WeakCall(self.restart)}]

        # if we were in a tutorial, just pop a transition to get to the
        # actual round
        elif isinstance(activity, bsTutorial.TutorialActivity):
            self.setActivity(bs.newActivity(bsGame.TransitionActivity))
        else:

            # generic team games..
            if isinstance(results, bs.TeamGameResults):
                playerInfo = results._playerInfo
                score = results._getTeamScore(results._getTeams()[0])
                failMessage = None
                scoreOrder = ('decreasing' if results._lowerIsBetter
                              else 'increasing')
                if results._scoreType in ('seconds', 'milliseconds', 'time'):
                    scoreType = 'time'
                    # results contains milliseconds; ScoreScreen wants
                    # centi-seconds; need to fix :-/
                    if score is not None:
                        score /= 10
                else:
                    if results._scoreType != 'points':
                        print "Unknown score type: '"+results._scoreType+"'"
                    scoreType = 'points'
            # old coop-specific games; should migrate away from these..
            else:
                playerInfo = (results['playerInfo']
                              if 'playerInfo' in results else None)
                score = results['score'] if 'score' in results else None
                failMessage = (results['failMessage']
                               if 'failMessage' in results else None)
                scoreOrder = (results['scoreOrder']
                              if 'scoreOrder' in results else 'increasing')
                scoreType = activity._getScoreType() if isinstance(
                    activity, CoopGameActivity) else None

            # looks like we were in a round - check the outcome and
            # go from there
            if outcome == 'restart':
                # this will pop up back in the same round
                self.setActivity(bs.newActivity(bsGame.TransitionActivity))
            else:
                self.setActivity(bs.newActivity(
                    CoopScoreScreen,
                    {'playerInfo': playerInfo, 'score': score,
                     'failMessage': failMessage,
                     'scoreOrder': scoreOrder,
                     'scoreType': scoreType,
                     'outcome': outcome,
                     'campaign': self._campaign,
                     'level': self._campaignInfo['level']}))

        # no matter what, get the next 2 levels ready to go..
        self._updateOnDeckGameInstances()

# fill out our campaigns (need to let other loading happen first though)


def fillOutCampaigns():

    import bsOnslaught
    import bsFootball
    import bsRunaround
    import bsTheLastStand
    import bsMeteorShower
    import bsRace
    import bsEasterEggHunt

    # FIXME - once translations catch up, we can convert these to use the
    # generic display-name '${GAME} Training' type stuff..
    c = Campaign('Easy')
    c.addLevel(
        bs.Level(
            'Onslaught Training', gameType=bsOnslaught.OnslaughtGame,
            settings={'preset': 'trainingEasy'},
            previewTexName='doomShroomPreview'))
    c.addLevel(
        bs.Level(
            'Rookie Onslaught', gameType=bsOnslaught.OnslaughtGame,
            settings={'preset': 'rookieEasy'},
            previewTexName='courtyardPreview'))
    c.addLevel(
        bs.Level(
            'Rookie Football', gameType=bsFootball.FootballCoopGame,
            settings={'preset': 'rookieEasy'},
            previewTexName='footballStadiumPreview'))
    c.addLevel(
        bs.Level(
            'Pro Onslaught', gameType=bsOnslaught.OnslaughtGame,
            settings={'preset': 'proEasy'},
            previewTexName='doomShroomPreview'))
    c.addLevel(
        bs.Level(
            'Pro Football', gameType=bsFootball.FootballCoopGame,
            settings={'preset': 'proEasy'},
            previewTexName='footballStadiumPreview'))
    c.addLevel(
        bs.Level(
            'Pro Runaround', gameType=bsRunaround.RunaroundGame,
            settings={'preset': 'proEasy'},
            previewTexName='towerDPreview'))
    c.addLevel(
        bs.Level(
            'Uber Onslaught', gameType=bsOnslaught.OnslaughtGame,
            settings={'preset': 'uberEasy'},
            previewTexName='courtyardPreview'))
    c.addLevel(
        bs.Level(
            'Uber Football', gameType=bsFootball.FootballCoopGame,
            settings={'preset': 'uberEasy'},
            previewTexName='footballStadiumPreview'))
    c.addLevel(
        bs.Level(
            'Uber Runaround', gameType=bsRunaround.RunaroundGame,
            settings={'preset': 'uberEasy'},
            previewTexName='towerDPreview'))
    _registerCampaign(c)

    c = Campaign('Default')
    c.addLevel(
        bs.Level(
            'Onslaught Training', gameType=bsOnslaught.OnslaughtGame,
            settings={'preset': 'training'},
            previewTexName='doomShroomPreview'))
    c.addLevel(
        bs.Level(
            'Rookie Onslaught', gameType=bsOnslaught.OnslaughtGame,
            settings={'preset': 'rookie'},
            previewTexName='courtyardPreview'))
    c.addLevel(
        bs.Level(
            'Rookie Football', gameType=bsFootball.FootballCoopGame,
            settings={'preset': 'rookie'},
            previewTexName='footballStadiumPreview'))
    c.addLevel(
        bs.Level(
            'Pro Onslaught', gameType=bsOnslaught.OnslaughtGame,
            settings={'preset': 'pro'},
            previewTexName='doomShroomPreview'))
    c.addLevel(
        bs.Level(
            'Pro Football', gameType=bsFootball.FootballCoopGame,
            settings={'preset': 'pro'},
            previewTexName='footballStadiumPreview'))
    c.addLevel(
        bs.Level(
            'Pro Runaround', gameType=bsRunaround.RunaroundGame,
            settings={'preset': 'pro'},
            previewTexName='towerDPreview'))
    c.addLevel(
        bs.Level(
            'Uber Onslaught', gameType=bsOnslaught.OnslaughtGame,
            settings={'preset': 'uber'},
            previewTexName='courtyardPreview'))
    c.addLevel(
        bs.Level(
            'Uber Football', gameType=bsFootball.FootballCoopGame,
            settings={'preset': 'uber'},
            previewTexName='footballStadiumPreview'))
    c.addLevel(
        bs.Level(
            'Uber Runaround', gameType=bsRunaround.RunaroundGame,
            settings={'preset': 'uber'},
            previewTexName='towerDPreview'))
    c.addLevel(
        bs.Level(
            'The Last Stand', gameType=bsTheLastStand.TheLastStandGame,
            settings={},
            previewTexName='rampagePreview'))
    _registerCampaign(c)

    # challenges are our 'official' random extra co-op levels
    c = Campaign('Challenges', sequential=False)
    c.addLevel(
        bs.Level(
            'Infinite Onslaught', gameType=bsOnslaught.OnslaughtGame,
            settings={'preset': 'endless'},
            previewTexName='doomShroomPreview'))
    c.addLevel(
        bs.Level(
            'Infinite Runaround', gameType=bsRunaround.RunaroundGame,
            settings={'preset': 'endless'},
            previewTexName='towerDPreview'))
    c.addLevel(
        bs.Level(
            'Race', displayName='${GAME}', gameType=bsRace.RaceGame,
            settings={'map': 'Big G', 'Laps': 3, 'Bomb Spawning': 0},
            previewTexName='bigGPreview'))
    c.addLevel(
        bs.Level(
            'Pro Race', displayName='Pro ${GAME}', gameType=bsRace.RaceGame,
            settings={'map': 'Big G', 'Laps': 3, 'Bomb Spawning': 1000},
            previewTexName='bigGPreview'))
    c.addLevel(
        bs.Level(
            'Lake Frigid Race', displayName='${GAME}', gameType=bsRace.RaceGame,
            settings={'map': 'Lake Frigid', 'Laps': 6, 'Mine Spawning': 2000,
                      'Bomb Spawning': 0},
            previewTexName='lakeFrigidPreview'))
    c.addLevel(
        bs.Level(
            'Football', displayName='${GAME}',
            gameType=bsFootball.FootballCoopGame,
            settings={'preset': 'tournament'},
            previewTexName='footballStadiumPreview'))
    c.addLevel(
        bs.Level(
            'Pro Football', displayName='Pro ${GAME}',
            gameType=bsFootball.FootballCoopGame,
            settings={'preset': 'tournamentPro'},
            previewTexName='footballStadiumPreview'))
    c.addLevel(
        bs.Level(
            'Runaround', displayName='${GAME}',
            gameType=bsRunaround.RunaroundGame,
            settings={'preset': 'tournament'},
            previewTexName='towerDPreview'))
    c.addLevel(
        bs.Level(
            'Uber Runaround', displayName='Uber ${GAME}',
            gameType=bsRunaround.RunaroundGame,
            settings={'preset': 'tournamentUber'},
            previewTexName='towerDPreview'))
    c.addLevel(
        bs.Level(
            'The Last Stand', displayName='${GAME}',
            gameType=bsTheLastStand.TheLastStandGame,
            settings={'preset': 'tournament'},
            previewTexName='rampagePreview'))
    c.addLevel(bs.Level(
        'Tournament Infinite Onslaught',
        displayName='Infinite Onslaught',
        gameType=bsOnslaught.OnslaughtGame,
        settings={'preset': 'endlessTournament'},
        previewTexName='doomShroomPreview'))
    c.addLevel(bs.Level(
        'Tournament Infinite Runaround',
        displayName='Infinite Runaround',
        gameType=bsRunaround.RunaroundGame,
        settings={'preset': 'endlessTournament'},
        previewTexName='towerDPreview'))

    # these modules get pulled into 'challenges' and ignored for 'user'
    internalModules = ['bsNinjaFight', 'bsMeteorShower',
                       'bsTargetPractice', 'bsEasterEggHunt']

    # add levels defined within our internal modules..
    allLevels = []
    modules = bsUtils._getModulesWithCall(
        'bsGetLevels', whiteList=internalModules)
    for module in modules:
        try:
            allLevels += module.bsGetLevels()
        except Exception:
            bs.printException("error fetching levels from module "+str(module))
    for level in allLevels:
        try:
            c.addLevel(level)
        except Exception:
            bs.printException("error adding level '"+str(level)+"'")
    _registerCampaign(c)

    # User is the 'wild west' where custom mods and whatnot live
    c = Campaign('User', sequential=False)
    # add any levels from other user-space modules..
    allLevels = []
    modules = bsUtils._getModulesWithCall(
        'bsGetLevels', blackList=internalModules)
    for module in modules:
        try:
            allLevels += module.bsGetLevels()
        except Exception:
            bs.printException("error fetching levels from module "+str(module))
    for level in allLevels:
        try:
            c.addLevel(level)
        except Exception:
            bs.printException("error adding level '"+str(level)+"'")
    _registerCampaign(c)


with bs.Context('UI'):
    bs.pushCall(fillOutCampaigns)
