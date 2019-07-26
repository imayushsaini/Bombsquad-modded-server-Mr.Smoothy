import bs
import bsUtils
import bsInternal

gAchievements = []
gAchievementsToDisplay = []
gAchievementDisplayTimer = None
gLastAchievementDisplayTime = 0
gCompletionBannerSlots = set()

# FIXME we should probably point achievements
# at coop levels instead of hard-coding names..
# (so level name substitution works right and whatnot)
gAchLevelNames = {
    'Boom Goes the Dynamite': 'Pro Onslaught',
    'Boxer': 'Onslaught Training',
    'Flawless Victory': 'Rookie Onslaught',
    'Gold Miner': 'Uber Onslaught',
    'Got the Moves': 'Uber Football',
    'Last Stand God': 'The Last Stand',
    'Last Stand Master': 'The Last Stand',
    'Last Stand Wizard': 'The Last Stand',
    'Mine Games': 'Rookie Onslaught',
    'Off You Go Then': 'Onslaught Training',
    'Onslaught God': 'Infinite Onslaught',
    'Onslaught Master': 'Infinite Onslaught',
    'Onslaught Training Victory': 'Onslaught Training',
    'Onslaught Wizard': 'Infinite Onslaught',
    'Precision Bombing': 'Pro Runaround',
    'Pro Boxer': 'Pro Onslaught',
    'Pro Football Shutout': 'Pro Football',
    'Pro Football Victory': 'Pro Football',
    'Pro Onslaught Victory': 'Pro Onslaught',
    'Pro Runaround Victory': 'Pro Runaround',
    'Rookie Football Shutout': 'Rookie Football',
    'Rookie Football Victory': 'Rookie Football',
    'Rookie Onslaught Victory': 'Rookie Onslaught',
    'Runaround God': 'Infinite Runaround',
    'Runaround Master': 'Infinite Runaround',
    'Runaround Wizard': 'Infinite Runaround',
    'Stayin\' Alive': 'Uber Runaround',
    'Super Mega Punch': 'Pro Football',
    'Super Punch': 'Rookie Football',
    'TNT Terror': 'Uber Onslaught',
    'The Great Wall': 'Uber Runaround',
    'The Wall': 'Pro Runaround',
    'Uber Football Shutout': 'Uber Football',
    'Uber Football Victory': 'Uber Football',
    'Uber Onslaught Victory': 'Uber Onslaught',
    'Uber Runaround Victory': 'Uber Runaround'
}

# used for non-game-based achievements such as controller-connection ones


def _awardLocalAchievement(ach):
    try:
        a = getAchievement(ach)
        if a is not None and not a.isComplete():
            # report new achievements to the game-service..
            bsInternal._reportAchievement(ach)
            # and to our account..
            bsInternal._addTransaction({'type': 'ACHIEVEMENT', 'name': ach})
            # now attempt to show a banner
            _displayBanner(ach)

    except Exception:
        bs.printException()


# simply display a completion banner for an achievement; used for server-driven
# achievements
def _displayBanner(ach):
    try:
        import bsAchievement
        # FIXME - need to get these using the UI context somehow instead of
        # trying to inject these into whatever activity happens to be active..
        # (since that won't work while in client mode)
        a = bsInternal._getForegroundHostActivity()
        if a is not None:
            with bs.Context(a):
                bsAchievement.getAchievement(ach).announceCompletion()
    except Exception:
        bs.printException('error showing server ach')

# this gets called whenever game-center/game-circle/etc tells us which
# achievements we currently have.  We always defer to them, even if that
# means we have to un-set an achievement we think we have


def setCompletedAchievements(achs):
    #print 'LOCALLY SETTING COMPLETED TO',achs
    # clear all then fill these in
    bs.getConfig()['Achievements'] = {}
    for aName in achs:
        getAchievement(aName).setComplete(announce=False, writeConfig=False)
    # write config in one fell swoop..
    bs.writeConfig()


def getAchievement(name):
    try:
        return [a for a in gAchievements if a._name == name][0]
    except Exception:
        raise Exception("Invalid achievement name: '"+name+"'")

# return the mult for achievement pts (just for display; changing this here
# won't affect what you get :-P)


def _getAchMult(includeProBonus=False):
    val = bsInternal._getAccountMiscReadVal('achAwardMult', 5)
    if includeProBonus and bsUtils._havePro():
        val *= 2
    return val


def getAchievementsForCoopLevel(level):
    # for the Easy campaign we return achievements for the Default
    # campaign too.. (want the user to see what achieements are part of the
    # level even if they can't unlock them all on easy mode)
    return [a for a in gAchievements if a._level in
            (level, level.replace('Easy', 'Default'))]


def _displayNextAchievement():
    global gAchievementDisplayTimer
    global gAchievementsToDisplay

    # pull the first achievement off the list and display it, or kill the
    # display-timer if the list is empty
    if len(gAchievementsToDisplay) > 0:
        try:
            a, sound = gAchievementsToDisplay.pop(0)
            a.showCompletionBanner(sound)
        except Exception:
            bs.printException("error showing next achievement")
            gAchievementsToDisplay = []
            gAchievementDisplayTimer = None
    else:
        gAchievementDisplayTimer = None


class Achievement(object):
    def __init__(self, name, iconName, iconColor, level, award,
                 hardModeOnly=False):
        self._name = name
        self._iconName = iconName
        self._iconColor = list(iconColor)+[1]
        self._level = level
        self._completionBannerSlot = None
        self._award = award
        self._hardModeOnly = hardModeOnly

    def getName(self):
        return self._name

    def getIconTexture(self, complete):
        return bs.getTexture(self._iconName if complete else 'achievementEmpty')

    def getIconColor(self, complete):
        return self._iconColor if complete else (1, 1, 1, 0.6)

    def _getConfig(self):
        if not 'Achievements' in bs.getConfig():
            bs.getConfig()['Achievements'] = {}
        if not self._name in bs.getConfig()['Achievements']:
            bs.getConfig()['Achievements'][self._name] = {'Complete': False}
        return bs.getConfig()['Achievements'][self._name]

    def isHardModeOnly(self):
        return self._hardModeOnly

    def isComplete(self):
        config = self._getConfig()
        return config['Complete']

    def announceCompletion(self, sound=True):

        # even though there are technically achievements when we're not
        # signed in, lets not show them (otherwise we tend to get
        # confusing 'controller connected' achievements popping up while
        # waiting to log in which can be confusing..
        if bsInternal._getAccountState() != 'SIGNED_IN':
            return

        # if we're being freshly complete, display/report it and whatnot
        if not [self, sound] in gAchievementsToDisplay:
            gAchievementsToDisplay.append([self, sound])

        # if there's no achievement display timer going, kick one off
        # (if one's already running it will pick this up before it dies)
        global gAchievementDisplayTimer
        global gLastAchievementDisplayTime
        # need to check last time too; its possible our timer wasn't able to
        # clear itself if an activity died and took it down with it..
        if ((gAchievementDisplayTimer is None
             or bs.getRealTime()-gLastAchievementDisplayTime > 2000)
                and bs.getActivity(exceptionOnNone=False) is not None):
            gAchievementDisplayTimer = bs.Timer(
                1000, _displayNextAchievement, repeat=True, timeType='net')
            _displayNextAchievement()  # show the first immediately

    # note this only sets local state; use a transaction to actually award these
    def setComplete(self, complete=True, announce=True, sound=True,
                    writeConfig=True):
        config = self._getConfig()
        if complete != config['Complete']:
            config['Complete'] = complete
            if writeConfig:
                bs.writeConfig()

    def getDisplayString(self):
        try:
            if self._level != '':
                import bsCoopGame
                campaignName, campaignLevel = self._level.split(':')
                n = bsCoopGame.getCampaign(campaignName).getLevel(
                    campaignLevel).getDisplayString()
            else:
                n = ''
        except Exception, e:
            n = ''
            bs.printException()
        return bs.Lstr(
            resource='achievements.' + self._name + '.name',
            subs=[('${LEVEL}', n)])

    def getDescription(self):
        if 'description' in bsUtils._getResource('achievements')[self._name]:
            return bs.Lstr(resource='achievements.'+self._name+'.description')
        else:
            return bs.Lstr(resource='achievements.' + self._name +
                           '.descriptionFull')

    def getDescriptionComplete(self):
        if 'descriptionComplete' in bsUtils._getResource('achievements')[
                self._name]:
            return bs.Lstr(resource='achievements.' + self._name +
                           '.descriptionComplete')
        else:
            return bs.Lstr(
                resource='achievements.' + self._name +
                '.descriptionFullComplete')

    def getDescriptionFull(self):
        return bs.Lstr(
            resource='achievements.' + self._name + '.descriptionFull',
            subs=[('${LEVEL}', bs.Lstr(
                translate=['coopLevelNames', gAchLevelNames.get(
                           self._name, '?')]))])

    def getDescriptionFullComplete(self):
        return bs.Lstr(
            resource='achievements.' + self._name + '.descriptionFullComplete',
            subs=[('${LEVEL}', bs.Lstr(
                translate=['coopLevelNames', gAchLevelNames.get(
                           self._name, '?')]))])

    def getAwardTicketValue(self, includeProBonus=False):
        'Return the ticket award value for this achievement'
        return (bsInternal._getAccountMiscReadVal(
            'achAward.' + self._name, self._award)
                * _getAchMult(includeProBonus))

    def getPowerRankingValue(self):
        'Return the power-ranking award value for this achievement'
        return bsInternal._getAccountMiscReadVal(
            'achLeaguePoints.' + self._name, self._award)

    def createDisplay(
            self, x, y, delay, outDelay=None, color=None, style='postGame'):

        if style == 'postGame':
            inGameColors = False
            inMainMenu = False
            hAttach = vAttach = attach = 'center'
        elif style == 'inGame':
            inGameColors = True
            inMainMenu = False
            hAttach = 'left'
            vAttach = 'top'
            attach = 'topLeft'
        elif style == 'news':
            inGameColors = True
            inMainMenu = True
            hAttach = 'center'
            vAttach = 'top'
            attach = 'topCenter'
        else:
            raise Exception('invalid style "'+style+'"')

        # attempt to determine what campaign we're in
        # (so we know whether to show "hard mode only")
        if inMainMenu:
            hmo = False
        else:
            try:
                hmo = (
                    self._hardModeOnly and bs.getSession()._campaignInfo
                    ['campaign'] == 'Easy')
            except Exception:
                bs.printException("unable to determine campaign")
                hmo = False

        activity = bs.getActivity()
        if inGameColors:
            objs = []
            outDelayFin = (delay+outDelay) if outDelay is not None else None
            if color is not None:
                c1 = (2.0*color[0], 2.0*color[1], 2.0*color[2], color[3])
                c2 = color
            else:
                c1 = (1.5, 1.5, 2, 1.0)
                c2 = (0.8, 0.8, 1.0, 1.0)

            if hmo:
                c1 = (c1[0], c1[1], c1[2], c1[3]*0.6)
                c2 = (c2[0], c2[1], c2[2], c2[3]*0.2)

            objs.append(bsUtils.Image(self.getIconTexture(False),
                                      hostOnly=True,
                                      color=c1,
                                      position=(x-25, y+5),
                                      attach=attach,
                                      transition='fadeIn',
                                      transitionDelay=delay,
                                      vrDepth=4,
                                      transitionOutDelay=outDelayFin,
                                      scale=(40, 40)).autoRetain())
            txt = self.getDisplayString()
            txtS = 0.85
            txtMaxW = 300
            objs.append(bsUtils.Text(
                txt, hostOnly=True, maxWidth=txtMaxW,
                position=(x, y + 2),
                transition='fadeIn', scale=txtS, flatness=0.6,
                shadow=0.5, hAttach=hAttach, vAttach=vAttach,
                color=c2, transitionDelay=delay + 50,
                transitionOutDelay=outDelayFin).autoRetain())
            txt2S = 0.62
            txt2MaxW = 400
            objs.append(
                bsUtils.Text(
                    self.getDescriptionFull()
                    if inMainMenu else self.getDescription(), hostOnly=True,
                    maxWidth=txt2MaxW, position=(x, y - 14),
                    transition='fadeIn', vrDepth=-5, hAttach=hAttach,
                    vAttach=vAttach, scale=txt2S, flatness=1.0, shadow=0.5,
                    color=c2, transitionDelay=delay + 100,
                    transitionOutDelay=outDelayFin).autoRetain())

            if hmo:
                t = bsUtils.Text(bs.Lstr(resource='difficultyHardOnlyText'),
                                 hostOnly=True,
                                 maxWidth=txt2MaxW*0.7,
                                 position=(x+60, y+5),
                                 transition='fadeIn',
                                 vrDepth=-5,
                                 hAttach=hAttach,
                                 vAttach=vAttach,
                                 hAlign='center',
                                 vAlign='center',
                                 scale=txtS*0.8,
                                 flatness=1.0,
                                 shadow=0.5,
                                 color=(1, 1, 0.6, 1),
                                 transitionDelay=delay+100,
                                 transitionOutDelay=outDelayFin).autoRetain()
                t.node.rotate = 10
                objs.append(t)

            # ticket-award
            awardX = -100
            objs.append(bsUtils.Text(
                bs.getSpecialChar('ticket'),
                hostOnly=True, position=(x + awardX + 33, y + 7),
                transition='fadeIn', scale=1.5, hAttach=hAttach,
                vAttach=vAttach, hAlign='center', vAlign='center',
                color=(1, 1, 1, 0.2 if hmo else 0.4),
                transitionDelay=delay + 50,
                transitionOutDelay=outDelayFin).autoRetain())
            objs.append(bsUtils.Text(
                '+' + str(self.getAwardTicketValue()),
                hostOnly=True, position=(x + awardX + 28, y + 16),
                transition='fadeIn', scale=0.7, flatness=1,
                hAttach=hAttach, vAttach=vAttach, hAlign='center',
                vAlign='center', color=(c2),
                transitionDelay=delay + 50,
                transitionOutDelay=outDelayFin).autoRetain())

        else:
            complete = self.isComplete()
            objs = []
            cIcon = self.getIconColor(complete)
            if hmo and not complete:
                cIcon = (cIcon[0], cIcon[1], cIcon[2], cIcon[3]*0.3)
            objs.append(bsUtils.Image(self.getIconTexture(complete),
                                      hostOnly=True,
                                      color=cIcon,
                                      position=(x-25, y+5),
                                      attach=attach,
                                      vrDepth=4,
                                      transition='inRight',
                                      transitionDelay=delay,
                                      transitionOutDelay=None,
                                      scale=(40, 40)).autoRetain())
            if complete:
                objs.append(
                    bsUtils.Image(
                        bs.getTexture('achievementOutline'),
                        hostOnly=True, modelTransparent=bs.getModel(
                            'achievementOutline'),
                        color=(2, 1.4, 0.4, 1),
                        vrDepth=8, position=(x - 25, y + 5),
                        attach=attach, transition='inRight',
                        transitionDelay=delay, transitionOutDelay=None,
                        scale=(40, 40)).autoRetain())
            else:

                if not complete:
                    awardX = -100
                    objs.append(bsUtils.Text(
                        bs.getSpecialChar('ticket'),
                        hostOnly=True,
                        position=(x + awardX + 33, y + 7),
                        transition='inRight', scale=1.5,
                        hAttach=hAttach, vAttach=vAttach,
                        hAlign='center', vAlign='center',
                        color=(1, 1, 1, 0.4)
                        if complete
                        else(1, 1, 1, (0.1 if hmo else 0.2)),
                        transitionDelay=delay + 50,
                        transitionOutDelay=None).autoRetain())
                    objs.append(bsUtils.Text(
                        '+' + str(self.getAwardTicketValue()),
                        hostOnly=True,
                        position=(x + awardX + 28, y + 16),
                        transition='inRight', scale=0.7, flatness=1,
                        hAttach=hAttach, vAttach=vAttach,
                        hAlign='center', vAlign='center',
                        color=((0.8, 0.93, 0.8, 1.0)
                               if complete
                               else(
                            0.6, 0.6, 0.6,
                            (0.2 if hmo else 0.4))),
                        transitionDelay=delay + 50,
                        transitionOutDelay=None).autoRetain())
                    # show 'hard-mode-only' only over incomplete achievements
                    # when that's the case..
                    if hmo:
                        t = bsUtils.Text(bs.Lstr(
                            resource='difficultyHardOnlyText'),
                            hostOnly=True, maxWidth=300 * 0.7,
                            position=(x + 60, y + 5),
                            transition='fadeIn', vrDepth=-5,
                            hAttach=hAttach, vAttach=vAttach,
                            hAlign='center', vAlign='center',
                            scale=0.85 * 0.8, flatness=1.0,
                            shadow=0.5, color=(1, 1, 0.6, 1),
                            transitionDelay=delay + 50,
                            transitionOutDelay=None).autoRetain()
                        t.node.rotate = 10
                        objs.append(t)

            objs.append(bsUtils.Text(
                self.getDisplayString(),
                hostOnly=True,
                maxWidth=300,
                position=(x, y+2),
                transition='inRight',
                scale=0.85,
                flatness=0.6,
                hAttach=hAttach,
                vAttach=vAttach,
                color=((0.8, 0.93, 0.8, 1.0) if complete
                       else (0.6, 0.6, 0.6, (0.2 if hmo else 0.4))),
                transitionDelay=delay+50,
                transitionOutDelay=None).autoRetain())
            objs.append(bsUtils.Text(
                self.getDescriptionComplete()
                if complete else self.getDescription(),
                hostOnly=True, maxWidth=400, position=(x, y - 14),
                transition='inRight', vrDepth=-5, hAttach=hAttach,
                vAttach=vAttach, scale=0.62, flatness=1.0,
                color=((0.6, 0.6, 0.6, 1.0)
                       if complete
                       else(
                    0.6, 0.6, 0.6, (0.2 if hmo else 0.4))),
                transitionDelay=delay + 100,
                transitionOutDelay=None).autoRetain())
        return objs

    def _removeBannerSlot(self):
        #print 'REMOVING SLOT',self._completionBannerSlot,'FOR',self
        gCompletionBannerSlots.remove(self._completionBannerSlot)
        self._completionBannerSlot = None

    def showCompletionBanner(self, sound=True):

        global gLastAchievementDisplayTime
        gLastAchievementDisplayTime = bs.getRealTime()

        # just piggy-back onto any current activity...
        # (should we use the session instead?..)
        activity = bs.getActivity(exceptionOnNone=False)

        # if this gets called while this achievement is occupying a slot
        # already, ignore it.. (probably should never happen in real
        # life but whatevs..)
        if self._completionBannerSlot is not None:
            return

        if activity is None:
            print 'showCompletionBanner() called with no current activity!'
            return

        if sound:
            bs.playSound(bs.getSound('achievement'), hostOnly=True)
        else:
            bs.gameTimer(
                500, bs.Call(
                    bs.playSound, bs.getSound('ding'),
                    hostOnly=True))

        yOffs = 0
        inTime = 300
        outTime = 3500

        baseVRDepth = 200

        # find the first free slot
        i = 0
        while True:
            if not i in gCompletionBannerSlots:
                #print 'ADDING SLOT',i,'FOR',self
                gCompletionBannerSlots.add(i)
                self._completionBannerSlot = i
                # remove us from that slot when we close..
                # use a real-timer in the UI context so the removal runs even
                # if our activity/session dies
                with bs.Context('UI'):
                    bs.realTimer(inTime+outTime, self._removeBannerSlot)
                break
            i += 1

        yOffs = 110*self._completionBannerSlot

        objs = []
        obj = bsUtils.Image(bs.getTexture('shadow'),
                            position=(-30, 30+yOffs),
                            front=True,
                            attach='bottomCenter',
                            transition='inBottom',
                            vrDepth=baseVRDepth-100,
                            transitionDelay=inTime,
                            transitionOutDelay=outTime,
                            color=(0.0, 0.1, 0, 1),
                            scale=(1000, 300)).autoRetain()
        objs.append(obj)
        obj.node.hostOnly = True
        obj = bsUtils.Image(bs.getTexture('light'),
                            position=(-180, 60+yOffs),
                            front=True,
                            attach='bottomCenter',
                            vrDepth=baseVRDepth,
                            transition='inBottom',
                            transitionDelay=inTime,
                            transitionOutDelay=outTime,
                            color=(1.8, 1.8, 1.0, 0.0),
                            scale=(40, 300)).autoRetain()
        objs.append(obj)

        obj.node.hostOnly = True
        obj.node.premultiplied = True
        c = bs.newNode('combine', owner=obj.node, attrs={'size': 2})
        bsUtils.animate(
            c, 'input0',
            {inTime: 0, inTime + 400: 30, inTime + 500: 40, inTime + 600: 30,
             inTime + 2000: 0})
        bsUtils.animate(
            c, 'input1',
            {inTime: 0, inTime + 400: 200, inTime + 500: 500, inTime + 600: 200,
             inTime + 2000: 0})
        c.connectAttr('output', obj.node, 'scale')
        bsUtils.animate(obj.node, 'rotate', {0: 0.0, 350: 360.0}, loop=True)
        obj = bsUtils.Image(self.getIconTexture(True),
                            position=(-180, 60+yOffs),
                            attach='bottomCenter',
                            front=True,
                            vrDepth=baseVRDepth-10,
                            transition='inBottom',
                            transitionDelay=inTime,
                            transitionOutDelay=outTime,
                            scale=(100, 100)).autoRetain()
        objs.append(obj)
        obj.node.hostOnly = True

        # flash
        color = self.getIconColor(True)
        c = bs.newNode('combine', owner=obj.node, attrs={'size': 3})
        keys = {
            inTime: 1.0 * color[0],
            inTime + 400: 1.5 * color[0],
            inTime + 500: 6.0 * color[0],
            inTime + 600: 1.5 * color[0],
            inTime + 2000: 1.0 * color[0]}
        bsUtils.animate(c, 'input0', keys)
        keys = {
            inTime: 1.0 * color[1],
            inTime + 400: 1.5 * color[1],
            inTime + 500: 6.0 * color[1],
            inTime + 600: 1.5 * color[1],
            inTime + 2000: 1.0 * color[1]}
        bsUtils.animate(c, 'input1', keys)
        keys = {
            inTime: 1.0 * color[2],
            inTime + 400: 1.5 * color[2],
            inTime + 500: 6.0 * color[2],
            inTime + 600: 1.5 * color[2],
            inTime + 2000: 1.0 * color[2]}
        bsUtils.animate(c, 'input2', keys)
        c.connectAttr('output', obj.node, 'color')

        obj = bsUtils.Image(bs.getTexture('achievementOutline'),
                            modelTransparent=bs.getModel('achievementOutline'),
                            position=(-180, 60+yOffs),
                            front=True,
                            attach='bottomCenter',
                            vrDepth=baseVRDepth,
                            transition='inBottom',
                            transitionDelay=inTime,
                            transitionOutDelay=outTime,
                            scale=(100, 100)).autoRetain()
        obj.node.hostOnly = True

        # flash
        color = (2, 1.4, 0.4, 1)
        c = bs.newNode('combine', owner=obj.node, attrs={'size': 3})
        keys = {
            inTime: 1.0 * color[0],
            inTime + 400: 1.5 * color[0],
            inTime + 500: 6.0 * color[0],
            inTime + 600: 1.5 * color[0],
            inTime + 2000: 1.0 * color[0]}
        bsUtils.animate(c, 'input0', keys)
        keys = {
            inTime: 1.0 * color[1],
            inTime + 400: 1.5 * color[1],
            inTime + 500: 6.0 * color[1],
            inTime + 600: 1.5 * color[1],
            inTime + 2000: 1.0 * color[1]}
        bsUtils.animate(c, 'input1', keys)
        keys = {
            inTime: 1.0 * color[2],
            inTime + 400: 1.5 * color[2],
            inTime + 500: 6.0 * color[2],
            inTime + 600: 1.5 * color[2],
            inTime + 2000: 1.0 * color[2]}
        bsUtils.animate(c, 'input2', keys)
        c.connectAttr('output', obj.node, 'color')
        objs.append(obj)

        obj = bsUtils.Text(
            bs.Lstr(
                value='${A}:',
                subs=[('${A}', bs.Lstr(resource='achievementText'))]),
            position=(-120, 91 + yOffs),
            front=True, vAttach='bottom', vrDepth=baseVRDepth - 10,
            transition='inBottom', flatness=0.5, transitionDelay=inTime,
            transitionOutDelay=outTime, color=(1, 1, 1, 0.8),
            scale=0.65).autoRetain()
        objs.append(obj)
        obj.node.hostOnly = True

        obj = bsUtils.Text(self.getDisplayString(),
                           position=(-120, 50+yOffs),
                           front=True,
                           vAttach='bottom',
                           transition='inBottom',
                           vrDepth=baseVRDepth,
                           flatness=0.5,
                           transitionDelay=inTime,
                           transitionOutDelay=outTime,
                           flash=True,
                           color=(1, 0.8, 0, 1.0),
                           scale=1.5).autoRetain()
        objs.append(obj)
        obj.node.hostOnly = True

        obj = bsUtils.Text(bs.getSpecialChar('ticket'),
                           position=(-120-170+5, 75+yOffs-20),
                           front=True,
                           vAttach='bottom',
                           hAlign='center', vAlign='center',
                           transition='inBottom',
                           vrDepth=baseVRDepth,
                           transitionDelay=inTime,
                           transitionOutDelay=outTime,
                           flash=True,
                           color=(0.5, 0.5, 0.5, 1),
                           scale=3.0).autoRetain()
        objs.append(obj)
        obj.node.hostOnly = True

        obj = bsUtils.Text('+'+str(self.getAwardTicketValue()),
                           position=(-120-180+5, 80+yOffs-20),
                           vAttach='bottom',
                           front=True,
                           hAlign='center', vAlign='center',
                           transition='inBottom',
                           vrDepth=baseVRDepth,
                           flatness=0.5,
                           shadow=1.0,
                           transitionDelay=inTime,
                           transitionOutDelay=outTime,
                           flash=True,
                           color=(0, 1, 0, 1),
                           scale=1.5).autoRetain()
        objs.append(obj)
        obj.node.hostOnly = True

        # add the 'x 2' if we've got pro
        if bsUtils._havePro():
            obj = bsUtils.Text('x 2',
                               position=(-120-180+45, 80+yOffs-50),
                               vAttach='bottom',
                               front=True,
                               hAlign='center', vAlign='center',
                               transition='inBottom',
                               vrDepth=baseVRDepth,
                               flatness=0.5,
                               shadow=1.0,
                               transitionDelay=inTime,
                               transitionOutDelay=outTime,
                               flash=True,
                               color=(0.4, 0, 1, 1),
                               scale=0.9).autoRetain()
            objs.append(obj)
            obj.node.hostOnly = True

        obj = bsUtils.Text(self.getDescriptionComplete(),
                           position=(-120, 30+yOffs),
                           front=True,
                           vAttach='bottom',
                           transition='inBottom',
                           vrDepth=baseVRDepth-10,
                           flatness=0.5,
                           transitionDelay=inTime,
                           transitionOutDelay=outTime,
                           color=(1.0, 0.7, 0.5, 1.0),
                           scale=0.8).autoRetain()
        objs.append(obj)
        obj.node.hostOnly = True

        for obj in objs:
            bs.gameTimer(
                outTime+1000, bs.WeakCall(obj.handleMessage, bs.DieMessage()))


# 5
gAchievements.append(
    Achievement('In Control', 'achievementInControl',
                (1, 1, 1), '', 5))
# 15
gAchievements.append(
    Achievement('Sharing is Caring', 'achievementSharingIsCaring',
                (1, 1, 1), '', 15))
# 10
gAchievements.append(
    Achievement('Dual Wielding', 'achievementDualWielding',
                (1, 1, 1), '', 10))

# 10
gAchievements.append(
    Achievement('Free Loader', 'achievementFreeLoader',
                (1, 1, 1), '', 10))
# 20
gAchievements.append(
    Achievement('Team Player', 'achievementTeamPlayer',
                (1, 1, 1), '', 20))

# 5
gAchievements.append(
    Achievement('Onslaught Training Victory', 'achievementOnslaught',
                (1, 1, 1), 'Default:Onslaught Training', 5))
# 5
gAchievements.append(
    Achievement('Off You Go Then', 'achievementOffYouGo',
                (1, 1.1, 1.3), 'Default:Onslaught Training', 5))
# 10
gAchievements.append(
    Achievement('Boxer', 'achievementBoxer',
                (1, 0.6, 0.6), 'Default:Onslaught Training', 10,
                hardModeOnly=True))

# 10
gAchievements.append(
    Achievement('Rookie Onslaught Victory', 'achievementOnslaught',
                (0.5, 1.4, 0.6), 'Default:Rookie Onslaught', 10))
# 10
gAchievements.append(
    Achievement('Mine Games', 'achievementMine',
                (1, 1, 1.4), 'Default:Rookie Onslaught', 10))
# 15
gAchievements.append(
    Achievement('Flawless Victory', 'achievementFlawlessVictory',
                (1, 1, 1), 'Default:Rookie Onslaught', 15, hardModeOnly=True))

# 10
gAchievements.append(
    Achievement('Rookie Football Victory', 'achievementFootballVictory',
                (1.0, 1, 0.6), 'Default:Rookie Football', 10))
# 10
gAchievements.append(
    Achievement('Super Punch', 'achievementSuperPunch',
                (1, 1, 1.8), 'Default:Rookie Football', 10))
# 15
gAchievements.append(
    Achievement('Rookie Football Shutout', 'achievementFootballShutout',
                (1, 1, 1), 'Default:Rookie Football', 15, hardModeOnly=True))

# 15
gAchievements.append(
    Achievement('Pro Onslaught Victory', 'achievementOnslaught',
                (0.3, 1, 2.0), 'Default:Pro Onslaught', 15))
# 15
gAchievements.append(
    Achievement('Boom Goes the Dynamite', 'achievementTNT',
                (1.4, 1.2, 0.8), 'Default:Pro Onslaught', 15))
# 20
gAchievements.append(
    Achievement('Pro Boxer', 'achievementBoxer',
                (2, 2, 0), 'Default:Pro Onslaught', 20, hardModeOnly=True))

# 15
gAchievements.append(
    Achievement('Pro Football Victory', 'achievementFootballVictory',
                (1.3, 1.3, 2.0), 'Default:Pro Football', 15))
# 15
gAchievements.append(
    Achievement('Super Mega Punch', 'achievementSuperPunch',
                (2, 1, 0.6), 'Default:Pro Football', 15))
# 20
gAchievements.append(
    Achievement('Pro Football Shutout', 'achievementFootballShutout',
                (0.7, 0.7, 2.0), 'Default:Pro Football', 20, hardModeOnly=True))

# 15
gAchievements.append(
    Achievement('Pro Runaround Victory', 'achievementRunaround',
                (1, 1, 1), 'Default:Pro Runaround', 15))
# 20
gAchievements.append(
    Achievement('Precision Bombing', 'achievementCrossHair',
                (1, 1, 1.3), 'Default:Pro Runaround', 20, hardModeOnly=True))
# 25
gAchievements.append(
    Achievement('The Wall', 'achievementWall',
                (1, 0.7, 0.7), 'Default:Pro Runaround', 25, hardModeOnly=True))

# 30
gAchievements.append(
    Achievement('Uber Onslaught Victory', 'achievementOnslaught',
                (2, 2, 1), 'Default:Uber Onslaught', 30))
# 30
gAchievements.append(
    Achievement('Gold Miner', 'achievementMine',
                (2, 1.6, 0.2), 'Default:Uber Onslaught', 30, hardModeOnly=True))
# 30
gAchievements.append(
    Achievement('TNT Terror', 'achievementTNT',
                (2, 1.8, 0.3), 'Default:Uber Onslaught', 30, hardModeOnly=True))

# 30
gAchievements.append(
    Achievement('Uber Football Victory', 'achievementFootballVictory',
                (1.8, 1.4, 0.3), 'Default:Uber Football', 30))
# 30
gAchievements.append(
    Achievement('Got the Moves', 'achievementGotTheMoves',
                (2, 1, 0), 'Default:Uber Football', 30, hardModeOnly=True))
# 40
gAchievements.append(
    Achievement('Uber Football Shutout', 'achievementFootballShutout',
                (2, 2, 0), 'Default:Uber Football', 40, hardModeOnly=True))

# 30
gAchievements.append(
    Achievement('Uber Runaround Victory', 'achievementRunaround',
                (1.5, 1.2, 0.2), 'Default:Uber Runaround', 30))
# 40
gAchievements.append(
    Achievement(
        'The Great Wall', 'achievementWall', (2, 1.7, 0.4),
        'Default:Uber Runaround', 40, hardModeOnly=True))
# 40
gAchievements.append(
    Achievement('Stayin\' Alive', 'achievementStayinAlive',
                (2, 2, 1), 'Default:Uber Runaround', 40, hardModeOnly=True))

# 20
gAchievements.append(
    Achievement('Last Stand Master', 'achievementMedalSmall',
                (2, 1.5, 0.3), 'Default:The Last Stand', 20, hardModeOnly=True))
# 40
gAchievements.append(
    Achievement('Last Stand Wizard', 'achievementMedalMedium',
                (2, 1.5, 0.3), 'Default:The Last Stand', 40, hardModeOnly=True))
# 60
gAchievements.append(
    Achievement('Last Stand God', 'achievementMedalLarge',
                (2, 1.5, 0.3), 'Default:The Last Stand', 60, hardModeOnly=True))

# 5
gAchievements.append(
    Achievement('Onslaught Master', 'achievementMedalSmall',
                (0.7, 1, 0.7), 'Challenges:Infinite Onslaught', 5))
# 15
gAchievements.append(
    Achievement('Onslaught Wizard', 'achievementMedalMedium',
                (0.7, 1.0, 0.7), 'Challenges:Infinite Onslaught', 15))
# 30
gAchievements.append(
    Achievement('Onslaught God', 'achievementMedalLarge',
                (0.7, 1.0, 0.7), 'Challenges:Infinite Onslaught', 30))

# 5
gAchievements.append(
    Achievement( 'Runaround Master', 'achievementMedalSmall',
                 (1.0, 1.0, 1.2), 'Challenges:Infinite Runaround', 5))
# 15
gAchievements.append(
    Achievement('Runaround Wizard', 'achievementMedalMedium',
                (1.0, 1.0, 1.2), 'Challenges:Infinite Runaround', 15))
# 30
gAchievements.append(
    Achievement('Runaround God', 'achievementMedalLarge',
                (1.0, 1.0, 1.2), 'Challenges:Infinite Runaround', 30))


# just a test...
def _test():

    def foo():
        gAchievements[0].announceCompletion()
        gAchievements[1].announceCompletion()
        gAchievements[2].announceCompletion()

    def foo2():
        gAchievements[3].announceCompletion()
        gAchievements[4].announceCompletion()
        gAchievements[5].announceCompletion()

    bs.netTimer(3000, foo)
    bs.netTimer(7000, foo2)
