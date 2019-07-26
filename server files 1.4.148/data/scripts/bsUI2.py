import bs
import bsUI
import time
import bsInternal
import copy
import bsUtils
import random


class UnlinkAccountsWindow(bsUI.Window):

    def __init__(self, transition='inRight', originWidget=None):
        if originWidget is not None:
            self._transitionOut = 'outScale'
            scaleOrigin = originWidget.getScreenSpaceCenter()
            transition = 'inScale'
        else:
            self._transitionOut = 'outRight'
            scaleOrigin = None
            transition = 'inRight'
        bgColor = (0.4, 0.4, 0.5)
        self._width = 540
        self._height = 350
        self._scrollWidth = 400
        self._scrollHeight = 200
        baseScale = 2.0 if bsUI.gSmallUI else 1.6 if bsUI.gMedUI else 1.1
        self._rootWidget = bs.containerWidget(
            size=(self._width, self._height),
            transition=transition, scale=baseScale,
            scaleOriginStackOffset=scaleOrigin, stackOffset=(0, -10)
            if bsUI.gSmallUI else(0, 0))
        self._cancelButton = bs.buttonWidget(
            parent=self._rootWidget, position=(30, self._height - 50),
            size=(50, 50),
            scale=0.7, label='', color=bgColor, onActivateCall=self._cancel,
            autoSelect=True, icon=bs.getTexture('crossOut'),
            iconScale=1.2)
        bs.textWidget(
            parent=self._rootWidget,
            position=(self._width * 0.5, self._height * 0.88),
            size=(0, 0),
            text=bs.Lstr(
                resource=\
                'accountSettingsWindow.unlinkAccountsInstructionsText'),
            maxWidth=self._width * 0.7, color=bsUI.gInfoTextColor,
            hAlign='center', vAlign='center')
        bs.containerWidget(edit=self._rootWidget,
                           cancelButton=self._cancelButton)

        self._scrollWidget = bs.scrollWidget(
            parent=self._rootWidget, highlight=False,
            position=((self._width - self._scrollWidth) * 0.5, self._height - 85
                      - self._scrollHeight),
            size=(self._scrollWidth, self._scrollHeight))
        bs.containerWidget(edit=self._scrollWidget, claimsLeftRight=True)
        self._columnWidget = bs.columnWidget(
            parent=self._scrollWidget, leftBorder=10)

        ourAccountID = bsInternal._get_public_login_id()
        if ourAccountID is None:
            entries = []
        else:
            accountInfos = bsInternal._getAccountMiscReadVal2(
                'linkedAccounts2', [])
            entries = [{'name': ai['d'], 'id':ai['id']}
                       for ai in accountInfos if ai['id'] != ourAccountID]

        # (avoid getting our selection stuck on an empty column widget)
        if len(entries) == 0:
            bs.containerWidget(edit=self._scrollWidget, selectable=False)
        for i, entry in enumerate(entries):
            t = bs.textWidget(
                parent=self._columnWidget, selectable=True, text=entry
                ['name'],
                size=(self._scrollWidth - 30, 30),
                autoSelect=True, clickActivate=True, onActivateCall=bs.Call(
                    self._onEntrySelected, entry))
            bs.widget(edit=t, leftWidget=self._cancelButton)
            if i == 0:
                bs.widget(edit=t, upWidget=self._cancelButton)

    def _onEntrySelected(self, entry):
        bs.screenMessage(bs.Lstr(
            resource='pleaseWaitText',
            fallbackResource='requestingText'),
            color=(0, 1, 0))
        bsInternal._addTransaction(
            {'type': 'ACCOUNT_UNLINK_REQUEST', 'accountID': entry['id'],
             'expireTime': time.time() + 5})
        bsInternal._runTransactions()
        bs.containerWidget(edit=self._rootWidget,
                           transition=self._transitionOut)

    def _cancel(self):
        bs.containerWidget(edit=self._rootWidget,
                           transition=self._transitionOut)


class LinkAccountsWindow(bsUI.Window):

    def __init__(self, transition='inRight', originWidget=None):
        if originWidget is not None:
            self._transitionOut = 'outScale'
            scaleOrigin = originWidget.getScreenSpaceCenter()
            transition = 'inScale'
        else:
            self._transitionOut = 'outRight'
            scaleOrigin = None
            transition = 'inRight'
        bgColor = (0.4, 0.4, 0.5)
        self._width = 560
        self._height = 420
        baseScale = 1.65 if bsUI.gSmallUI else 1.5 if bsUI.gMedUI else 1.1
        self._rootWidget = bs.containerWidget(
            size=(self._width, self._height),
            transition=transition, scale=baseScale,
            scaleOriginStackOffset=scaleOrigin, stackOffset=(0, -10)
            if bsUI.gSmallUI else(0, 0))
        self._cancelButton = bs.buttonWidget(
            parent=self._rootWidget, position=(40, self._height - 45),
            size=(50, 50),
            scale=0.7, label='', color=bgColor, onActivateCall=self._cancel,
            autoSelect=True, icon=bs.getTexture('crossOut'),
            iconScale=1.2)
        bs.textWidget(
            parent=self._rootWidget,
            position=(self._width * 0.5, self._height * 0.56),
            size=(0, 0),
            text=bs.Lstr(
                resource=\
                'accountSettingsWindow.linkAccountsInstructionsNewText',
                subs=[('${COUNT}',
                       str(
                           bsInternal._getAccountMiscReadVal(
                               'maxLinkAccounts', 5)))]),
            maxWidth=self._width * 0.9, color=bsUI.gInfoTextColor,
            maxHeight=self._height * 0.6, hAlign='center', vAlign='center')
        bs.containerWidget(edit=self._rootWidget,
                           cancelButton=self._cancelButton)
        bs.buttonWidget(
            parent=self._rootWidget, position=(40, 30),
            size=(200, 60),
            label=bs.Lstr(
                resource='accountSettingsWindow.linkAccountsGenerateCodeText'),
            autoSelect=True, onActivateCall=self._generatePress)
        self._enterCodeButton = bs.buttonWidget(
            parent=self._rootWidget, position=(self._width - 240, 30),
            size=(200, 60),
            label=bs.Lstr(
                resource='accountSettingsWindow.linkAccountsEnterCodeText'),
            autoSelect=True, onActivateCall=self._enterCodePress)

    def _generatePress(self):
        if bsInternal._getAccountState() != 'SIGNED_IN':
            bsUI.showSignInPrompt()
            return
        bs.screenMessage(
            bs.Lstr(resource='gatherWindow.requestingAPromoCodeText'),
            color=(0, 1, 0))
        bsInternal._addTransaction(
            {'type': 'ACCOUNT_LINK_CODE_REQUEST', 'expireTime': time.time()+5})
        bsInternal._runTransactions()

    def _enterCodePress(self):
        bsUI.PromoCodeWindow(modal=True, originWidget=self._enterCodeButton)
        bs.containerWidget(edit=self._rootWidget,
                           transition=self._transitionOut)

    def _cancel(self):
        bs.containerWidget(edit=self._rootWidget,
                           transition=self._transitionOut)


def _handleUIRemotePress():
    #dCount = bsInternal._getLocalActiveInputDevicesCount()
    env = bs.getEnvironment()
    if env['onTV'] and(
            env['platform'] == 'android' and env['subplatform'] == 'alibaba'):
        GetBSRemoteWindow()
    else:
        bs.screenMessage(
            bs.Lstr(resource="internal.controllerForMenusOnlyText"),
            color=(1, 0, 0))
        bs.playSound(bs.getSound('error'))


class GetBSRemoteWindow(bsUI.PopupWindow):

    def __init__(self):
        position = (0, 0)
        scale = 2.3 if bsUI.gSmallUI else 1.65 if bsUI.gMedUI else 1.23
        self._transitioningOut = False
        self._width = 570
        self._height = 350
        bgColor = (0.5, 0.4, 0.6)
        bsUI.PopupWindow.__init__(self, position=position, size=(
            self._width, self._height), scale=scale, bgColor=bgColor)
        env = bs.getEnvironment()
        self._cancelButton = bs.buttonWidget(
            parent=self._rootWidget, position=(50, self._height - 30),
            size=(50, 50),
            scale=0.5, label='', color=bgColor,
            onActivateCall=self._onCancelPress, autoSelect=True,
            icon=bs.getTexture('crossOut'),
            iconScale=1.2)
        bs.imageWidget(
            parent=self._rootWidget,
            position=(self._width * 0.5 - 110, self._height * 0.67 - 110),
            size=(220, 220),
            texture=bs.getTexture('multiplayerExamples'))
        bs.textWidget(
            parent=self._rootWidget, size=(0, 0),
            hAlign='center', vAlign='center', maxWidth=self._width * 0.9,
            position=(self._width * 0.5, 60),
            text=bs.Lstr(
                resource='remoteAppInfoShortText',
                subs=[('${APP_NAME}', bs.Lstr(resource='titleText')),
                      ('${REMOTE_APP_NAME}', bs.Lstr(
                          resource='remote_app.app_name'))]))

    def _onCancelPress(self):
        self._transitionOut()

    def _transitionOut(self):
        if not self._transitioningOut:
            self._transitioningOut = True
            bs.containerWidget(edit=self._rootWidget, transition='outScale')

    def onPopupCancel(self):
        bs.playSound(bs.getSound('swish'))
        self._transitionOut()


class ChallengeEntryWindow(bsUI.PopupWindow):

    def __init__(self, challengeID, challengeActivity=None,
                 position=(0, 0), delegate=None, scale=None, offset=(0, 0),
                 onCloseCall=None):

        self._challengeID = challengeID

        self._onCloseCall = onCloseCall
        if scale is None:
            scale = 2.3 if bsUI.gSmallUI else 1.65 if bsUI.gMedUI else 1.23
        self._delegate = delegate
        self._transitioningOut = False

        self._challengeActivity = challengeActivity

        self._width = 340
        self._height = 290

        self._canForfeit = False
        self._forfeitButton = None

        challenge = bsUI._getCachedChallenge(self._challengeID)
        # this stuff shouldn't change..
        if challenge is None:
            self._canForfeit = False
            self._prizeTickets = 0
            self._prizeTrophy = None
            self._level = 0
            self._waitTickets = 0
        else:
            self._canForfeit = challenge['canForfeit']
            self._prizeTrophy = challenge['prizeTrophy']
            self._prizeTickets = challenge['prizeTickets']
            self._level = challenge['level']
            t = time.time()
            self._waitTickets = max(
                1,
                int(
                    challenge['waitTickets'] *
                    (1.0 - (t - challenge['waitStart']) /
                     (challenge['waitEnd'] - challenge['waitStart']))))

        self._bgColor = (0.5, 0.4, 0.6)

        # creates our _rootWidget
        bsUI.PopupWindow.__init__(
            self, position=position, size=(self._width, self._height),
            scale=scale, bgColor=self._bgColor, offset=offset)
        self._state = None
        self._updateTimer = bs.Timer(
            1000, bs.WeakCall(self._update),
            repeat=True, timeType='real')
        self._update()

    def _rebuildForState(self, newState):

        if self._state is not None:
            self._save_state()

        # clear out previous state (if any)
        children = self._rootWidget.getChildren()
        for c in children:
            c.delete()

        self._state = newState

        # print 'REBUILDING FOR STATE',self._state
        self._cancelButton = bs.buttonWidget(
            parent=self._rootWidget, position=(20, self._height - 30),
            size=(50, 50),
            scale=0.5, label='', color=self._bgColor,
            onActivateCall=self._onCancel, autoSelect=True, icon=bs.getTexture(
                'crossOut'),
            iconScale=1.2)
        titleScale = 0.6
        titleColor = (1, 1, 1, 0.4)
        showPrizes = False
        showLevel = False
        showForfeitButton = False

        if self._state == 'error':
            titleStr = bs.Lstr(resource='coopSelectWindow.challengesText')
            bs.textWidget(
                parent=self._rootWidget,
                position=(self._width * 0.5, self._height * 0.5),
                size=(0, 0),
                hAlign='center', vAlign='center', scale=0.7, text=bs.Lstr(
                    resource='errorText'),
                maxWidth=self._width * 0.8)
        elif self._state == 'skipWaitNextChallenge':
            titleStr = bs.Lstr(resource='coopSelectWindow.nextChallengeText')
            bWidth = 140
            bHeight = 130
            imgWidth = 80
            imgHeight = 80
            bPos = (self._width*0.5, self._height*0.52)
            b = bs.buttonWidget(
                parent=self._rootWidget,
                position=(bPos[0] - bWidth * 0.5, bPos[1] - bHeight * 0.5),
                onActivateCall=bs.WeakCall(self._load),
                label='', size=(bWidth, bHeight),
                buttonType='square', autoSelect=True)
            bs.containerWidget(edit=self._rootWidget, selectedChild=b)
            bs.textWidget(
                parent=self._rootWidget, drawController=b, hAlign='center',
                vAlign='center', text=bs.Lstr(
                    resource='coopSelectWindow.skipWaitText'),
                size=(0, 0),
                maxWidth=bWidth * 0.8, color=(0.75, 1.0, 0.7),
                position=(bPos[0],
                          bPos[1] - bHeight * 0.0),
                scale=0.9)
            bs.textWidget(
                parent=self._rootWidget, drawController=b, hAlign='center',
                vAlign='center', text=bs.getSpecialChar('ticket') +
                str(self._waitTickets),
                size=(0, 0),
                scale=0.6, color=(1, 0.5, 0),
                position=(bPos[0],
                          bPos[1] - bHeight * 0.23))
        elif self._state == 'skipWaitNextPlay':
            showLevel = True
            showForfeitButton = True
            bWidth = 140
            bHeight = 130
            imgWidth = 80
            imgHeight = 80
            bPos = (self._width*0.5, self._height*0.52)
            b = bs.buttonWidget(
                parent=self._rootWidget,
                position=(bPos[0] - bWidth * 0.5, bPos[1] - bHeight * 0.5),
                onActivateCall=bs.WeakCall(self._play),
                label='', size=(bWidth, bHeight),
                buttonType='square', autoSelect=True)
            bs.widget(edit=b, upWidget=self._cancelButton)
            bs.containerWidget(edit=self._rootWidget, selectedChild=b)
            bs.textWidget(
                parent=self._rootWidget, drawController=b, hAlign='center',
                vAlign='center', text=bs.Lstr(
                    resource='coopSelectWindow.playNowText'),
                size=(0, 0),
                maxWidth=bWidth * 0.8, color=(0.75, 1.0, 0.7),
                position=(bPos[0],
                          bPos[1] - bHeight * 0.0),
                scale=0.9)
            bs.textWidget(
                parent=self._rootWidget, drawController=b, hAlign='center',
                vAlign='center', text=bs.getSpecialChar('ticket') +
                str(self._waitTickets),
                size=(0, 0),
                scale=0.6, color=(1, 0.5, 0),
                position=(bPos[0],
                          bPos[1] - bHeight * 0.23))
            showPrizes = True

        elif self._state == 'freePlay':
            showLevel = True
            showForfeitButton = True
            bWidth = 140
            bHeight = 130
            b = bs.buttonWidget(
                parent=self._rootWidget,
                position=(self._width * 0.5 - bWidth * 0.5, self._height * 0.52
                          - bHeight * 0.5),
                onActivateCall=bs.WeakCall(self._play),
                label=bs.Lstr(resource='playText'),
                size=(bWidth, bHeight),
                buttonType='square', autoSelect=True)
            bs.widget(edit=b, upWidget=self._cancelButton)
            bs.containerWidget(edit=self._rootWidget, selectedChild=b)
            showPrizes = True
        elif self._state == 'ended':
            titleStr = bs.Lstr(resource='coopSelectWindow.challengesText')
            bs.textWidget(
                parent=self._rootWidget,
                position=(self._width * 0.5, self._height * 0.5),
                size=(0, 0),
                hAlign='center', vAlign='center', scale=0.7, text=bs.Lstr(
                    resource='challengeEndedText'),
                maxWidth=self._width * 0.8)
        else:
            titleStr = ''
            print 'Unrecognized state for ChallengeEntryWindow:', self._state

        if showLevel:
            titleColor = (1, 1, 1, 0.7)
            titleStr = 'Meteor Shower Blah'
            titleScale = 0.7
            bs.textWidget(parent=self._rootWidget,
                          position=(self._width * 0.5, self._height * 0.86),
                          size=(0, 0),
                          hAlign='center', vAlign='center',
                          color=(0.8, 0.8, 0.4, 0.7),
                          flatness=1.0, scale=0.55, text=bs.Lstr(
                              resource='levelText',
                              subs=[('${NUMBER}', str(self._level))]),
                          maxWidth=self._width * 0.8)

        self._titleText = bs.textWidget(
            parent=self._rootWidget,
            position=(self._width * 0.5, self._height - 20),
            size=(0, 0),
            hAlign='center', vAlign='center', scale=titleScale, text=titleStr,
            maxWidth=200, color=titleColor)

        if showForfeitButton:
            bWidth = 40
            bHeight = 25
            self._forfeitButton = bs.buttonWidget(
                parent=self._rootWidget,
                position=(self._width - bWidth - 16,
                          self._height - bHeight - 10),
                label=bs.Lstr(resource='coopSelectWindow.forfeitText'),
                size=(bWidth, bHeight),
                buttonType='square', color=(0.6, 0.45, 0.6),
                onActivateCall=bs.WeakCall(self._onForfeitPress),
                textColor=(0.65, 0.55, 0.65),
                autoSelect=True)
        else:
            self._forfeitButton = None

        if showPrizes:
            bs.textWidget(
                parent=self._rootWidget,
                position=(self._width * 0.5, self._height * 0.24),
                size=(0, 0),
                hAlign='center', vAlign='center', flatness=1.0, scale=0.6,
                text=bs.Lstr(resource='coopSelectWindow.prizesText'),
                maxWidth=self._width * 0.8, color=(0.8, 0.8, 1, 0.5)),
            prizes = []
            if self._prizeTrophy is not None:
                prizes.append(bs.getSpecialChar(
                    'trophy'+str(self._prizeTrophy)))
            if self._prizeTickets != 0:
                prizes.append(
                    bs.getSpecialChar('ticketBacking') +
                    str(self._prizeTickets))
            bs.textWidget(
                parent=self._rootWidget,
                position=(self._width * 0.5, self._height * 0.13),
                size=(0, 0),
                hAlign='center', vAlign='center', scale=0.8, flatness=1.0,
                color=(0.7, 0.7, 0.7, 1),
                text='   '.join(prizes),
                maxWidth=self._width * 0.8)

        self._restore_state()

    def _load(self):
        self._transitionOut()
        bs.screenMessage(
            "WOULD LOAD CHALLENGE: "+self._challengeID, color=(0, 1, 0))

    def _play(self):
        self._transitionOut()
        bs.screenMessage(
            "WOULD PLAY CHALLENGE: "+self._challengeID, color=(0, 1, 0))

    def _onForfeitPress(self):
        if self._canForfeit:
            bsUI.ConfirmWindow(
                bs.Lstr(resource='coopSelectWindow.forfeitConfirmText'),
                bs.WeakCall(self._forfeit),
                originWidget=self._forfeitButton, width=400, height=120)
        else:
            bs.screenMessage(
                bs.Lstr(
                    resource='coopSelectWindow.forfeitNotAllowedYetText'),
                color=(1, 0, 0))
            bs.playSound(bs.getSound('error'))

    def _forfeit(self):
        self._transitionOut()
        bs.screenMessage(
            "WOULD FORFEIT CHALLENGE: "+self._challengeID, color=(0, 1, 0))

    def _update(self):
        # figure out what our state should be based on our current cached
        # challenge data
        challenge = bsUI._getCachedChallenge(self._challengeID)
        if challenge is None:
            newState = 'error'
        elif challenge['end'] <= time.time():
            newState = 'ended'
        elif challenge['waitEnd'] > time.time():
            if challenge['waitType'] == 'nextChallenge':
                newState = 'skipWaitNextChallenge'
            else:
                newState = 'skipWaitNextPlay'
        else:
            newState = 'freePlay'

        # if our state is changing, rebuild..
        if self._state != newState:
            self._rebuildForState(newState)

        if self._forfeitButton is not None:
            bs.buttonWidget(
                edit=self._forfeitButton, color=(0.6, 0.45, 0.6)
                if self._canForfeit else(0.6, 0.57, 0.6),
                textColor=(0.65, 0.55, 0.65)
                if self._canForfeit else(0.5, 0.5, 0.5))

    def _onCancel(self):
        self._transitionOut()

    def _transitionOut(self):
        if not self._transitioningOut:
            self._transitioningOut = True
            self._save_state()
            bs.containerWidget(edit=self._rootWidget, transition='outScale')
            if self._onCloseCall is not None:
                self._onCloseCall()

    def onPopupCancel(self):
        bs.playSound(bs.getSound('swish'))
        self._onCancel()

    def _save_state(self):
        pass

    def _restore_state(self):
        pass

class AccountLinkCodeWindow(bsUI.Window):
    def __init__(self, data):
        self._width = 350
        self._height = 200
        self._rootWidget = bs.containerWidget(
            size=(self._width, self._height),
            color=(0.45, 0.63, 0.15),
            transition='inScale', scale=1.8
            if bsUI.gSmallUI else 1.35 if bsUI.gMedUI else 1.0)
        self._data = copy.deepcopy(data)
        bs.playSound(bs.getSound('cashRegister'))
        bs.playSound(bs.getSound('swish'))
        self._cancelButton = bs.buttonWidget(
            parent=self._rootWidget, scale=0.5, position=(40, self._height - 40),
            size=(50, 50),
            label='', onActivateCall=self.close, autoSelect=True,
            color=(0.45, 0.63, 0.15),
            icon=bs.getTexture('crossOut'),
            iconScale=1.2)
        bs.containerWidget(edit=self._rootWidget,
                           cancelButton=self._cancelButton)
        t = bs.textWidget(
            parent=self._rootWidget,
            position=(self._width * 0.5, self._height * 0.5),
            size=(0, 0),
            color=(1.0, 3.0, 1.0),
            scale=2.0, hAlign="center", vAlign="center", text=data['code'],
            maxWidth=self._width * 0.85)

    def close(self):
        bs.containerWidget(edit=self._rootWidget, transition='outScale')


class ServerDialogWindow(bsUI.Window):

    def __init__(self, data):
        self._dialogID = data['dialogID']
        txt = bs.Lstr(
            translate=('serverResponses', data['text']),
            subs=data.get('subs', [])).evaluate()
        txt = txt.strip()
        txtScale = 1.5
        txtHeight = bsInternal._getStringHeight(
            txt, suppressWarning=True) * txtScale
        self._width = 500
        self._height = 130+min(200, txtHeight)
        self._rootWidget = bs.containerWidget(
            size=(self._width, self._height),
            transition='inScale', scale=1.8
            if bsUI.gSmallUI else 1.35 if bsUI.gMedUI else 1.0)
        self._startTime = bs.getRealTime()

        bs.playSound(bs.getSound('swish'))
        t = bs.textWidget(
            parent=self._rootWidget,
            position=(self._width * 0.5, 70 + (self._height - 70) * 0.5),
            size=(0, 0),
            color=(1.0, 3.0, 1.0),
            scale=txtScale, hAlign="center", vAlign="center", text=txt,
            maxWidth=self._width * 0.85, maxHeight=(self._height - 110))
        showCancel = data.get('showCancel', True)
        if showCancel:
            self._cancelButton = bs.buttonWidget(
                parent=self._rootWidget, position=(30, 30),
                size=(160, 60),
                autoSelect=True, label=bs.Lstr(resource='cancelText'),
                onActivateCall=self._cancelPress)
        else:
            self._cancelButton = None
        self._okButton = bs.buttonWidget(
            parent=self._rootWidget,
            position=((self._width - 182)
                      if showCancel else(self._width * 0.5 - 80), 30),
            size=(160, 60),
            autoSelect=True, label=bs.Lstr(resource='okText'),
            onActivateCall=self._okPress)
        bs.containerWidget(edit=self._rootWidget,
                           cancelButton=self._cancelButton,
                           startButton=self._okButton,
                           selectedChild=self._okButton)

    def _okPress(self):
        if bs.getRealTime()-self._startTime < 1000:
            bs.playSound(bs.getSound('error'))
            return
        bsInternal._addTransaction(
            {'type': 'DIALOG_RESPONSE',
             'dialogID': self._dialogID, 'response': 1})
        bs.containerWidget(edit=self._rootWidget, transition='outScale')

    def _cancelPress(self):
        if bs.getRealTime()-self._startTime < 1000:
            bs.playSound(bs.getSound('error'))
            return
        bsInternal._addTransaction(
            {'type': 'DIALOG_RESPONSE',
             'dialogID': self._dialogID, 'response': 0})
        bs.containerWidget(edit=self._rootWidget, transition='outScale')


class ReportPlayerWindow(bsUI.Window):

    def __init__(self, accountID, originWidget):
        self._width = 550
        self._height = 220
        self._accountID = accountID
        self._transitionOut = 'outScale'
        scaleOrigin = originWidget.getScreenSpaceCenter()
        transition = 'inScale'

        self._rootWidget = bs.containerWidget(
            size=(self._width, self._height),
            parent=bsInternal._getSpecialWidget('overlayStack'),
            transition='inScale', scaleOriginStackOffset=scaleOrigin, scale=1.8
            if bsUI.gSmallUI else 1.35 if bsUI.gMedUI else 1.0)
        self._cancelButton = bs.buttonWidget(
            parent=self._rootWidget, scale=0.7, position=(40, self._height - 50),
            size=(50, 50),
            label='', onActivateCall=self.close, autoSelect=True,
            color=(0.4, 0.4, 0.5),
            icon=bs.getTexture('crossOut'),
            iconScale=1.2)
        bs.containerWidget(edit=self._rootWidget,
                           cancelButton=self._cancelButton)
        t = bs.textWidget(
            parent=self._rootWidget,
            position=(self._width * 0.5, self._height * 0.64),
            size=(0, 0),
            color=(1, 1, 1, 0.8),
            scale=1.2, hAlign="center", vAlign="center", text=bs.Lstr(
                resource='reportThisPlayerReasonText'),
            maxWidth=self._width * 0.85)
        bs.buttonWidget(
            parent=self._rootWidget, size=(235, 60),
            position=(20, 30),
            label=bs.Lstr(resource='reportThisPlayerLanguageText'),
            onActivateCall=self._onLanguagePress, autoSelect=True)
        bs.buttonWidget(
            parent=self._rootWidget, size=(235, 60),
            position=(self._width - 255, 30),
            label=bs.Lstr(resource='reportThisPlayerCheatingText'),
            onActivateCall=self._onCheatingPress, autoSelect=True)

    def _onLanguagePress(self):
        bsInternal._addTransaction({'type': 'REPORT_ACCOUNT',
                                    'reason': 'language',
                                    'account': self._accountID})
        import urllib
        body = bs.Lstr(resource='reportPlayerExplanationText').evaluate()
        bs.openURL(
            'mailto:support@froemling.net?subject=BombSquad Player Report: ' +
            self._accountID + '&body=' + urllib.quote(bs.utf8(body)))
        self.close()

    def _onCheatingPress(self):
        bsInternal._addTransaction({'type': 'REPORT_ACCOUNT',
                                    'reason': 'cheating',
                                    'account': self._accountID})
        import urllib
        body = bs.Lstr(resource='reportPlayerExplanationText').evaluate()
        bs.openURL(
            'mailto:support@froemling.net?subject=BombSquad Player Report: ' +
            self._accountID + '&body=' + urllib.quote(bs.utf8(body)))
        self.close()

    def close(self):
        bs.containerWidget(edit=self._rootWidget, transition='outScale')


class SharePlaylistResultsWindow(bsUI.Window):

    def __init__(self, name, data, origin=(0, 0)):

        self._width = 450
        self._height = 300
        self._rootWidget = bs.containerWidget(
            size=(self._width, self._height),
            color=(0.45, 0.63, 0.15),
            transition='inScale', scale=1.8
            if bsUI.gSmallUI else 1.35 if bsUI.gMedUI else 1.0)
        bs.playSound(bs.getSound('cashRegister'))
        bs.playSound(bs.getSound('swish'))

        self._cancelButton = bs.buttonWidget(
            parent=self._rootWidget, scale=0.7,
            position=(40, self._height - (40)),
            size=(50, 50),
            label='', onActivateCall=self.close, autoSelect=True,
            color=(0.45, 0.63, 0.15),
            icon=bs.getTexture('crossOut'),
            iconScale=1.2)
        bs.containerWidget(edit=self._rootWidget,
                           cancelButton=self._cancelButton)

        t = bs.textWidget(
            parent=self._rootWidget,
            position=(self._width * 0.5, self._height * 0.745),
            size=(0, 0),
            color=bsUI.gInfoTextColor, scale=1.0, flatness=1.0, hAlign="center",
            vAlign="center", text=bs.Lstr(
                resource='exportSuccessText', subs=[('${NAME}', name)]),
            maxWidth=self._width * 0.85)

        t = bs.textWidget(
            parent=self._rootWidget,
            position=(self._width * 0.5, self._height * 0.645),
            size=(0, 0),
            color=bsUI.gInfoTextColor, scale=0.6, flatness=1.0, hAlign="center",
            vAlign="center", text=bs.Lstr(
                resource='importPlaylistCodeInstructionsText'),
            maxWidth=self._width * 0.85)

        t = bs.textWidget(
            parent=self._rootWidget,
            position=(self._width * 0.5, self._height * 0.4),
            size=(0, 0),
            color=(1.0, 3.0, 1.0),
            scale=2.3, hAlign="center", vAlign="center", text=data,
            maxWidth=self._width * 0.85)

    def close(self):
        bs.containerWidget(edit=self._rootWidget, transition='outScale')


class SharePlaylistImportWindow(bsUI.PromoCodeWindow):

    def __init__(self, originWidget=None, onSuccessCallback=None):
        bsUI.PromoCodeWindow.__init__(
            self, modal=True, originWidget=originWidget)
        self._onSuccessCallback = onSuccessCallback

    def _onImportResponse(self, response):

        if response is None:
            bs.screenMessage(bs.Lstr(resource='errorText'), color=(1, 0, 0))
            bs.playSound(bs.getSound('error'))
            return

        if response['playlistType'] == 'Team Tournament':
            playlistTypeName = bs.Lstr(resource='playModes.teamsText')
        elif response['playlistType'] == 'Free-for-All':
            playlistTypeName = bs.Lstr(resource='playModes.freeForAllText')
        else:
            playlistTypeName = bs.Lstr(value=response['playlistType'])

        playlistTypeName
        bs.screenMessage(
            bs.Lstr(
                resource='importPlaylistSuccessText',
                subs=[('${TYPE}', playlistTypeName),
                      ('${NAME}', response['playlistName'])]),
            color=(0, 1, 0))
        bs.playSound(bs.getSound('gunCocking'))
        if self._onSuccessCallback is not None:
            self._onSuccessCallback()
        bs.containerWidget(edit=self._rootWidget,
                           transition=self._transitionOut)

    def _doEnter(self):
        bsInternal._addTransaction(
            {'type': 'IMPORT_PLAYLIST', 'expireTime': time.time() + 5,
             'code': bs.textWidget(query=self._textField)},
            callback=bs.WeakCall(self._onImportResponse))
        bsInternal._runTransactions()
        bs.screenMessage(bs.Lstr(resource='importingText'))


gHavePartyQueueWindow = False


class PartyQueueWindow(bsUI.Window):

    class Dude(object):
        def __init__(
            self, parent, distance, initialOffset, isPlayer, accountID,
                name):
            sc = 1.0
            self._lineLeft = parent._lineLeft
            self._lineWidth = parent._lineWidth
            self._lineBottom = parent._lineBottom
            self._targetDistance = distance
            self._distance = distance + initialOffset
            self._boostBrightness = 0.0
            self._debug = False

            position = (parent._lineLeft + self._lineWidth *
                        (1.0 - self._distance),
                        parent._lineBottom + 40)
            self._sc = sc = 1.1 if isPlayer else 0.6 + random.random() * 0.2
            self._yOffs = -30.0 if isPlayer else -47.0 * sc
            self._color = (
                0.2, 1.0, 0.2) if isPlayer else(
                0.5 + 0.3 * random.random(),
                0.4 + 0.2 * random.random(),
                0.5 + 0.3 * random.random())
            self._eyeColor = (0.7*1.0+0.3*self._color[0],
                              0.7*1.0+0.3*self._color[1],
                              0.7*1.0+0.3*self._color[2])
            self._bodyImage = bs.buttonWidget(
                parent=parent._rootWidget, selectable=True, label='',
                size=(sc * 60, sc * 80),
                color=self._color, texture=parent._lineupTex,
                modelTransparent=parent._lineup1TransparentModel)
            bs.buttonWidget(edit=self._bodyImage, onActivateCall=bs.WeakCall(
                parent.onAccountPress, accountID, self._bodyImage))
            bs.widget(edit=self._bodyImage, autoSelect=True)
            self._eyesImage = bs.imageWidget(
                parent=parent._rootWidget, size=(sc * 36, sc * 18),
                texture=parent._lineupTex, color=self._eyeColor,
                modelTransparent=parent._eyesModel)
            self._nameText = bs.textWidget(
                parent=parent._rootWidget, size=(0, 0),
                shadow=0, flatness=1.0, text=name, maxWidth=100,
                hAlign='center', vAlign='center', scale=0.75,
                color=(1, 1, 1, 0.6))
            self._updateImage()

            # DEBUG: vis target pos..
            if self._debug:
                self._bodyImageTarget = bs.imageWidget(
                    parent=parent._rootWidget, size=(sc * 60, sc * 80),
                    color=self._color, texture=parent._lineupTex,
                    modelTransparent=parent._lineup1TransparentModel)
                self._eyesImageTarget = bs.imageWidget(
                    parent=parent._rootWidget, size=(sc * 36, sc * 18),
                    texture=parent._lineupTex, color=self._eyeColor,
                    modelTransparent=parent._eyesModel)
                # (updates our image positions)
                self.setTargetDistance(self._targetDistance)
            else:
                self._bodyImageTarget = self._eyesImageTarget = None

        def __del__(self):

            # ew.  our destructor here may get called as part of an internal
            # widget tear-down.
            # running further widget calls here can quietly break stuff, so we
            # need to push a deferred call to kill these as necessary instead.
            # (should bulletproof internal widget code to give a clean error
            # in this case)
            def killWidgets(widgets):
                for widget in widgets:
                    if widget is not None and widget.exists():
                        widget.delete()
            bs.pushCall(
                bs.Call(
                    killWidgets,
                    [self._bodyImage, self._eyesImage, self._bodyImageTarget,
                     self._eyesImageTarget, self._nameText]))

        def setTargetDistance(self, dist):
            self._targetDistance = dist
            if self._debug:
                sc = self._sc
                position = (
                    self._lineLeft + self._lineWidth *
                    (1.0 - self._targetDistance),
                    self._lineBottom - 30)
                bs.imageWidget(edit=self._bodyImageTarget, position=(
                    position[0]-sc*30, position[1]-sc*25-70))
                bs.imageWidget(edit=self._eyesImageTarget, position=(
                    position[0]-sc*18, position[1]+sc*31-70))

        def step(self, smoothing):
            self._distance = smoothing * self._distance + \
                (1.0 - smoothing) * self._targetDistance
            self._updateImage()
            self._boostBrightness *= 0.9

        def _updateImage(self):
            sc = self._sc
            position = (self._lineLeft + self._lineWidth *
                        (1.0 - self._distance),
                        self._lineBottom + 40)
            brightness = 1.0 + self._boostBrightness
            bs.buttonWidget(
                edit=self._bodyImage,
                position=(position[0] - sc * 30, position[1] - sc * 25
                          + self._yOffs),
                color=(self._color[0] * brightness, self._color
                       [1] * brightness,
                       self._color[2] * brightness))
            bs.imageWidget(
                edit=self._eyesImage,
                position=(position[0]-sc*18, position[1]+sc*31+self._yOffs),
                color=(self._eyeColor[0]*brightness,
                       self._eyeColor[1]*brightness,
                       self._eyeColor[2]*brightness))
            bs.textWidget(edit=self._nameText, position=(
                position[0]-sc*0, position[1]+sc*40.0))

        def boost(self, amount, smoothing):
            self._distance = max(0.0, self._distance - amount)
            self._updateImage()
            self._lastBoostTime = time.time()
            self._boostBrightness += 0.6

    def __init__(self, queueID, address, port):
        global gHavePartyQueueWindow
        gHavePartyQueueWindow = True
        self._address = address
        self._port = port
        self._queueID = queueID
        self._width = 800
        self._height = 400
        self._lastConnectAttemptTime = None
        self._lastTransactionTime = None
        self._boostButton = None
        self._boostPrice = None
        self._boostLabel = None
        self._fieldShown = False
        self._dudes = []
        self._dudesByID = {}
        self._ticketsRemaining = None
        self._lineLeft = 40.0
        self._lineWidth = self._width - 190
        self._lineBottom = self._height * 0.4
        self._lineupTex = bs.getTexture('playerLineup')
        self._angryComputerTransparentModel = bs.getModel(
            'angryComputerTransparent')
        self._angryComputerImage = None
        self._lineup1TransparentModel = bs.getModel('playerLineup1Transparent')
        self._lineup2TransparentModel = bs.getModel('playerLineup2Transparent')
        self._lineup3TransparentModel = bs.getModel('playerLineup3Transparent')
        self._lineup4TransparentModel = bs.getModel('playerLineup4Transparent')
        self._lineImage = None
        self._eyesModel = bs.getModel('plasticEyesTransparent')
        self._whiteTex = bs.getTexture('white')
        self._rootWidget = bs.containerWidget(
            size=(self._width, self._height),
            color=(0.45, 0.63, 0.15),
            transition='inScale', scale=1.4
            if bsUI.gSmallUI else 1.2 if bsUI.gMedUI else 1.0)

        self._cancelButton = bs.buttonWidget(
            parent=self._rootWidget, scale=1.0,
            position=(60, self._height - 80),
            size=(50, 50),
            label='', onActivateCall=self.close, autoSelect=True,
            color=(0.45, 0.63, 0.15),
            icon=bs.getTexture('crossOut'),
            iconScale=1.2)
        bs.containerWidget(edit=self._rootWidget,
                           cancelButton=self._cancelButton)

        self._titleText = bs.textWidget(
            parent=self._rootWidget,
            position=(self._width * 0.5, self._height * 0.55),
            size=(0, 0),
            color=(1.0, 3.0, 1.0),
            scale=1.3, hAlign="center", vAlign="center", text=bs.Lstr(
                resource='internal.connectingToPartyText'),
            maxWidth=self._width * 0.65)

        self._ticketsText = bs.textWidget(
            parent=self._rootWidget,
            position=(self._width - 180, self._height - 20),
            size=(0, 0),
            color=(0.2, 1.0, 0.2),
            scale=0.7, hAlign="center", vAlign="center", text='')

        # update at roughly 30fps
        self._updateTimer = bs.Timer(
            33, bs.WeakCall(self.update),
            repeat=True, timeType='real')
        self.update()

    def __del__(self):
        try:
            global gHavePartyQueueWindow
            gHavePartyQueueWindow = False
            bsInternal._addTransaction(
                {'type': 'PARTY_QUEUE_REMOVE', 'q': self._queueID})
            bsInternal._runTransactions()
        except Exception:
            bs.printException('err removing self from party queue')

    def onAccountPress(self, accountID, originWidget):
        if accountID is None:
            bs.playSound(bs.getSound('error'))
            return
        bsUI.AccountInfoWindow(accountID=accountID,
                               position=originWidget.getScreenSpaceCenter())

    def close(self):
        bs.containerWidget(edit=self._rootWidget, transition='outScale')

    def _updateField(self, response):
        if self._angryComputerImage is None:
            self._angryComputerImage = bs.imageWidget(
                parent=self._rootWidget,
                position=(self._width - 180, self._height * 0.5 - 65),
                size=(150, 150),
                texture=self._lineupTex,
                modelTransparent=self._angryComputerTransparentModel)
        if self._lineImage is None:
            self._lineImage = bs.imageWidget(
                parent=self._rootWidget, color=(0.0, 0.0, 0.0),
                opacity=0.2, position=(self._lineLeft, self._lineBottom - 2.0),
                size=(self._lineWidth, 4.0),
                texture=self._whiteTex)

        # now go through the data they sent, creating dudes for us and our
        # enemies as needed and updating target positions on all of them..

        # mark all as unclaimed so we know which ones to kill off..
        for dude in self._dudes:
            dude.claimed = False

        # always have a dude for ourself..
        if -1 not in self._dudesByID:
            dude = self.Dude(
                self, response['d'],
                self._initialOffset, True, bsInternal._getAccountMiscReadVal2(
                    'resolvedAccountID', None),
                bsInternal._getAccountDisplayString())
            self._dudesByID[-1] = dude
            self._dudes.append(dude)
        else:
            self._dudesByID[-1].setTargetDistance(response['d'])
        self._dudesByID[-1].claimed = True

        # now create/destroy enemies
        for enemyID, enemyDistance, enemyAccountID, enemyName in response['e']:
            if enemyID not in self._dudesByID:
                dude = self.Dude(
                    self, enemyDistance, self._initialOffset, False,
                    enemyAccountID, enemyName)
                self._dudesByID[enemyID] = dude
                self._dudes.append(dude)
            else:
                self._dudesByID[enemyID].setTargetDistance(enemyDistance)
            self._dudesByID[enemyID].claimed = True

        # remove unclaimed dudes from both of our lists
        self._dudesByID = dict(
            [item for item in self._dudesByID.items() if item[1].claimed])
        self._dudes = [dude for dude in self._dudes if dude.claimed]

    def _hideField(self):
        self._angryComputerImage.delete()
        self._angryComputerImage = None
        self._lineImage.delete()
        self._lineImage = None
        self._dudes = []
        self._dudesByID = {}

    def onUpdateResponse(self, response):
        if not self._rootWidget.exists():
            return

        if response is not None:

            shouldShowField = True if response.get('d') is not None else False

            self._smoothing = response['s']
            self._initialOffset = response['o']

            # if they gave us a position, show the field..
            if shouldShowField:
                bs.textWidget(
                    edit=self._titleText, text=bs.Lstr(
                        resource='waitingInLineText'),
                    position=(self._width * 0.5, self._height * 0.85))
                self._updateField(response)
                self._fieldShown = True
            if not shouldShowField and self._fieldShown:
                bs.textWidget(
                    edit=self._titleText, text=bs.Lstr(
                        resource='internal.connectingToPartyText'),
                    position=(self._width * 0.5, self._height * 0.55))
                self._hideField()
                self._fieldShown = False

            # if they told us there's a boost button, update..
            if response.get('bt') is not None:
                self._boostTickets = response['bt']
                self._boostStrength = response['bs']
                if self._boostButton is None:
                    self._boostButton = bs.buttonWidget(
                        parent=self._rootWidget, scale=1.0,
                        position=(self._width * 0.5 - 75, 20),
                        size=(150, 100),
                        buttonType='square', label='',
                        onActivateCall=self.onBoostPress, enableSound=False,
                        color=(0, 1, 0),
                        autoSelect=True)
                    self._boostLabel = bs.textWidget(
                        parent=self._rootWidget,
                        drawController=self._boostButton,
                        position=(self._width * 0.5, 88),
                        size=(0, 0),
                        color=(0.8, 1.0, 0.8),
                        scale=1.5, hAlign="center", vAlign="center",
                        text=bs.Lstr(resource='boostText'),
                        maxWidth=150)
                    self._boostPrice = bs.textWidget(
                        parent=self._rootWidget,
                        drawController=self._boostButton,
                        position=(self._width * 0.5, 50),
                        size=(0, 0),
                        color=(0, 1, 0),
                        scale=0.9, hAlign="center", vAlign="center",
                        text=bs.getSpecialChar('ticket') +
                        str(self._boostTickets),
                        maxWidth=150)
            else:
                if self._boostButton is not None:
                    self._boostButton.delete()
                    self._boostButton = None
                if self._boostPrice is not None:
                    self._boostPrice.delete()
                    self._boostPrice = None
                if self._boostLabel is not None:
                    self._boostLabel.delete()
                    self._boostLabel = None

            # if they told us to go ahead and try and connect, do so..
            # (note: servers will disconnect us if we try to connect before
            # getting this go-ahead, so don't get any bright ideas...)
            if response.get('c', False):
                # enforce a delay between connection attempts
                # (in case they're jamming on the boost button)
                now = time.time()
                if (self._lastConnectAttemptTime is None
                        or now - self._lastConnectAttemptTime > 10.0):
                    bsInternal._connectToParty(
                        address=self._address, port=self._port,
                        printProgress=False)
                    self._lastConnectAttemptTime = now

    def onBoostPress(self):
        if bsInternal._getAccountState() != 'SIGNED_IN':
            bsUI.showSignInPrompt()
            return

        if bsInternal._getAccountTicketCount() < self._boostTickets:
            bs.playSound(bs.getSound('error'))
            bsUI.showGetTicketsPrompt()
            return

        bs.playSound(bs.getSound('laserReverse'))
        bsInternal._addTransaction({'type': 'PARTY_QUEUE_BOOST',
                                    't': self._boostTickets,
                                    'q': self._queueID},
                                   callback=bs.WeakCall(self.onUpdateResponse))
        # lets not run these immediately (since they may be rapid-fire,
        # just bucket them until the next tick)

        # the transaction handles the local ticket change, but we apply our
        # local boost vis manually here..
        # (our visualization isnt really wired up to be transaction-based)
        ourDude = self._dudesByID.get(-1)
        if ourDude is not None:
            ourDude.boost(self._boostStrength, self._smoothing)

    def update(self):
        if not self._rootWidget.exists():
            return

        # update boost-price
        if self._boostPrice is not None:
            bs.textWidget(edit=self._boostPrice, text=bs.getSpecialChar(
                'ticket') + str(self._boostTickets))

        # update boost button color based on if we have enough moola
        if self._boostButton is not None:
            canBoost = (True if (bsInternal._getAccountState() == 'SIGNED_IN'
                                 and bsInternal._getAccountTicketCount() >=
                                 self._boostTickets) else False)
            bs.buttonWidget(
                edit=self._boostButton,
                color=(0, 1, 0) if canBoost else (0.7, 0.7, 0.7))

        # update ticket-count
        if self._ticketsText is not None:
            if self._boostButton is not None:
                if bsInternal._getAccountState() == 'SIGNED_IN':
                    val = bs.getSpecialChar(
                        'ticket')+str(bsInternal._getAccountTicketCount())
                else:
                    val = bs.getSpecialChar('ticket')+'???'
                bs.textWidget(edit=self._ticketsText, text=val)
            else:
                bs.textWidget(edit=self._ticketsText, text='')

        currentTime = bs.getRealTime()
        if (self._lastTransactionTime is None
                or currentTime - self._lastTransactionTime >
                bsInternal._getAccountMiscReadVal('pqInt', 5000)):
            self._lastTransactionTime = currentTime
            bsInternal._addTransaction(
                {'type': 'PARTY_QUEUE_QUERY', 'q': self._queueID},
                callback=bs.WeakCall(self.onUpdateResponse))
            bsInternal._runTransactions()

        # step our dudes
        for dude in self._dudes:
            dude.step(self._smoothing)


class ResourceTypeInfoWindow(bsUI.PopupWindow):
    def __init__(self, originWidget):
        scale = 2.3 if bsUI.gSmallUI else 1.65 if bsUI.gMedUI else 1.23
        self._transitioningOut = False
        self._width = 570
        self._height = 350
        bgColor = (0.5, 0.4, 0.6)
        bsUI.PopupWindow.__init__(self, size=(self._width, self._height),
                                  toolbarVisibility='INHERIT',
                                  scale=scale, bgColor=bgColor,
                                  position=originWidget.getScreenSpaceCenter())
        self._cancelButton = bs.buttonWidget(
            parent=self._rootWidget, position=(50, self._height - 30),
            size=(50, 50),
            scale=0.5, label='', color=bgColor,
            onActivateCall=self._onCancelPress, autoSelect=True,
            icon=bs.getTexture('crossOut'),
            iconScale=1.2)

    def _onCancelPress(self):
        self._transitionOut()

    def _transitionOut(self):
        if not self._transitioningOut:
            self._transitioningOut = True
            bs.containerWidget(edit=self._rootWidget, transition='outScale')

    def onPopupCancel(self):
        bs.playSound(bs.getSound('swish'))
        self._transitionOut()
