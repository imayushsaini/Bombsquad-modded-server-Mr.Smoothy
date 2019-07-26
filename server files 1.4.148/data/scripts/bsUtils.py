import bs
import weakref
import os
import sys
import thread
import threading
import time
import random
import urllib
import urllib2
import ast
import gc
import types
import copy
import bsInternal
import bsGame
import json

# even when kiosk mode is set, we want behavior to differ depending on
# whether we launch games from the kiosk menu or the real one
# (hence the need for this dynamic var)
gRunningKioskModeGame = bs.getEnvironment()['kioskMode']
gConfigFileIsHealthy = False

# this is incremented any time the app is backgrounded/foregrounded;
# can be a simple way to determine if network data should be refreshed/etc.
gAppFGState = 0
_gServerConfig = {}

# NOTE: player color options are enforced server-side for non-pro accounts
# so don't change these or they won't stick...
_gPlayerColors = [
    (1, 0.15, 0.15), (0.2, 1, 0.2), (0.1, 0.1, 1), (0.2, 1, 1),
    (0.5, 0.25, 1.0), (1, 1, 0), (1, 0.5, 0), (1, 0.3, 0.5),
    (0.1, 0.1, 0.5), (0.4, 0.2, 0.1), (0.1, 0.35, 0.1), (1, 0.8, 0.5),
    (0.4, 0.05, 0.05), (0.13, 0.13, 0.13), (0.5, 0.5, 0.5), (1, 1, 1)]
gMusic = None
_gConfig = None

gNodeOwnerWeakRefs = []
gNodeOwnerWeakRefsCleanCounter = 0
gPrintOnceErrors = set()

class Lstr(object):
    """
    category: General Utility Classes

    Used to specify strings in a language-independent way.
    These should be used whenever possible in place of hard-coded strings
    so that in-game or UI elements show up correctly on all clients in their
    currently-active language.

    To see available resource keys, look at any of the bsLanguage*.py files
    in the game or the translations pages at bombsquadgame.com/translate.

    # EXAMPLE 1: specify a string from a resource path
    myNode.text = bs.Lstr(resource='audioSettingsWindow.titleText')

    # EXAMPLE 2: specify a translated string via a category and english value;
    # if a translated value is available, it will be used; otherwise the english
    # value will be. To see available translation categories, look under the
    # 'translations' resource section.
    myNode.text = bs.Lstr(translate=('gameDescriptions', 'Defeat all enemies'))

    # EXAMPLE 3: specify a raw value and some substitutions.  Substitutions can
    # be used with resource and translate modes as well.
    myNode.text = bs.Lstr(value='${A} / ${B}',
                          subs=[('${A}', str(score)), ('${B}', str(total))])

    # EXAMPLE 4: Lstrs can be nested.  This example would display the resource
    # at resPathA but replace ${NAME} with the value of the resource at resPathB
    myTextNode.text = bs.Lstr(resource='resPathA',
                              subs=[('${NAME}', bs.Lstr(resource='resPathB'))])
    """
    def __init__(self, *args, **keywds):
        """
        Instantiate a Lstr; pass a value for either 'resource', 'translate',
        or 'value'. (see Lstr help for examples).
        'subs' can be a sequence of 2-member sequences consisting of values
        and replacements.
        'fallbackResource' can be a resource key that will be used if the
        main one is not present for
        the current language in place of falling back to the english value
        ('resource' mode only).
        'fallbackValue' can be a literal string that will be used if neither
        the resource nor the fallback resource is found ('resource' mode only).
        """
        if args: raise Exception('Lstr accepts only keyword arguments')
        # Basically just store the exact args they passed.
        # ...however if they passed any Lstr values for subs,
        # replace them with that Lstr's dict
        self._args = keywds
        ourType = type(self)

        if type(self._args.get('value')) is ourType:
            raise Exception("'value' must be a regular string; not an Lstr")
        
        if 'subs' in self._args:
            subsNew = []
            for key, value in keywds['subs']:
                if type(value) is type(self):
                    subsNew.append((key, value._args))
                else:
                    subsNew.append((key, value))
            self._args['subs'] = subsNew

        # as of protocol 31 we support compact key names
        # ('t' instead of 'translate', etc). Convert as needed.
        if 'translate' in keywds:
            keywds['t'] = keywds['translate']
            del keywds['translate']
        if 'resource' in keywds:
            keywds['r'] = keywds['resource']
            del keywds['resource']
        if 'value' in keywds:
            keywds['v'] = keywds['value']
            del keywds['value']
        if 'fallback' in keywds:
            printErrorOnce('deprecated "fallback" arg passed to Lstr(); use '
                           'either "fallbackResource" or "fallbackValue"')
            keywds['f'] = keywds['fallback']
            del keywds['fallback']
        if 'fallbackResource' in keywds:
            keywds['f'] = keywds['fallbackResource']
            del keywds['fallbackResource']
        if 'subs' in keywds:
            keywds['s'] = keywds['subs']
            del keywds['subs']
        if 'fallbackValue' in keywds:
            keywds['fv'] = keywds['fallbackValue']
            del keywds['fallbackValue']
        
    def evaluate(self):
        """
        Evaluates the Lstr and returns a flat string in the current language.
        You should avoid doing this as much as possible and instead pass
        and store Lstr values.
        """
        return bsInternal._evaluateLstr(self._getJson())

    def isFlatValue(self):
        """
        Returns true if the Lstr is a simple string value with no translations,
        resources, or substitutions.  In this case it is reasonable to replace
        it with a simple flattened string or do string manipulation on it.
        """
        return True if ('v' in self._args
                        and not self._args.get('s', [])) else False
    
    def _getJson(self):
        try:
            return uni(json.dumps(self._args, separators=(',', ':')))
        except Exception:
            bs.printException('_getJson failed for', self._args)
            return u'JSON_ERR'

    def __str__(self):
        return '<bs.Lstr: '+self._getJson()+'>'

    def __repr__(self):
        return '<bs.Lstr: '+self._getJson()+'>'
    
    
def printException(*args, **keywds):
    """
    category: General Utility Functions

    Prints all arguments provided along with various info about the
    current context and the outstanding exception.
    """
    if len(keywds) > 0:
        raise Exception("keyword args not allowed")
    try:
        import traceback
        errStr = ' '.join([unicode(a) for a in args])
        print 'ERROR:', errStr
        bsInternal._printContext()
        print 'Traceback for bs.printException() call (most recent call last):'
        traceback.print_stack()
        traceback.print_exc()
    except Exception:
        print 'ERROR: exception in bs.printException():'
        traceback.print_exc()

def printError(*args, **keywds):
    """
    category: General Utility Functions

    Prints all arguments provided along with various info about the
    current context.
    """
    if len(keywds) > 0:
        raise Exception("keyword args not allowed")
    try:
        import traceback
        errStr = ' '.join([str(a) for a in args])
        print 'ERROR:', errStr
        bsInternal._printContext()
        print 'Traceback for bs.printError() call (most recent call last):'
        traceback.print_stack()
    except Exception:
        print 'ERROR: exception in bs.printError():'
        traceback.print_exc()

gErrorsPrinted = set()

def printErrorOnce(*args, **keywds):
    """
    category: General Utility Functions

    A convenience wrapper to bs.printError()
    that only prints each unique error one time
    (uniqueness is based only on the arguments passed)
    """
    errStr = ' '.join([str(a) for a in args])
    if errStr not in gErrorsPrinted:
        gErrorsPrinted.add(errStr)
        printError(*args, **keywds)
        
def getConfig():
    """
    category: General Utility Functions

    Returns a dict representing BombSquad's persistent config data.
    Be very careful to only put simple values in here that
    can be passed to json dumps/loads.
    This data gets committed to disk/cloud/etc when you call bs.writeConfig().
    """
    return _gConfig

def getSharedObject(name):
    """
    category: Game Flow Functions

    Returns a predefined node/material/texture/etc for the current activity,
    creating it if necessary.
    Available Values:

    'globals': returns the 'globals' bs.Node, containing various global controls
               & values.

    'objectMaterial': a bs.Material that should be applied to any small, normal,
                      physical objects such as bombs, boxes, players, etc. Other
                      materials often check for the  presence of this material
                      as a prerequisite for performing certain actions (such as
                      disabling collisions between initially-overlapping
                      objects)

    'playerMaterial': a bs.Material to be applied to player parts.  Generally,
                      materials related to the process of scoring when reaching
                      a goal, etc will look for the presence of this material
                      on things that hit them.

    'pickupMaterial': a bs.Material; collision shapes used for picking things
                      up will have this material applied. To prevent an object
                      from being picked up, you can add a material that disables
                      collisions against things containing this material.

    'footingMaterial': anything that can be 'walked on' should have this
                       bs.Material applied; generally just terrain and whatnot.
                       A character will snap upright whenever touching something
                       with this material so it should not be applied to props,
                       etc.

    'attackMaterial':  a bs.Material applied to explosion shapes, punch shapes,
                       etc.  An object not wanting to recieve impulse/etc
                       messages can disable collisions against this material.

    'deathMaterial':  a bs.Material that sends a bs.DieMessage() to anything
                      that touches it; handy for terrain below a cliff, etc.

    'regionMaterial':  a bs.Material used for non-physical collision shapes
                       (regions); collisions can generally be allowed with this
                       material even when initially overlapping since it is not
                       physical.

    'railingMaterial': a bs.Material with a very low friction/stiffness/etc that
                       can be applied to invisible 'railings' useful for gently
                       keeping characters from falling off of cliffs.
    """
    # grab current activity or session
    activity = bs.getActivity(exceptionOnNone=False)
    if activity is not None:

        # grab shared-objs dict (creating if necessary)
        try: sharedObjs = activity._sharedObjects
        except Exception: sharedObjs = activity._sharedObjects = {}

        # grab item out of it
        try: return sharedObjs[name]
        except Exception: pass

        # hmm looks like it doesn't yet exist; create it if its a valid value
        if name == 'globals':
            obj = bs.newNode('globals')
        elif name in ['objectMaterial', 'playerMaterial', 'pickupMaterial',
                      'footingMaterial', 'attackMaterial']:
            obj = bs.Material()
        elif name == 'deathMaterial':
            obj = bs.Material()
            obj.addActions(('message', 'theirNode',
                            'atConnect', bs.DieMessage()))
        elif name == 'regionMaterial':
            obj = bs.Material()
        elif name == 'railingMaterial':
            obj = bs.Material()
            obj.addActions(('modifyPartCollision', 'collide', False))
            obj.addActions(('modifyPartCollision', 'stiffness', 0.003))
            obj.addActions(('modifyPartCollision', 'damping', 0.00001))
            obj.addActions(conditions=('theyHaveMaterial',
                                       bs.getSharedObject('playerMaterial')),
                           actions=(('modifyPartCollision', 'collide', True),
                                    ('modifyPartCollision', 'friction', 0.0)))
        else:
            raise Exception("unrecognized shared object (activity context): '"
                            +name+"'")
    else:
        session = bs.getSession(exceptionOnNone=False)
        if session is not None:
            # grab shared-objs dict (creating if necessary)
            try: sharedObjs = session._sharedObjects
            except Exception: sharedObjs = session._sharedObjects = {}

            # grab item out of it
            try: return sharedObjs[name]
            except Exception: pass

            # hmm looks like it doesn't yet exist; create if its a valid value
            if name == 'globals':
                obj = bs.newNode('sessionGlobals')
            else:
                raise Exception("unrecognized shared object "
                                "(session context): '" + name + "'")
        else:
            raise Exception("no current activity or session context")

    # ok, got a shiny new shared obj; store it for quick access next time
    sharedObjs[name] = obj
    return obj
    
def getHumanReadableUserScriptsPath():
    "Return a human readable path to user-scripts (NOT a valid filesystem path)"
    env = bs.getEnvironment()
    path = env['userScriptsDirectory']
    if path is None: return '<Not Available>'
    # on newer versions of android, the user's external storage dir is probably
    # only visible to the user's processes and thus not really useful printed
    # in its entirety; lets print it as <External Storage>/myfilepath
    if env['platform'] == 'android':
        extStoragePath = bsInternal._androidGetExternalStoragePath()
        if (extStoragePath is not None
                and env['userScriptsDirectory'].startswith(extStoragePath)):
            path = ('<'+bs.Lstr(resource='externalStorageText').evaluate()
                    +'>'+env['userScriptsDirectory'][len(extStoragePath):])
    return path
    
def showUserScripts():
    "Open or at least nicely print the location of the user-scripts directory"
    env = bs.getEnvironment()

    # first off, if we need permission for this, ask for it.
    if not bsInternal._havePermission("storage"):
        bs.playSound(bs.getSound('error'))
        bs.screenMessage(bs.Lstr(resource='storagePermissionAccessText'),
                         color=(1, 0, 0))
        bsInternal._requestPermission("storage")
        return

    # secondly, if the dir doesn't exist, attempt to make it
    if not os.path.exists(env['userScriptsDirectory']):
        os.makedirs(env['userScriptsDirectory'])

    # on android, attempt to write a file in their user-scripts dir telling
    # them about modding (this also has the side-effect of allowing us to
    # media-scan that dir so it shows up in android-file-transfer, since it
    # doesn't seem like theres a way to inform the media scanner of an empty
    # directory, (which means they would have to reboot their device before
    # they can see it)
    if env['platform'] == 'android':
        try:
            usd = env['userScriptsDirectory']
            if usd is not None and os.path.isdir(usd):
                fileName = usd+'/aboutThisFolder.txt'
                f = open(fileName, 'wb')
                f.write('You can drop files in here to mod BombSquad.  '
                        'See settings/advanced in the game for more info.')
                f.close()
                bs.androidMediaScanFile(fileName)
        except Exception:
            bs.printException('error writing aboutThisFolder stuff')
        
    # on a few platforms we try to open the dir in the UI
    if env['platform'] in ['mac', 'windows']:
        bsInternal._openDirExternally(env['userScriptsDirectory'])
        
    # otherwise we just print a pretty version of it
    else:
        bs.screenMessage(getHumanReadableUserScriptsPath())

def createUserSystemScripts():
    """Sets up a copy of BombSquad system scripts under your user scripts dir
    that you can edit and experiment with."""
    import shutil
    path = (bs.getEnvironment()['userScriptsDirectory']
            + '/sys/'+bs.getEnvironment()['version'])
    if os.path.exists(path): shutil.rmtree(path)
    if os.path.exists(path+"_tmp"): shutil.rmtree(path+"_tmp")
    try:
        os.makedirs(path+'_tmp')
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path+"_tmp"): pass
        else: raise

    # shutil.copytree doesn't seem to work nicely on android,
    # so lets do it manually
    srcDir = bs.getEnvironment()['systemScriptsDirectory']
    dstDir = path+"_tmp"
    files = os.listdir(bs.getEnvironment()['systemScriptsDirectory'])
    for f in files:
        print 'COPYING', srcDir+'/'+f, '->', dstDir
        shutil.copyfile(srcDir+'/'+f, dstDir+'/'+f)

    print 'MOVING', path+"_tmp", path
    shutil.move(path+"_tmp", path)
    print 'Created system scripts at :\'' + path + \
        '\'\nRestart BombSquad to use them. (use bs.quit() to exit the game)'
    if bs.getEnvironment()['platform'] == 'android':
        print ('Note: the new files may not be visible via '
               'android-file-transfer until you restart your device.')

def deleteUserSystemScripts():
    'Cleans out the scripts created by createUserSystemScripts()'
    import shutil
    path = bs.getEnvironment()['userScriptsDirectory'] + \
        '/sys/' + bs.getEnvironment()['version']
    if os.path.exists(path):
        shutil.rmtree(path)
        print ('User system scripts deleted.\nRestart BombSquad to use internal'
               ' scripts. (use bs.quit() to exit the game)')
    else:
        print 'User system scripts not found.'
    # if the sys path is empty, kill it
    d = bs.getEnvironment()['userScriptsDirectory']+'/sys'
    if os.path.isdir(d) and len(os.listdir(d)) == 0:
        os.rmdir(d)
    if 'android' in bs.getEnvironment()['userAgentString']:
        bs.androidRefreshFiles() # get android file transfer to reflect this

class WeakCall(object):
    """
    category: General Utility Classes

    Wraps a callable and arguments into a single callable object.
    When passed a bound method as the callable, the instance portion
    of it is weak-referenced, meaning the underlying instance is
    free to die if all other references to it go away. Should this
    occur, calling the WeakCall is simply a no-op.

    Think of this as a handy way to tell an object to do something
    at some point in the future if it happens to still exist.

    # EXAMPLE A: this code will create a FooClass instance and call its
    # bar() method 5 seconds later; it will be kept alive even though
    # we overwrite its variable with None because the bound method
    # we pass as a timer callback (foo.bar) strong-references it
    foo = FooClass()
    bs.gameTimer(length=1000, call=foo.bar)
    foo = None

    # EXAMPLE B: this code will *not* keep our object alive; it will die
    # when we overwrite it with None and its bar() method won't get called
    foo = FooClass()
    bs.gameTimer(length=1000, call=bs.WeakCall(foo.bar))
    foo = None

    Note: additional args and keywords you provide to the WeakCall()
    constructor are stored as regular strong-references; you'll need
    to wrap them in weakrefs manually if desired.
    """
    def __init__(self, *args, **keywds):
        """
        Instantiate a WeakCall; pass a callable as the first
        arg, followed by any number of arguments or keywords.

        # example: wrap a method call with some positional and keyword args:
        myCallable = bs.WeakCall(myObj.doStuff, argVal, namedArg=anotherVal)

        # now we have a single callable to run that whole mess..
        # this is the same as calling myObj.doStuff(argVal, namedArg=anotherVal)
        # (provided myObj still exists; this will do nothing otherwise)
        myCallable()
        """
        if hasattr(args[0], 'im_func'): self._call = WeakMethod(args[0])
        else:
            global _gDidWeakCallWarning
            try: did = _gDidWeakCallWarning
            except Exception: did = False
            if not did:
                print ('Warning: callable passed to bs.WeakCall() is not'
                       ' weak-referencable (' + str(args[0]) +
                       '); use bs.Call() instead to avoid this '
                       'warning. Stack-trace:')
                import traceback
                traceback.print_stack()
                _gDidWeakCallWarning = True
            self._call = args[0]
        self._args = args[1:]
        self._keywds = keywds
    def __call__(self, *argsExtra):
        return self._call(*self._args + argsExtra, **self._keywds)
    def __str__(self):
        return ('<bs.WeakCall object; _call='+str(self._call)
                + ' _args=' + str(self._args) +' _keywds='
                + str(self._keywds)+'>')

class Call(object):
    """
    category: General Utility Classes

    Wraps a callable and arguments into a single callable object.
    The callable is strong-referenced so it won't die until this object does.
    Note that a bound method (ex: myObj.doSomething) contains a reference
    to the 'self' object, so you will be keeping that object alive too.
    Use bs.WeakCall if you want to pass a callback without keeping things alive.
    """
    def __init__(self, *args, **keywds):
        """
        Instantiate a Call; pass a callable as the first
        arg, followed by any number of arguments or keywords.

        # example: wrap a method call with 1 positional and 1 keyword arg
        myCallable = bs.Call(myObj.doStuff, argVal, namedArg=anotherVal)

        # now we have a single callable to run that whole mess
        # this is the same as calling myObj.doStuff(argVal, namedArg=anotherVal)
        myCallable()
        """

        self._call = args[0]
        self._args = args[1:]
        self._keywds = keywds
    def __call__(self, *argsExtra):
        return self._call(*self._args+argsExtra, **self._keywds)
    def __str__(self):
        return ('<bs.Call object; _call=' + str(self._call) + ' _args='
                + str(self._args) + ' _keywds=' + str(self._keywds) +'>')
    
class WeakMethod :
    """ wraps a bound method using weak references so that the original is
    free to die. If called with a dead target, is simply a no-op """
    def __init__( self , f ) :
        self.f = f.im_func
        self.c = weakref.ref( f.im_self )
    def __call__( self , *args, **keywds ) :
        c = self.c()
        if c is None : return
        return self.f(*((c,)+args), **keywds)
    def __str__(self):
        return '<bs.WeakMethod object; call='+str(self.f)+'>'
    
_gLanguageTarget = None
_gLanguageMerged = None

def _getLanguages():
    langs = set()
    env = bs.getEnvironment()
    for i, d in enumerate([env['systemScriptsDirectory'],
                          env['userScriptsDirectory']]):
        try: names = os.listdir(d)
        except Exception: names = []
        for name in names:
            if name.startswith('bsLanguage') and name.endswith('.py'):
                langName = name[10:-3]
                if _canDisplayLanguage(langName):
                    langs.add(langName)
    vals = list(langs)
    vals.sort()
    return vals

def _ensureHaveAccountPlayerProfile():

    # this only applies when we're signed in..
    if bsInternal._getAccountState() != 'SIGNED_IN':
        return

    # if the short version of our account name currently cant be
    # displayed by the game, cancel..
    if not bsInternal._haveChars(
            bsInternal._getAccountDisplayString(full=False)): return
    
    config = bs.getConfig()
    
    if ('Player Profiles' not in config
        or '__account__' not in config['Player Profiles']):
        # create a spaz with a nice default purply color
        bsInternal._addTransaction({'type':'ADD_PLAYER_PROFILE',
                                    'name':'__account__',
                                    'profile':{'character':'Spaz',
                                               'color':(0.5, 0.25, 1.0),
                                               'highlight':(0.5, 0.25, 1.0)}})
        bsInternal._runTransactions()
    
# used internally
def _handleRemoteAchievementList(completedAchievements):
    import bsAchievement
    bsAchievement.setCompletedAchievements(completedAchievements)
    
def _getRemoteAppName():
    env = bs.getEnvironment()
    # on ali we point at their custom app instead of BSRemote
    if env['platform'] == 'android' and env['subplatform'] == 'alibaba':
        return u'\u963f\u91cc\u7535\u89c6'
    else:
        return bs.Lstr(resource='remote_app.app_name')
    
def _shouldSubmitDebugInfo():
    try: return bs.getConfig()['Submit Debug Info']
    except Exception: return True

def _handleAppPause():
    pass

def _handleAppResume():
    # if there's music playing externally, make sure we aren't playing ours
    import bsUtils
    import bsInternal
    import bsUI
    if bsInternal._isOSPlayingMusic():
        _playMusic(None)
    global gAppFGState
    gAppFGState += 1
    # mark our cached tourneys as invalid so anyone using them knows
    # they might be out of date
    for entry in bsUI.gTournamentInfo.values():
        entry['valid'] = False

# high level way to launch a challenge game locally
def _handleRunChallengeGame(game, force=False, args={}):
    import bsCoopGame
    import bsUI
    if game == '': raise Exception("empty game name")
    campaignName, levelName = game.split(':')
    campaign = bsCoopGame.getCampaign(campaignName)
    levels = campaign.getLevels()
    
    # if this campaign is sequential, make sure we've completed the
    # one before this
    if campaign.isSequential() and not force:
        for i in range(len(levels)):
            if levels[i].getName() == levelName:
                break
            if not levels[i].getComplete():
                bsUI.LockedErrorWindow(campaign.getLevel(levelName)\
                                       .getDisplayString(),
                                       campaign.getLevel(levels[i].getName())\
                                       .getDisplayString())
                return False

    # ok we're good to go..
    bsUI.gCoopSessionArgs = {'campaign':campaignName, 'level':levelName}
    for argName, argVal in args.items():
        bsUI.gCoopSessionArgs[argName] = argVal
    
    def _fadeEnd():
        import bsCoopGame
        try: bsInternal._newHostSession(bsCoopGame.CoopSession)
        except Exception:
            bs.printException()
            import bsMainMenu
            bsInternal._newHostSession(bsMainMenu.MainMenuSession)
            
    bsInternal._fadeScreen(False, time=250, endCall=_fadeEnd)
    return True

def openURL(address, *args, **keywds):
    """
    category: General Utility Functions

    Open the provided url in a web-browser, or display the URL
    string in a window if that isn't possible.
    """
    bsInternal._openURL(address, *args, **keywds)

def isBrowserLikelyAvailable():
    """
    category: General Utility Functions

    Returns whether or not a web-browser is likely to be available
    on the current device.  If this returns False you may want to
    avoid calling bs.showURL() with any lengthy addresses.
    (bs.showURL() will display an address as a string in a window
    if unable to bring up a browser, but that is only useful for
    simple URLs.)
    """

    env = bs.getEnvironment()
    platform = env['platform']
    subplatform = env['subplatform']
    touchscreen = bsInternal._getInputDevice('TouchScreen', '#1',
                                             exceptionOnNone=False)
    
    # ouya has a browser... but its sucks so lets say no.
    if platform == 'android' and subplatform == 'ouya': return False
    
    # if we're on a vr device or an android device with no touchscreen,
    # assume no browser
    if env['vrMode'] or (platform == 'android' and touchscreen is None):
        return False

    # anywhere else assume we've got one
    return True
    
def _getDefaultFreeForAllPlaylist():
    return [
         {
            'settings':{
               'Epic Mode':False,
               'Kills to Win Per Player':10,
               'Respawn Times':1.0,
               'Time Limit':300,
               'map':'Doom Shroom'
            },
            'type':'bsDeathMatch.DeathMatchGame'
         },
         {
            'settings':{
               'Chosen One Gets Gloves':True,
               'Chosen One Gets Shield':False,
               'Chosen One Time':30,
               'Epic Mode':0,
               'Respawn Times':1.0,
               'Time Limit':300,
               'map':'Monkey Face'
            },
            'type':'bsChosenOne.ChosenOneGame'
         },
         {
            'settings':{
               'Hold Time':30,
               'Respawn Times':1.0,
               'Time Limit':300,
               'map':'Zigzag'
            },
            'type':'bsKingOfTheHill.KingOfTheHillGame'
         },
         {
            'settings':{
               'Epic Mode':False,
               'map':'Rampage'
            },
            'type':'bsMeteorShower.MeteorShowerGame'
         },
         {
            'settings':{
               'Epic Mode':1,
               'Lives Per Player':1,
               'Respawn Times':1.0,
               'Time Limit':120,
               'map':'Tip Top'
            },
            'type':'bsElimination.EliminationGame'
         },
         {
            'settings':{
               'Hold Time':30,
               'Respawn Times':1.0,
               'Time Limit':300,
               'map':'The Pad'
            },
            'type':'bsKeepAway.KeepAwayGame'
         },
         {
            'settings':{
               'Epic Mode':True,
               'Kills to Win Per Player':10,
               'Respawn Times':0.25,
               'Time Limit':120,
               'map':'Rampage'
            },
            'type':'bsDeathMatch.DeathMatchGame'
         },
         {
            'settings':{
               'Bomb Spawning':1000,
               'Epic Mode':False,
               'Laps':3,
               'Mine Spawn Interval':4000,
               'Mine Spawning':4000,
               'Time Limit':300,
               'map':'Big G'
            },
            'type':'bsRace.RaceGame'
         },
         {
            'settings':{
               'Hold Time':30,
               'Respawn Times':1.0,
               'Time Limit':300,
               'map':'Happy Thoughts'
            },
            'type':'bsKingOfTheHill.KingOfTheHillGame'
         },
         {
            'settings':{
               'Enable Impact Bombs':1,
               'Enable Triple Bombs':False,
               'Target Count':2,
               'map':'Doom Shroom'
            },
            'type':'bsTargetPractice.TargetPracticeGame'
         },
         {
            'settings':{
               'Epic Mode':False,
               'Lives Per Player':5,
               'Respawn Times':1.0,
               'Time Limit':300,
               'map':'Step Right Up'
            },
            'type':'bsElimination.EliminationGame'
         },
         {
            'settings':{
               'Epic Mode':False,
               'Kills to Win Per Player':10,
               'Respawn Times':1.0,
               'Time Limit':300,
               'map':'Crag Castle'
            },
            'type':'bsDeathMatch.DeathMatchGame'
         },
         {
            'map':'Lake Frigid',
            'settings':{
               'Bomb Spawning':0,
               'Epic Mode':False,
               'Laps':6,
               'Mine Spawning':2000,
               'Time Limit':300,
               'map':'Lake Frigid'
            },
            'type':'bsRace.RaceGame'
         }
      ]

def _getDefaultTeamsPlaylist():
    return [
         {
            'settings':{
               'Epic Mode':False,
               'Flag Idle Return Time':30,
               'Flag Touch Return Time':0,
               'Respawn Times':1.0,
               'Score to Win':3,
               'Time Limit':600,
               'map':'Bridgit'
            },
            'type':'bsCaptureTheFlag.CTFGame'
         },
         {
            'settings':{
               'Epic Mode':False,
               'Respawn Times':1.0,
               'Score to Win':3,
               'Time Limit':600,
               'map':'Step Right Up'
            },
            'type':'bsAssault.AssaultGame'
         },
         {
            'settings':{
               'Balance Total Lives':False,
               'Epic Mode':False,
               'Lives Per Player':3,
               'Respawn Times':1.0,
               'Solo Mode':True,
               'Time Limit':600,
               'map':'Rampage'
            },
            'type':'bsElimination.EliminationGame'
         },
         {
            'settings':{
               'Epic Mode':False,
               'Kills to Win Per Player':5,
               'Respawn Times':1.0,
               'Time Limit':300,
               'map':'Roundabout'
            },
            'type':'bsDeathMatch.DeathMatchGame'
         },
         {
            'settings':{
               'Respawn Times':1.0,
               'Score to Win':1,
               'Time Limit':600,
               'map':'Hockey Stadium'
            },
            'type':'bsHockey.HockeyGame'
         },
         {
            'settings':{
               'Hold Time':30,
               'Respawn Times':1.0,
               'Time Limit':300,
               'map':'Monkey Face'
            },
            'type':'bsKeepAway.KeepAwayGame'
         },
         {
            'settings':{
               'Balance Total Lives':False,
               'Epic Mode':True,
               'Lives Per Player':1,
               'Respawn Times':1.0,
               'Solo Mode':False,
               'Time Limit':120,
               'map':'Tip Top'
            },
            'type':'bsElimination.EliminationGame'
         },
         {
            'settings':{
               'Epic Mode':False,
               'Respawn Times':1.0,
               'Score to Win':3,
               'Time Limit':300,
               'map':'Crag Castle'
            },
            'type':'bsAssault.AssaultGame'
         },
         {
            'settings':{
               'Epic Mode':False,
               'Kills to Win Per Player':5,
               'Respawn Times':1.0,
               'Time Limit':300,
               'map':'Doom Shroom'
            },
            'type':'bsDeathMatch.DeathMatchGame'
         },
         {
            'settings':{
               'Epic Mode':False,
               'map':'Rampage'
            },
            'type':'bsMeteorShower.MeteorShowerGame'
         },
         {
            'settings':{
               'Epic Mode':False,
               'Flag Idle Return Time':30,
               'Flag Touch Return Time':0,
               'Respawn Times':1.0,
               'Score to Win':2,
               'Time Limit':600,
               'map':'Roundabout'
            },
            'type':'bsCaptureTheFlag.CTFGame'
         },
         {
            'settings':{
               'Respawn Times':1.0,
               'Score to Win':21,
               'Time Limit':600,
               'map':'Football Stadium'
            },
            'type':'bsFootball.FootballTeamGame'
         },
         {
            'settings':{
               'Epic Mode':True,
               'Respawn Times':0.25,
               'Score to Win':3,
               'Time Limit':120,
               'map':'Bridgit'
            },
            'type':'bsAssault.AssaultGame'
         },
         {
            'map':'Doom Shroom',
            'settings':{
               'Enable Impact Bombs':1,
               'Enable Triple Bombs':False,
               'Target Count':2,
               'map':'Doom Shroom'
            },
            'type':'bsTargetPractice.TargetPracticeGame'
         },
         {
            'settings':{
               'Hold Time':30,
               'Respawn Times':1.0,
               'Time Limit':300,
               'map':'Tip Top'
            },
            'type':'bsKingOfTheHill.KingOfTheHillGame'
         },
         {
            'settings':{
               'Epic Mode':False,
               'Respawn Times':1.0,
               'Score to Win':2,
               'Time Limit':300,
               'map':'Zigzag'
            },
            'type':'bsAssault.AssaultGame'
         },
         {
            'settings':{
               'Epic Mode':False,
               'Flag Idle Return Time':30,
               'Flag Touch Return Time':0,
               'Respawn Times':1.0,
               'Score to Win':3,
               'Time Limit':300,
               'map':'Happy Thoughts'
            },
            'type':'bsCaptureTheFlag.CTFGame'
         },
         {
            'settings':{
               'Bomb Spawning':1000,
               'Epic Mode':True,
               'Laps':1,
               'Mine Spawning':2000,
               'Time Limit':300,
               'map':'Big G'
            },
            'type':'bsRace.RaceGame'
         },
         {
            'settings':{
               'Epic Mode':False,
               'Kills to Win Per Player':5,
               'Respawn Times':1.0,
               'Time Limit':300,
               'map':'Monkey Face'
            },
            'type':'bsDeathMatch.DeathMatchGame'
         },
         {
            'settings':{
               'Hold Time':30,
               'Respawn Times':1.0,
               'Time Limit':300,
               'map':'Lake Frigid'
            },
            'type':'bsKeepAway.KeepAwayGame'
         },
         {
            'settings':{
               'Epic Mode':False,
               'Flag Idle Return Time':30,
               'Flag Touch Return Time':3,
               'Respawn Times':1.0,
               'Score to Win':2,
               'Time Limit':300,
               'map':'Tip Top'
            },
            'type':'bsCaptureTheFlag.CTFGame'
         },
         {
            'settings':{
               'Balance Total Lives':False,
               'Epic Mode':False,
               'Lives Per Player':3,
               'Respawn Times':1.0,
               'Solo Mode':False,
               'Time Limit':300,
               'map':'Crag Castle'
            },
            'type':'bsElimination.EliminationGame'
         },
         {
            'settings':{
               'Epic Mode':True,
               'Respawn Times':0.25,
               'Time Limit':120,
               'map':'Zigzag'
            },
            'type':'bsConquest.ConquestGame'
         }
      ]

def _readConfig():
    global gConfigFileIsHealthy
    global _gConfig
    configFilePath = bs.getEnvironment()['configFilePath']
    configContents = ''
    try:
        oldConfigPath = configFilePath[:-5]
        if os.path.exists(configFilePath):
            f = open(configFilePath, 'rb')
            configContents = f.read()
            f.close()
            # supply unicode input to force unicode output
            _gConfig = json.loads(configContents.decode(
                'utf-8', errors='ignore'))
            # while we're here, if they have an old-style config,
            # rename it so they know its old
            if (os.path.exists(oldConfigPath)
                    and not os.path.exists(oldConfigPath+'.old')):
                try: os.rename(oldConfigPath, oldConfigPath+'.old')
                except Exception as e:
                    print 'unable to rename old non-json config:', e
        else:
            # special case - we used to store configs as python code
            # so if we can't find our json file, look for that...
            if os.path.exists(oldConfigPath):
                f2 = open(oldConfigPath, 'rb')
                configContents = f2.read()
                f2.close()
                _gConfig = ast.literal_eval(configContents)
                # push it in and out of json just to make sure we get what
                # we would loading from a json config.. (all unicode, etc)
                _gConfig = jsonPrep(_gConfig)
            else:
                # no new file; no old file. start fresh
                _gConfig = {}
        gConfigFileIsHealthy = True
        
    except Exception as e:
        
        print ('error reading config file at time '+str(bs.getRealTime())
               +': \''+configFilePath+'\':\n'), e
        # whenever this happens lets back up the broken one just in case it
        # gets overwritten accidentally
        print 'backing up current config file to \''+configFilePath+".broken\'"
        try:
            import shutil
            shutil.copyfile(configFilePath, configFilePath+'.broken')
        except Exception as e: print 'EXC copying broken config:', e
        try:
            bsInternal._log('broken config contents:\n'+configContents.replace(
                '\000', '<NULL_BYTE>'), toConsole=False)
        except Exception as e:
            print 'EXC logging broken config contents:', e
        _gConfig = {}

        # now attempt to read one of our 'prev' backup copies
        prevPath = configFilePath + '.prev'
        try:
            if os.path.exists(prevPath):
                f = open(prevPath, 'rb')
                configContents = f.read()
                f.close()
                _gConfig = json.loads(configContents)
            else: _gConfig = {}
            gConfigFileIsHealthy = True
            print 'successfully read backup config.'
        except Exception as e:
            print 'EXC reading prev backup config:', e

def _prettifyList(l, indent=0, multiLine=True):
    bits = []
    bits.append('[\n' if multiLine else '[')
    for i in range(len(l)):
        a = l[i]
        if isinstance(a, dict):
            if multiLine: bits.append(' '*(indent+3))
            bits += _prettifyDict(a, indent+3, multiLine, returnBits=True)
        else:
            if multiLine: bits.append(' '*(indent+3) + repr(a))
            else: bits.append(repr(a))
        if (i < (len(l)-1)):
            bits.append(',')
        if multiLine: bits.append("\n")
    bits.append((' '*indent + ']') if multiLine else ']')
    return bits

def _prettifyDict(d, indent=0, multiLine=True, returnBits=False):
    bits = []
    bits.append('{\n' if multiLine else '{')
    items = d.items()
    items.sort()
    for i in range(len(items)):
        a = items[i][0]
        b = items[i][1]
        maxStrLineLen = 100
        if isinstance(b, dict):
            if multiLine: bits.append(' '*(indent+3) + repr(a) + ':')
            else: bits.append(repr(a) + ':')
            bits += _prettifyDict(b, indent+3, multiLine, returnBits=True)
        elif isinstance(b, list):
            if multiLine: bits.append(' '*(indent+3) + repr(a) + ':')
            else: bits.append(repr(a) + ':')
            bits += _prettifyList(b, indent+3, multiLine)
        # special case - break really long strings into multiple lines
        elif multiLine and isinstance(b, str) and len(b) > maxStrLineLen:
            bCopy = b
            bLines = []
            indentStr = ' '*(indent+3+len(a)+4)
            while len(bCopy) > 0:
                if len(bLines) > 0:
                    bLines.append(indentStr+repr(bCopy[:maxStrLineLen]))
                else: bLines.append('('+repr(bCopy[:maxStrLineLen]))
                bCopy = bCopy[maxStrLineLen:]
            bits.append(' '*(indent+3) + repr(a) + ':' + '\n'.join(bLines)+')')
        else:
            if multiLine: bits.append(' '*(indent+3) + repr(a) + ':' + repr(b))
            else: bits.append(repr(a) + ':' + repr(b))
        if (i < (len(items)-1)):
            bits.append(',')
        if multiLine: bits.append("\n")
    bits.append((' '*indent + '}') if multiLine else '}')

    if returnBits:
        return bits
    else: return ''.join(bits)


gAllowingPackageMods = None
gPackageModsAdded = set()

def _getModulesWithCall(callName, whiteList=None, blackList=None):
    
    # first off, see if we're allowing low-level mods if we havn't
    global gAllowingPackageMods
    if gAllowingPackageMods is None:
        gAllowingPackageMods = bsInternal._getSetting('Enable Package Mods')
        
    haveMods = False
    env = bs.getEnvironment()
    scriptDirs = [env['systemScriptsDirectory'], env['userScriptsDirectory']]

    # if package mods are enabled, tally up all dirs under user-mods that we
    # consider to be 'packages' - we'll import anything we find in them too..
    extraPackageModFiles = []
    if gAllowingPackageMods:
        import sys
        d = env['userScriptsDirectory']

        if os.path.isdir(d):
            try:
                dirlist = os.listdir(d)
            except Exception:
                bs.printException('error listing dir during'
                                  ' _getModulesWithCall(): \''+d+'\'')
                dirlist = []
        else: dirlist = []
        
        for name in dirlist:
            packageDir = d+'/'+name
            if os.path.isdir(packageDir) and name != 'sys':
                # for each valid package we find, add it to the python
                # path and media lookup path if we havn't yet..
                if name not in gPackageModsAdded:
                    gPackageModsAdded.add(name)
                    sys.path.append(packageDir+'/scripts')
                    bsInternal._addPackage(name, packageDir)
                scriptDirs.append(packageDir+'/scripts')

    # lets warn if have duplicate scripts..
    namesImported = set()

    modules = []
    for i, d in enumerate(scriptDirs):

        if os.path.isdir(d):
            try: dirlist = os.listdir(d)
            except Exception as e:
                import errno
                if (type(e) == OSError
                        and e.errno in (errno.EACCES, errno.ENOENT)):
                    pass # we expect these sometimes..
                else:
                    bs.printException('error listing dir during '
                                      '_getModulesWithCall(): \''+d+'\'')
                dirlist = []
        else: dirlist = []

        for name in dirlist:
            try:
                if name == 'sys' or name.endswith('.py'):
                    # if there's anything in user-mods or package dirs,
                    # let the game know that we've got moding going on..
                    # (we do less error reporting in this case for
                    # my sanity's sake)
                    if i >= 1: haveMods = True

                moduleName = name.replace('.py', '')

                # if there's a black-list, make sure this isn't on it
                if (blackList is None or moduleName not in blackList):

                    # if there's a white-list, make sure this *is* on it
                    if (whiteList is None or moduleName in whiteList):
                        
                        # avoid importing language modules here to save
                        # a bit of time/memory..
                        if (name.endswith('.py')
                            and not name.startswith('bsLanguage')):
                            if name in namesImported:
                                errMsg = ("Warning: duplicate mod script "
                                          "found: '"+name+"'; ignoring.")
                                print errMsg
                                bs.screenMessage(errMsg, color=(1, 0, 0))
                            else:
                                namesImported.add(name)
                                module = __import__(moduleName)

                                # only look at the module if it contains
                                # the callable we're after
                                call = getattr(module, callName, None)
                                if call is not None and callable(call):

                                    # if this module's API-version doesn't match
                                    # ours, ignore it (and complain about it)
                                    ourAPIVersion = 4
                                    try: moduleAPIVersion = \
                                       module.bsGetAPIVersion()
                                    except Exception: moduleAPIVersion = None
                                    if moduleAPIVersion == ourAPIVersion:
                                        modules.append(module)
                                    else:
                                        try: name = module.__name__
                                        except Exception: name = str(module)
                                        txt = bs.Lstr(
                                            resource='apiVersionErrorText',
                                            subs=[('${NAME}', name),
                                                  ('${VERSION_USED}',
                                                   str(moduleAPIVersion)),
                                                  ('${VERSION_REQUIRED}',
                                                   str(ourAPIVersion))])
                                        bs.screenMessage(txt, color=(1, 0.5, 0))
            except Exception:
                bs.printException('Error importing game module \''+name+'\'')
                
    bsInternal._setHaveMods(haveMods)
    return modules

def getGameTypes():
    allGames = []
    modules = _getModulesWithCall('bsGetGames')
    for module in modules:
        if ((module.__name__ != 'bsMeteorShower'
             or bsInternal._getPurchased('games.meteor_shower'))
            and (module.__name__ != 'bsTargetPractice'
                 or bsInternal._getPurchased('games.target_practice'))
            and (module.__name__ != 'bsNinjaFight'
                 or bsInternal._getPurchased('games.ninja_fight'))
            and (module.__name__ != 'bsEasterEggHunt'
                 or bsInternal._getPurchased('games.easter_egg_hunt'))):
            allGames += module.bsGetGames()
    return allGames

gTips = []

def _getNextTip():
    """ returns the next tip to be displayed """
    global gTips
    if len(gTips) == 0:
        for tip in _getAllTips():
            gTips.insert(random.randint(0, len(gTips)), tip)
    t = gTips.pop()
    return t

def _getAllTips():
    tips =  [
        ('If you are short on controllers, install the \'${REMOTE_APP_NAME}\' '
        'app\non your mobile devices to use them as controllers.'),
        ('Create player profiles for yourself and your friends with\nyour '
        'preferred names and appearances instead of using random ones.'),
        ('You can \'aim\' your punches by spinning left or right.\nThis is '
        'useful for knocking bad guys off edges or scoring in hockey.'),
        ('If you pick up a curse, your only hope for survival is to\nfind a '
        'health powerup in the next few seconds.'),
        ('A perfectly timed running-jumping-spin-punch can kill in a single '
         'hit\nand earn you lifelong respect from your friends.'),
        'Always remember to floss.',
        'Don\'t run all the time.  Really.  You will fall off cliffs.',
        ('In Capture-the-Flag, your own flag must be at your base to score, '
         'If the other\nteam is about to score, stealing their flag can be '
         'a good way to stop them.'),
        ('If you get a sticky-bomb stuck to you, jump around and spin in '
         'circles. You might\nshake the bomb off, or if nothing else your '
         'last moments will be entertaining.'),
        ('You take damage when you whack your head on things,\nso try to not '
         'whack your head on things.'),
        'If you kill an enemy in one hit you get double points for it.',
        ('Despite their looks, all characters\' abilities are identical,\nso '
         'just pick whichever one you most closely resemble.'),
        'You can throw bombs higher if you jump just before throwing.',
        ('Throw strength is based on the direction you are holding.\nTo toss '
         'something gently in front of you, don\'t hold any direction.'),
        ('If someone picks you up, punch them and they\'ll let go.\nThis '
         'works in real life too.'),
        ('Don\'t get too cocky with that energy shield; you can still get '
         'yourself thrown off a cliff.'),
        ('Many things can be picked up and thrown, including other players.  '
         'Tossing\nyour enemies off cliffs can be an effective and '
         'emotionally fulfilling strategy.'),
        ('Ice bombs are not very powerful, but they freeze\nwhoever they '
         'hit, leaving them vulnerable to shattering.'),
        'Don\'t spin for too long; you\'ll become dizzy and fall.',
        ('Run back and forth before throwing a bomb\nto \'whiplash\' it '
         'and throw it farther.'),
        ('Punches do more damage the faster your fists are moving,\nso '
         'try running, jumping, and spinning like crazy.'),
        'In hockey, you\'ll maintain more speed if you turn gradually.',
        ('The head is the most vulnerable area, so a sticky-bomb\nto the '
         'noggin usually means game-over.'),
        ('Hold down any button to run. You\'ll get places faster\nbut '
         'won\'t turn very well, so watch out for cliffs.'),
        ('You can judge when a bomb is going to explode based on the\n'
         'color of sparks from its fuse:  yellow..orange..red..BOOM.'),
        ]
    ua = bs.getEnvironment()['userAgentString']
    tips += ['If your framerate is choppy, try turning down resolution\nor '
             'visuals in the game\'s graphics settings.']
    if bs.getEnvironment()['platform'] in ('android', 'ios'):
        tips += [('If your device gets too warm or you\'d like to conserve '
                  'battery power,\nturn down "Visuals" or "Resolution" '
                  'in Settings->Graphics'),]
    if bs.getEnvironment()['platform'] in ['mac', 'android']:
        tips += ['Tired of the soundtrack?  Replace it with your own!'
                 '\nSee Settings->Audio->Soundtrack']
    # hot-plugging is currently mac/android only
    if bs.getEnvironment()['platform'] in ['mac', 'android', 'windows']:
        tips += [
            'Players can join and leave in the middle of most games,\n'
            'and you can also plug and unplug controllers on the fly.',
        ]
    return tips

def _getUnOwnedGameTypes():
    try:
        import bsUI
        import bsInternal
        unOwnedGames = set()
        if bs.getEnvironment()['subplatform'] != 'headless':
            for section in bsUI._getStoreLayout()['minigames']:
                for m in section['items']:
                    if not bsInternal._getPurchased(m):
                        mInfo = bsUI._getStoreItem(m)
                        unOwnedGames.add(mInfo['gameType'])
        return unOwnedGames
    except Exception:
        bs.printException("error calcing un-owned games")
        return set()

def _filterPlaylist(playlist, sessionType, addResolvedType=False,
                    removeUnOwned=True, markUnOwned=False):
    """ returns a filtered version of a playlist - strips out or replaces
    invalid or unowned game types, makes sure all settings are present,
    and adds in a 'resolvedType' which is the actual type """
    import bsMap
    goodList = []
    if removeUnOwned or markUnOwned:
        unOwnedMaps = bsMap._getUnOwnedMaps()
        unOwnedGameTypes = _getUnOwnedGameTypes()
    else:
        unOwnedMaps = []
        unOwnedGameTypes = []
        
    for i, gamespec in enumerate(copy.deepcopy(playlist)):
        # 'map' used to be called 'level'
        if 'level' in gamespec:
            gamespec['map'] = gamespec['level']
            del gamespec['level']
        # we now stuff map into settings instead of it being its own thing...
        if 'map' in gamespec:
            gamespec['settings']['map'] = gamespec['map']
            del gamespec['map']
        gamespec['settings']['map'] = bsMap.getFilteredMapName(
            gamespec['settings']['map'])
        if removeUnOwned and gamespec['settings']['map'] in unOwnedMaps:
            continue
        # ok, for each game in our list, try to import the module and grab
        # the actual game class. add successful ones to our initial list
        # to present to the user
        if type(gamespec['type']) in [str, unicode]:
            try:
                # do some type filters for backwards compat.
                if gamespec['type'] == 'Happy_Thoughts.HappyThoughtsGame':
                    gamespec['type'] = 'bsAssault.AssaultGame'
                if gamespec['type'] == 'Assault.AssaultGame':
                    gamespec['type'] = 'bsAssault.AssaultGame'
                if gamespec['type'] == 'King_of_the_Hill.KingOfTheHillGame':
                    gamespec['type'] = 'bsKingOfTheHill.KingOfTheHillGame'
                if gamespec['type'] == 'Capture_the_Flag.CTFGame':
                    gamespec['type'] = 'bsCaptureTheFlag.CTFGame'
                if gamespec['type'] == 'Death_Match.DeathMatchGame':
                    gamespec['type'] = 'bsDeathMatch.DeathMatchGame'
                if gamespec['type'] == 'ChosenOne.ChosenOneGame':
                    gamespec['type'] = 'bsChosenOne.ChosenOneGame'
                if gamespec['type'] == 'Conquest.Conquest':
                    gamespec['type'] = 'bsConquest.ConquestGame'
                if gamespec['type'] == 'Conquest.ConquestGame':
                    gamespec['type'] = 'bsConquest.ConquestGame'
                if gamespec['type'] == 'Elimination.EliminationGame':
                    gamespec['type'] = 'bsElimination.EliminationGame'
                if gamespec['type'] == 'Football.FootballGame':
                    gamespec['type'] = 'bsFootball.FootballTeamGame'
                if gamespec['type'] == 'Hockey.HockeyGame':
                    gamespec['type'] = 'bsHockey.HockeyGame'
                if gamespec['type'] == 'Keep_Away.KeepAwayGame':
                    gamespec['type'] = 'bsKeepAway.KeepAwayGame'
                if gamespec['type'] == 'Race.RaceGame':
                    gamespec['type'] = 'bsRace.RaceGame'
                gameModuleName, gameClassName = gamespec['type'].split('.')

                gameModule = __import__(gameModuleName)
                gameClass = getattr(gameModule, gameClassName)

                # skip this one completely if they want to strip un-owned stuff.
                if removeUnOwned and gameClass in unOwnedGameTypes: continue
                if addResolvedType: gamespec['resolvedType'] = gameClass
                if markUnOwned and gamespec['settings']['map'] in unOwnedMaps:
                    gamespec['isUnOwnedMap'] = True
                if markUnOwned and gameClass in unOwnedGameTypes:
                    gamespec['isUnOwnedGame'] = True
                    
                # make sure all settings the game defines are present
                neededSettings = gameClass.getSettings(sessionType)
                for settingName, setting in neededSettings:
                    if settingName not in gamespec['settings']:
                        gamespec['settings'][settingName] = setting['default']
                goodList.append(gamespec)
            except Exception:
                pass # hmm in what case would we want to report this?...
        else:
            raise Exception("invalid gamespec format")
    return goodList


gLogUploadTimerStarted = False
gLogHaveNew = False


# called on debug log prints..
# when this happens, we can upload our log to the server
# after a short bit if desired.
def _handleLog():
    global gLogUploadTimerStarted
    global gLogHaveNew
    gLogHaveNew = True

    if not gLogUploadTimerStarted:
        def _putLog():
            import bsUtils
            if not bsUtils._gSuppressDebugReports:
                try: sessionName = str(bsInternal._getForegroundHostSession())
                except Exception: sessionName = 'unavailable'
                try: activityName = str(bsInternal._getForegroundHostActivity())
                except Exception: activityName = 'unavailable'
                env = bs.getEnvironment()
                info = {
                    'log':bsInternal._getLog(),
                    'version':env['version'],
                    'build':env['buildNumber'],
                    'userAgentString':bs.getEnvironment()['userAgentString'],
                    'session':sessionName,
                    'activity':activityName,
                    'fatal':0,
                    'userRanCommands':bsInternal._hasUserRunCommands(),
                    'time':bs.getRealTime(),
                    'userModded':bsInternal._hasUserMods()}
                def response(data):
                    # a non-None response means success; lets
                    # take note that we don't need to report further
                    # log info this run
                    if data is not None:
                        global gLogHaveNew
                        gLogHaveNew = False
                        bsInternal._markLogSent()
                bsUtils.serverPut('bsLog', info, response)
        gLogUploadTimerStarted = True

        # delay our log upload slightly in case other
        # pertinant info gets printed between now and then
        bs.realTimer(3000, _putLog)

        # after a while, allow another log-put
        def _reset():
            global gLogUploadTimerStarted
            gLogUploadTimerStarted = False
            if gLogHaveNew: _handleLog()
        if not bsInternal._isLogFull():
            bs.realTimer(1000*60*10, _reset)

def writeConfig(force=False, storeRemote=True):
    """category: General Utility Functions
    Commit the config to disk/cloud/etc"""

    bsConfig = bs.getConfig()
    global gConfigFileIsHealthy
    if not gConfigFileIsHealthy and not force:
        print ("Current config file is broken; "
               "skipping write to avoid losing settings.")
        return
    bsInternal._markConfigDirty()
    
def _setLanguage(language, printChange=True, storeToConfig=True):
    """Set the language used by the game.  Pass None to use OS default."""
    global _gLanguageTarget
    global _gLanguageMerged
    bsConfig = bs.getConfig()
    try: curLanguage = bsConfig['Lang']
    except Exception: curLanguage = None

    # store this in the config if its changing
    if language != curLanguage and storeToConfig:
        if language is None:
            del bsConfig['Lang'] # clear it out for default
        else:
            bsConfig['Lang'] = language
        writeConfig()
        switched = True
    else: switched = False

    # None implies default (currently locked to english)
    if language is None:
        language = _getDefaultLanguage()
    try:
        lEnglish = __import__('bsLanguageEnglish')
        l = __import__('bsLanguage'+language)
        if language != 'English': reload(l) # helpful for iterating
    except Exception:
        bs.printException('Exception importing language:', language)
        bs.screenMessage("Error setting language to '"
                         + language + "'; see log for details", color=(1, 0, 0))
        switched = False
        l = None
    # create an attrdict of *just* our target language
    _gLanguageTarget = AttrDict()
    _addToAttrDict(_gLanguageTarget,
                   l.values if l is not None else lEnglish.values)
    # create an attrdict of our target languaged overlaid on our base (english)
    languages = []
    if l is not None: languages.append(l)
    if language != 'English': languages.append(__import__('bsLanguageEnglish'))
    languages.reverse()
    lFull = AttrDict()
    for l in languages:
        _addToAttrDict(lFull, l.values)
    _gLanguageMerged = lFull

    # pass some keys/values in for low level code to use;
    # start with everything in ther 'internal' section...
    internalVals = [v for v in lFull['internal'].items()
                    if type(v[1]) in (str, unicode)]
    # cherry-pick various other values to include..
    # (should probably get rid of the 'internal' section
    # and do everything this way)
    for value in ['replayNameDefaultText', 'replayWriteErrorText',
                  'replayVersionErrorText', 'replayReadErrorText']:
        internalVals.append((value, lFull[value]))
    internalVals.append(('axisText', lFull['configGamepadWindow']['axisText']))
    randomNames = [n.strip() for n in _gLanguageMerged['randomPlayerNamesText']\
                   .split(',')]
    randomNames = [n for n in randomNames if n != '']
    bsInternal._setInternalLanguageKeys(internalVals, randomNames)
    if switched and printChange:
        bs.screenMessage(bs.Lstr(resource='languageSetText',
                                 subs=[('${LANGUAGE}', bs.Lstr(
                                     translate=('languages', language)))]),
                         color=(0, 1, 0))

gLastInGameAdRemoveMessageShowTime = None

def _doRemoveInGameAdsMessage():

    # print this message once every 10 minutes at most
    t = bs.getRealTime()
    global gLastInGameAdRemoveMessageShowTime
    if (gLastInGameAdRemoveMessageShowTime is None
            or (t - gLastInGameAdRemoveMessageShowTime > 1000*60*10)):
        gLastInGameAdRemoveMessageShowTime = t
        with bs.Context('UI'):
            bs.realTimer(1000, bs.Call(bs.screenMessage, bs.Lstr(
                resource='removeInGameAdsText',
                subs=[('${PRO}',
                       bs.Lstr(resource='store.bombSquadProNameText')),
                      ('${APP_NAME}', bs.Lstr(resource='titleText'))]),
                                       color=(1, 1, 0)))
    
class AttrDict(dict):
    """ a dict that can be accessed with dot notation: foo.bar is equivalant
        to foo['bar']. NOTE: accessing via attribute currently also currently
        translates from utf8 to unicode (should maybe start storing these
        in unicode to avoid that quirk) """
    def __getattr__(self, attr):
        val = self[attr]
        if type(val) is str: return val.decode('utf-8')
        else: return val
    def __setattr__(self, attr, value):
        raise Exception()
        self[attr] = value

def _addToAttrDict(dst, src):
    for key, value in src.items():
        if type(value) is dict:
            try: dstDict = dst[key]
            except Exception: dstDict = dst[key] = AttrDict()
            if type(dstDict) is not AttrDict:
                raise Exception("language key '"+ key
                                + "' is defined both as a dict and value")
            _addToAttrDict(dstDict, value)
        else:
            if type(value) not in (float, int, bool, str, unicode, type(None)):
                raise Exception("invalid value type for res '" + key
                                + "': " + str(type(value)))
            dst[key] = value

def _canDisplayLanguage(lang):
    # we don't yet support full unicode display on windows or linux..
    if (lang in ('Chinese', 'Persian', 'Korean', 'Arabic', 'Hindi')
            and bs.getEnvironment()['platform'] in ('windows', 'linux')):
        return False
    else:
        return True
    
def _getDefaultLanguage():
    langs = { 'de':'German', 'es':'Spanish', 'it':'Italian', 'nl':'Dutch',
              'da':'Danish', 'pt':'Portuguese', 'fr':'French', 'ru':'Russian',
              'pl':'Polish', 'sv':'Swedish', 'eo':'Esperanto', 'cs':'Czech',
              'hr':'Croatian', 'hu':'Hungarian', 'be':'Belarussian',
              'ro':'Romanian', 'ko':'Korean', 'fa':'Persian', 'ar':'Arabic',
              'zh':'Chinese', 'tr':'Turkish', 'id':'Indonesian',
              'sr':'Serbian', 'uk':'Ukrainian', 'hi':'Hindi'}
    lang = langs.get(bs.getEnvironment()['locale'][:2], 'English')
    if not _canDisplayLanguage(lang): lang = 'English'
    return lang

def getLanguage(returnNoneForDefault=False):
    """
    category: General Utility Functions

    Returns the language currently being used by the game.
    This may or may not equal the language in use by the OS.
    """

    try: language = bs.getConfig()['Lang']
    except Exception: language = None

    if language is None and not returnNoneForDefault:
        language = _getDefaultLanguage()

    return language
    
        
def _getResource(resource, fallbackResource=None, fallbackValue=None):
    try:
        global _gLanguageTarget
        global _gLanguageMerged

        # if we have no language set, go ahead and set it
        if _gLanguageMerged is None:
            language = getLanguage()
            try: _setLanguage(language, printChange=False, storeToConfig=False)
            except Exception:
                bs.printException('exception setting language to', language)
                # try english as a fallback
                if (language != 'English'):
                    print 'Resorting to fallback language (English)'
                    try: _setLanguage('English', printChange=False,
                                      storeToConfig=False)
                    except Exception as e:
                        print 'Error setting language to English fallback: ', e

        # if they provided a fallbackResource value, try the
        # target-language-only dict first and then fall back to trying the
        # fallbackResource value in the merged dict.
        if fallbackResource is not None:
            try:
                values = _gLanguageTarget
                splits = resource.split('.')
                dicts = splits[:-1]
                key = splits[-1]
                for d in dicts: values = values[d]
                val = values[key]
                if uni and type(val) is str:
                    val = val.decode('utf-8', errors='ignore')
                return val
            except Exception:
                # FIXME - shouldn't we try the fallback resource in the merged
                # dict AFTER we try the main resource in the merged dict?...
                try:
                    values = _gLanguageMerged
                    splits = fallbackResource.split('.')
                    dicts = splits[:-1]
                    key = splits[-1]
                    for d in dicts: values = values[d]
                    val = values[key]
                    if uni and type(val) is str:
                        val = val.decode('utf-8', errors='ignore')
                    return val
                
                except Exception:
                    # if we got nothing for fallbackResource, default to the
                    # normal code which checks or primary value in the merge
                    # dict; there's a chance we can get an english value for
                    # it (which we weren't looking for the first time through)
                    pass
                    
        values = _gLanguageMerged
        splits = resource.split('.')
        dicts = splits[:-1]
        key = splits[-1]
        for d in dicts: values = values[d]
        val = values[key]
        if uni and type(val) is str:
            val = val.decode('utf-8', errors='ignore')
        return val

    except Exception:
        # ok looks like we couldn't find our main or fallback resource anywhere.
        # now if we've been given a fallback value, return it; otherwise fail
        if fallbackValue is not None:
            return uni(fallbackValue)
        raise Exception("resource not found: '"+resource+"'")

def _translate(category, s, raiseExceptions=False, printErrors=False):
    try: translated = _getResource('translations')[category][s]
    except Exception as e:
        if raiseExceptions: raise e
        if printErrors:
            print ('Translate error: category=\'' + category + '\' name=\''
                   + s +'\' exc=' + str(e) + '')
        translated = None
    if translated is None:
        translated = s
    return bs.uni(translated) if uni else translated

def getTypeName(t):
    return t.__module__ + '.' + t.__name__

def resolveTypeName(typeName):
    moduleName, className = typeName.split('.')
    module = __import__(moduleName)
    return getattr(module, className)
    
def getPlayerColors():
    """ return user-selectable player colors """
    return _gPlayerColors

# call suppressDebugReports() to keep from spamming the
# debug log server during development
_gSuppressDebugReports = False
def suppressDebugReports():
    bs.screenMessage("Supressing debug reports", color=(1, 0, 0))
    global _gSuppressDebugReports
    _gSuppressDebugReports = True
_gPrintedLiveObjectWarning = False

def animate(node, attr, keys, loop=False, offset=0, driver='gameTime'):
    """
    category: Game Flow Functions

    Creates an animCurve node with the provided values and time as an input,
    connect it to the provided attribute, and set it to die with the target.
    Key values are provided as time:value dictionary pairs.  Time values are
    relative to the current time. Returns the animCurve node.
    """

    if driver != 'gameTime':
        raise Exception("fixme; only support game-time currently")
    items = keys.items()
    items.sort()
    curve = bs.newNode("animCurve", owner=node,
                       name='Driving '+str(node)+' \''+attr+'\'')
    curve.times = [time for time, val in items]
    curve.values = [val for time, val in items]
    curve.loop = loop
    curve.offset = bs.getGameTime()+offset
    # if we're not looping, set a timer to kill this curve
    # after its done its job
    # FIXME - even if we are looping we should have a way to die once we
    # get disconnected
    if loop == False:
        bs.gameTimer(int(items[-1][0])+1000, curve.delete)

    # do the connects last so all our attrs are in place when we push initial
    # values through..
    bs.getSharedObject('globals').connectAttr(driver, curve, "in")
    curve.connectAttr("out", node, attr)
    return curve

def animateArray(node, attr, size, keys, loop=False,
                 offset=0, driver='gameTime'):
    """
    category: Game Flow Functions
    
    Like bsUtils.animate(), but operates on array attributes.
    """
    combine = bs.newNode('combine', owner=node, attrs={'size':size})
    if driver != 'gameTime':
        raise Exception("fixme; only support game-time currently")
    items = keys.items()
    items.sort()
    curves = {}
    for i in range(size):
        curve = bs.newNode("animCurve", owner=node,
                           name=('Driving '+str(node)+' \''
                                  + attr + '\' member ' + str(i)))
        bs.getSharedObject('globals').connectAttr(driver, curve, "in")
        curve.times = [time for time, val in items]
        curve.values = [val[i] for time, val in items]
        curve.loop = loop
        curve.offset = bs.getGameTime()+offset
        curve.connectAttr("out", combine, 'input'+str(i))
        # if we're not looping, set a timer to kill this
        # curve after its done its job
        if loop == False:
            bs.gameTimer(int(items[-1][0])+1000, curve.delete)
    combine.connectAttr('output', node, attr)
    # if we're not looping, set a timer to kill the combine once the job is done
    # FIXME - even if we are looping we should have a way to die
    # once we get disconnected
    if loop == False:
        bs.gameTimer(int(items[-1][0])+1000, combine.delete)

# called internally..
def _shutdown():
    if _gMusicPlayer is not None:
        _gMusicPlayer.shutdown()

class MusicPlayer(object):

    def __init__(self):
        self._haveSetInitialVolume = False
        self._entryToPlay = None
        self._volume = 1.0
        self._actuallyPlaying = False

    def selectEntry(self, callback, currentEntry, selectionTargetName):
        return self.onSelectEntry(callback, currentEntry, selectionTargetName)
        
    def setVolume(self, volume):
        oldVolume = self._volume
        self._volume = volume
        self.onSetVolume(volume)
        self._updatePlayState()

    def _updatePlayState(self):
        # if we arent playing, should be, and have positive volume, do so
        if not self._actuallyPlaying:
            if self._entryToPlay is not None and self._volume > 0.0:
                self.onPlay(self._entryToPlay)
                self._actuallyPlaying = True
        else:
            if self._actuallyPlaying and (self._entryToPlay is None
                                          or self._volume <= 0.0):
                self.onStop()
                self._actuallyPlaying = False
                
    def play(self, entry):
        if not self._haveSetInitialVolume:
            self._volume = bsInternal._getSetting('Music Volume')
            self.onSetVolume(self._volume)
            self._haveSetInitialVolume = True
        self._entryToPlay = copy.deepcopy(entry)

        # if we're currently *actually* playing something,
        # switch to the new thing..
        # otherwise update state which will start us playing *only*
        # if proper (volume > 0, etc)
        if self._actuallyPlaying: self.onPlay(self._entryToPlay)
        else: self._updatePlayState()

    def stop(self):
        self._entryToPlay = None
        self._updatePlayState()

    def shutdown(self):
        self.onShutdown()
        
    # subclasses should override the following:
    def onSelectEntry(self, callback, currentEntry, selectionTargetName):
        """should present a GUI to select an entry; callback should
        be called with an entry or None to signify default"""
        pass
    
    def onSetVolume(self, volume):
        'Called when the volume should be changed'
        pass

    def onPlay(self, entry):
        'Called when a new song/playlist/etc should be played'
        pass

    def onStop(self):
        'Called when the music should stop'
        pass

    def onShutdown(self):
        'Called on final app shutdown'
        pass

_gMusicPlayer = None
_gMusicPlayerType = None

# for internal music player
def _getValidMusicFileExtensions():
    return ['mp3', 'ogg', 'm4a', 'wav', 'flac', 'mid']

if bs.getEnvironment()['platform'] == 'android':

    # this talks to native stuff via our c layer
    class InternalMusicPlayer(MusicPlayer):
        def __init__(self):
            MusicPlayer.__init__(self)
            self._wantToPlay = False
            self._actuallyPlaying = False
            
        def onSelectEntry(self, callback, currentEntry, selectionTargetName):
            import bsUI
            return bsUI.GetSoundtrackEntryTypeWindow(callback,
                                                     currentEntry,
                                                     selectionTargetName)
        def onSetVolume(self, volume):
            bsInternal._musicPlayerSetVolume(volume);

        class _PickFolderSongThread(threading.Thread):
            def __init__(self, path, callback):
                threading.Thread.__init__(self)
                self._callback = callback
                self._path = path

            def run(self):
                try:
                    bsInternal._setThreadName("BS_PickFolderSongThread")
                    allFiles = []
                    validExtensions = ['.'+x for x in
                                       _getValidMusicFileExtensions()]
                    for root, subFolders, files in os.walk(bs.utf8(self._path)):
                        for f in files:
                            if any(f.lower().endswith(ext)
                                   for ext in validExtensions):
                                allFiles.insert(random.randrange(
                                    len(allFiles)+1), bs.uni(root+'/'+f))
                    if len(allFiles) == 0:
                        raise Exception(bs.Lstr(
                            resource='internal.noMusicFilesInFolderText')\
                                        .evaluate())
                    bs.callInGameThread(bs.Call(self._callback,
                                                result=allFiles))
                except Exception as e:
                    bs.printException()
                    try: errStr = unicode(e)
                    except Exception: errStr = '<ENCERR4523>'
                    bs.callInGameThread(
                        bs.Call(self._callback, result=self._path,
                                error=errStr))
            
        def onPlay(self, entry):
            entryType = _getSoundtrackEntryType(entry)
            name = _getSoundtrackEntryName(entry)
            if entryType == 'musicFile':
                self._wantToPlay = self._actuallyPlaying = True
                bsInternal._musicPlayerPlay(name)
            elif entryType == 'musicFolder':
                # launch a thread to scan this folder and give us a random
                # valid file within
                self._wantToPlay = True
                self._actuallyPlaying = False
                self._PickFolderSongThread(name, self._onPlayFolderCB).start()

        def _onPlayFolderCB(self, result, error=None):
            if error is not None:
                rstr = bs.Lstr(resource='internal.errorPlayingMusicText')\
                         .evaluate()
                errStr = (rstr.replace(u'${MUSIC}', os.path.basename(result))
                          +u'; '+unicode(error))
                bs.screenMessage(errStr, color=(1, 0, 0))
                return

            # theres a chance a stop could have been issued before our thread
            # returned..
            # if that's the case, dont' play.
            if not self._wantToPlay:
                print '_onPlayFolderCB called with _wantToPlay False'
            else:
                self._actuallyPlaying = True
                bsInternal._musicPlayerPlay(result)
        
        def onStop(self):
            self._wantToPlay = False
            self._actuallyPlaying = False
            bsInternal._musicPlayerStop()

        def onShutdown(self):
            bsInternal._musicPlayerShutdown()

    _gMusicPlayerType = InternalMusicPlayer

elif (bs.getEnvironment()['platform'] == 'mac'
      and hasattr(bsInternal, '_iTunesInit')):

    class ITunesThread(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self._commandsAvailable = threading.Event()
            self._commands = []
            self._volume = 1.0
            self._currentPlaylist = None

        def run(self):
            bsInternal._setThreadName("BS_ITunesThread")
            # iTunes seems to be locking up sometimes when bombsquad quits.
            # I'm guessing it might be related to the scripting bridge app going
            # down when this thread dies.
            # ..so as a workaround, lets make it a global so it won't get killed
            global gITunesApp
            try: gITunesApp
            except Exception:
                bsInternal._iTunesInit()
                # it looks like launching iTunes here on 10.7/10.8 knocks us
                # out of fullscreen. Ew... that might be a bug, but for now we
                # can work around it by reactivating ourself after
                def doPrint():
                    bs.realTimer(1000, bs.Call(bs.screenMessage, bs.Lstr(
                        resource='usingItunesText'), (0, 1, 0)))
                bs.callInGameThread(doPrint)
                # here we grab this to force the actual launch
                # ..currently (on 10.8 at least) this is causing a switch
                # away from our fullscreen window. to work around this we
                # explicitly focus our main window to bring ourself back
                bsInternal._iTunesGetVolume()
                bs.callInGameThread(bsInternal._focusWindow)
            bsInternal._iTunesGetLibrarySource()
            done = False
            while not done:
                self._commandsAvailable.wait()
                self._commandsAvailable.clear()
                # (we're not protecting this list with a mutex but we're
                # just using it as a simple queue so it should be fine..)
                while len(self._commands) > 0:
                    cmd = self._commands.pop(0)
                    if cmd[0] == 'DIE':
                        # only stop if we've actually played something..
                        # (we don't want to kill music the user has playing)
                        if self._currentPlaylist and self._volume > 0:
                            try:
                                bsInternal._iTunesStop()
                                bsInternal._iTunesSetVolume(self._origVolume)
                            except Exception as e:
                                print 'Error stopping iTunes music:', e
                        done = True
                        break
                    elif cmd[0] == 'PLAY':
                        if cmd[1] is None:
                            if self._currentPlaylist and self._volume > 0:
                                try:
                                    bsInternal._iTunesStop()
                                    bsInternal._iTunesSetVolume(
                                        self._origVolume)
                                except Exception as e:
                                    print 'Error stopping iTunes music:', e
                            self._currentPlaylist = None
                        else:
                            # if we've got something playing with positive
                            # volume, stop it
                            if self._currentPlaylist and self._volume > 0:
                                try:
                                    bsInternal._iTunesStop()
                                    bsInternal._iTunesSetVolume(
                                        self._origVolume)
                                except Exception as e:
                                    print 'Error stopping iTunes music:', e
                            # set our playlist and play it if our volume is up
                            self._currentPlaylist = cmd[1]
                            if self._volume > 0:
                                self._origVolume = bsInternal._iTunesGetVolume()
                                self._updateITunesVolume()
                                self._playCurrentPlaylist()
                    elif cmd[0] == 'GET_PLAYLISTS':
                        try:
                            playlists = bsInternal._iTunesGetPlaylists()
                            playlists = [p for p in playlists if p not in [
                                'Music', 'Movies', 'TV Shows', 'Podcasts',
                                u'iTunes\xa0U', 'Books', 'Genius', 'iTunes DJ',
                                'Music Videos', 'Home Videos', 'Voice Memos',
                                'Audiobooks']]
                            playlists.sort(key=lambda x: x.lower())
                        except Exception as e:
                            print 'Error getting iTunes playlists:', e
                            playlists = []
                        bs.callInGameThread(bs.Call(cmd[1], playlists))

                    del cmd # allows the command data/callback/etc to be freed

        def _playCurrentPlaylist(self):
            try:
                if bsInternal._iTunesPlayPlaylist(self._currentPlaylist):
                    pass
                else:
                    bs.callInGameThread(bs.Call(bs.screenMessage, _getResource(
                        'playlistNotFoundText')+': \''+self._currentPlaylist
                                                +'\'', (1, 0, 0)))
            except Exception as e:
                try:
                    print ('Exception playing playlist "'
                           +self._currentPlaylist+'":'), e
                except Exception:
                    pass

        def _updateITunesVolume(self):
            bsInternal._iTunesSetVolume(
                max(0, min(100, int(100.0*self._volume))))

        def setVolume(self, volume):
            oldVolume = self._volume
            self._volume = volume

            # if we've got nothing we're supposed to be playing,
            # don't touch itunes..
            if self._currentPlaylist is None: return

            # if volume is going to zero, stop actually playing
            # but dont clear playlist
            if oldVolume > 0 and volume == 0:
                try:
                    bsInternal._iTunesStop()
                    bsInternal._iTunesSetVolume(self._origVolume)
                except Exception as e:
                    print 'Error stopping iTunes music:', e
            elif self._volume > 0:
                # if volume was zero, store pre-playing volume and start playing
                if oldVolume == 0:
                    self._origVolume = bsInternal._iTunesGetVolume()
                self._updateITunesVolume()
                if oldVolume == 0: self._playCurrentPlaylist()

        def playPlaylist(self, musicType):
            self._commands.append(['PLAY', musicType])
            self._commandsAvailable.set()

        def shutdown(self):
            self._commands.append(['DIE'])
            self._commandsAvailable.set()
            self.join()

        def getPlaylists(self, callback):
            self._commands.append(['GET_PLAYLISTS', callback])
            self._commandsAvailable.set()

    # define a music-player that talks to iTunes and lets us
    # select playlists as entries
    class MacITunesMusicPlayer(MusicPlayer):
        def __init__(self):
            MusicPlayer.__init__(self)
            self._thread = ITunesThread()
            self._thread.start()

        def onSelectEntry(self, callback, currentEntry, selectionTargetName):
            import bsUI
            return bsUI.GetSoundtrackEntryTypeWindow(callback, currentEntry,
                                                     selectionTargetName)
        def onSetVolume(self, volume):
            self._thread.setVolume(volume)

        def onPlay(self, entry):
            entryType = _getSoundtrackEntryType(entry)
            if entryType == 'iTunesPlaylist':
                self._thread.playPlaylist(_getSoundtrackEntryName(entry))
            else:
                print 'MacITunesMusicPlayer passed unrecognized entry type:', \
                    entryType

        def onStop(self):
            # pass
            self._thread.playPlaylist(None)

        def onShutdown(self):
            # pass
            self._thread.shutdown()

    _gMusicPlayerType = MacITunesMusicPlayer

def haveMusicPlayer():
    return (_gMusicPlayerType is not None)

def getMusicPlayer():
    global _gMusicPlayer
    if _gMusicPlayer is None:
        if _gMusicPlayerType is None:
            raise Exception("no music player type set")
        _gMusicPlayer = _gMusicPlayerType()
    return _gMusicPlayer

def _musicVolumeChanged(val):
    if _gMusicPlayer is not None:
        _gMusicPlayer.setVolume(val)
        
gMusicMode = 'regular'
gMusicTypes = {'regular':None, 'test':None}

def setMusicPlayMode(mode, forceRestart=False):
    global gMusicMode
    oldMode = gMusicMode
    gMusicMode = mode
    if oldMode != gMusicMode or forceRestart:
        # if we're switching into test mode we don't
        # actually play anything until its requested..
        # if we're switching *out* of test mode though
        # we want to go back to whatever the normal song was
        if mode == 'regular': _playMusic(gMusicTypes['regular'])

def _isSoundtrackEntryTypeSupported(entryType):
    ua = bs.getEnvironment()['userAgentString']
    if entryType == 'iTunesPlaylist':
        return True if 'Mac' in ua else False
    elif entryType in ('musicFile', 'musicFolder'):
        return True if ('android' in ua and \
                        bsInternal._androidGetExternalStoragePath() \
                        is not None) else False
    elif entryType == 'default':
        return True
        
def _getSoundtrackEntryType(entry):
    """Given a soundtrack entry, returns its type, taking into
    account what is supported locally."""
    try:
        if entry is None: entryType = u'default'
        # simple string denotes iTunesPlaylist (legacy format)
        elif type(entry) in (str, unicode): entryType = u'iTunesPlaylist'
        # for other entries we expect type and name strings in a dict
        elif (type(entry) is dict
              and 'type' in entry and type(entry['type']) in (str, unicode) 
              and 'name' in entry and type(entry['name']) in (str, unicode)):
            entryType = entry['type']
        else: raise Exception("invalid soundtrack entry: "+str(entry)
                              +" (type "+str(type(entry))+")")
        if _isSoundtrackEntryTypeSupported(entryType): return entryType
        else: raise Exception("invalid soundtrack entry:"+str(entry))
    except Exception as e:
        print 'EXC on _getSoundtrackEntryType', e
        return 'default'

def _getSoundtrackEntryName(entry):
    """Given a soundtrack entry, returns its name. Note that this does
    not ensure the entry is valid (use _getSoundtrackEntryType() for that)."""
    try:
        if entry is None: return None
        # simple string denotes an iTunesPlaylist name (legacy entry format)
        elif type(entry) is unicode: return entry
        elif type(entry) is str: return entry
        # for other entries we expect type and name strings in a dict
        elif (type(entry) is dict
              and 'type' in entry and type(entry['type']) in (str, unicode) 
              and 'name' in entry and type(entry['name']) in (str, unicode)):
            return entry['name']
        else: raise Exception("invalid soundtrack entry:"+str(entry))
    except Exception as e:
        print 'EXC on _getSoundtrackEntryName', e
        return 'default'

def playMusic(musicType, continuous=False):
    """
    category: Game Flow Functions

    A high level function to set or stop the current music based on a
    string musicType.
    
    Current valid values for 'musicType': 'Menu', 'Victory', 'CharSelect',
    'RunAway', 'Onslaught', 'Keep Away', 'Race', 'Epic Race', 'Scores',
    'GrandRomp', 'ToTheDeath', 'Chosen One', 'ForwardMarch', 'FlagCatcher',
    'Survival', 'Epic', 'Sports', 'Hockey', 'Football', 'Flying', 'Scary',
    'Marching'.

    This function will handle loading and playing sound media as necessary,
    and also supports custom user soundtracks on specific platforms so the
    user can override particular game music with their own.

    Pass None to stop music.

    if 'continuous' is True the musicType passed is the same as what is already
    playing, the playing track will not be restarted.
    """
    # all we do here now is set a few music attrs on the current globals
    # node; the foreground globals' current playing music then gets fed to
    # the _playMusic call below.. this way we can seamlessly support custom
    # soundtracks in replays/etc since we're replaying an attr value set;
    # not an actual sound node create
    g = bs.getSharedObject('globals')
    g.musicContinuous = continuous
    g.music = '' if musicType is None else musicType
    g.musicCount += 1
    
def _playMusic(musicType, continuous=False,
               mode='regular', testSoundtrack=None):
    "Actually plays the requested music type/mode"
    with bs.Context('UI'):
        # if they dont want to restart music and we're already
        # playing what's requested, we're done
        if continuous and gMusicTypes[mode] == musicType: return
        gMusicTypes[mode] = musicType
        bsConfig = bs.getConfig()

        # if the OS tells us there's currently music playing,
        # all our operations default to playing nothing
        if bsInternal._isOSPlayingMusic(): musicType = None

        # if we're not in the mode this music is being set for,
        # don't actually change what's playing
        if mode != gMusicMode: return

        # some platforms have a special music-player for things like iTunes
        # soundtracks, mp3s, etc. if this is the case, attempt to grab an
        # entry for this music-type, and if we have one, have the music-player
        # play it.  If not, we'll play game music ourself
        if musicType is not None and _gMusicPlayerType is not None:
            try:
                if testSoundtrack is not None:
                    soundtrack = testSoundtrack
                else:
                    soundtrack = bsConfig['Soundtracks'][bsConfig['Soundtrack']]
                entry = soundtrack[musicType]
            except Exception:
                entry = None
        else: entry = None

        # go through music-player
        if entry is not None:

            # stop any existing internal music..
            global gMusic
            if gMusic is not None:
                gMusic.delete()
                gMusic = None

            # play music-player music..
            getMusicPlayer().play(entry)

        # handle via internal music...
        else:
            if musicType is not None:
                loop = True
                if musicType == 'Menu':
                    filename = 'menuMusic'
                    volume = 5.0
                elif musicType == 'Victory':
                    filename = 'victoryMusic'
                    volume = 6.0
                    loop = False
                elif musicType == 'CharSelect':
                    filename = 'charSelectMusic'
                    volume = 2.0
                elif musicType == 'RunAway':
                    filename = 'runAwayMusic'
                    volume = 6.0
                elif musicType == 'Onslaught':
                    filename = 'runAwayMusic'
                    volume = 6.0
                elif musicType == 'Keep Away':
                    filename = 'runAwayMusic'
                    volume = 6.0
                elif musicType == 'Race':
                    filename = 'runAwayMusic'
                    volume = 6.0
                elif musicType == 'Epic Race':
                    filename = 'slowEpicMusic'
                    volume = 6.0
                elif musicType == 'Scores':
                    filename = 'scoresEpicMusic'
                    volume = 3.0
                    loop = False
                elif musicType == 'GrandRomp':
                    filename = 'grandRompMusic'
                    volume = 6.0
                elif musicType == 'ToTheDeath':
                    filename = 'toTheDeathMusic'
                    volume = 6.0
                elif musicType == 'Chosen One':
                    filename = 'survivalMusic'
                    volume = 4.0
                elif musicType == 'ForwardMarch':
                    filename = 'forwardMarchMusic'
                    volume = 4.0
                elif musicType == 'FlagCatcher':
                    filename = 'flagCatcherMusic'
                    volume = 6.0
                elif musicType == 'Survival':
                    filename = 'survivalMusic'
                    volume = 4.0
                elif musicType == 'Epic':
                    filename = 'slowEpicMusic'
                    volume = 6.0
                elif musicType == 'Sports':
                    filename = 'sportsMusic'
                    volume = 4.0
                elif musicType == 'Hockey':
                    filename = 'sportsMusic'
                    volume = 4.0
                elif musicType == 'Football':
                    filename = 'sportsMusic'
                    volume = 4.0
                elif musicType == 'Flying':
                    filename = 'flyingMusic'
                    volume = 4.0
                elif musicType == 'Scary':
                    filename = 'scaryMusic'
                    volume = 4.0
                elif musicType == 'Marching':
                    filename = 'whenJohnnyComesMarchingHomeMusic'
                    volume = 4.0
                else:
                    print "Unknown music: '"+musicType+"'"
                    filename = 'flagCatcherMusic'
                    volume = 6.0

            # stop any existing music-player playback
            if _gMusicPlayer is not None:
                _gMusicPlayer.stop()

            # stop any existing internal music..
            if gMusic is not None and gMusic.exists():
                gMusic.delete()
                gMusic = None

            # start up new internal music..
            if musicType is not None:
                # fixme - currently this won't start playing if we're paused
                # since attr values don't get updated until
                # node updates happen  :-(
                #with bs.Context(bs.getSession()):
                gMusic = bs.newNode(type='sound', attrs={
                    'sound':bs.getSound(filename),
                    'positional':False,
                    'music':True,
                    'volume':volume,
                    'loop':loop})

class Spawner(object):
    """
    category: Game Flow Classes

    Creates a light flash and sends a bs.Spawner.SpawnMessage
    to the current activity after a delay.
    """
    
    class SpawnMessage(object):
        """
        category: Message Classes

        Spawn message sent by a bs.Spawner after its delay has passed.

        Attributes:

           spawner
              The bs.Spawner we came from.

           data
              The data object passed by the user.

           pt
              The spawn position.
        """
        def __init__(self, spawner, data, pt):
            """
            Instantiate with the given values.
            """
            self.spawner = spawner
            self.data = data
            self.pt = pt
        
    def __init__(self, data=None, pt=(0, 0, 0), spawnTime=1000,
                 sendSpawnMessage=True, spawnCallback=None):
        """
        Instantiate a spawner given some custom data,
        a position, and a spawn-time in milliseconds.
        """
        self._spawnCallback = spawnCallback
        self._sendSpawnMessage = sendSpawnMessage
        self._spawnerSound = bs.getSound('swip2')
        self._data = data
        self._pt = pt
        # create a light where the spawn will happen
        self._light = bs.newNode('light', attrs={
            'position':tuple(pt),
            'radius':0.1,
            'color':(1.0, 0.1, 0.1),
            'lightVolumes':False})
        s = float(spawnTime)/3750
        minVal = 0.4
        maxVal = 0.7
        bs.playSound(self._spawnerSound, position=self._light.position)
        animate(self._light, 'intensity', {
            0:0.0, int(250*s):maxVal, int(500*s):minVal, int(750*s):maxVal,
            int(1000*s):minVal, int(1250*s):1.1*maxVal, int(1500*s):minVal,
            int(1750*s):1.2*maxVal, int(2000*s):minVal, int(2250*s):1.3*maxVal,
            int(2500*s):minVal, int(2750*s):1.4*maxVal, int(3000*s):minVal,
            int(3250*s):1.5*maxVal, int(3500*s):minVal, int(3750*s):2.0,
            int(4000*s):0.0})
        bs.gameTimer(int(spawnTime), self._spawn)

    def _spawn(self):

        bs.gameTimer(1000, self._light.delete)

        if self._spawnCallback is not None:
            self._spawnCallback()
            
        if self._sendSpawnMessage:
            # only run if our activity still exists
            activity = bs.getActivity()
            if activity is not None:
                activity.handleMessage(
                    self.SpawnMessage(self, self._data, self._pt))

def isPointInBox(p, b):
    """
    category: General Utility Functions

    Return whether a given point is within a given box.
    For use with standard def boxes (position|rotate|scale).
    """
    return ((abs(p[0]-b[0]) <= b[6]*0.5) and (abs(p[1]-b[1]) <= b[7]*0.5)
            and (abs(p[2]-b[2]) <= b[8]*0.5))

def getPlayerProfileIcon(profileName):
    """ given a profile, returns an icon string for it
    (non-account profiles only) """

    bsConfig = bs.getConfig()
    try: isGlobal = bsConfig['Player Profiles'][profileName]['global']
    except Exception: isGlobal = False
    if isGlobal:
        try: icon = bsConfig['Player Profiles'][profileName]['icon']
        except Exception: icon = bs.getSpecialChar('logo')
    else:
        icon = ''
    return bs.uni(icon)
    
def getPlayerProfileColors(profileName, profiles=None):
    """ given a profile, returns colors for them """
    bsConfig = bs.getConfig()
    if profiles is None: profiles = bsConfig['Player Profiles']

    # special case - when being asked for a random color in kiosk mode,
    # always return default purple
    if gRunningKioskModeGame and profileName is None:
        color = (0.5, 0.4, 1.0)
        highlight = (0.4, 0.4, 0.5)
    else:
        try: color = profiles[profileName]['color']
        except Exception:
            # key off name if possible
            if profileName is None:
                # first 6 are bright-ish
                color = _gPlayerColors[random.randrange(6)]
            else:
                # first 6 are bright-ish
                color = _gPlayerColors[sum([ord(c) for c in profileName]) % 6]

        try: highlight = profiles[profileName]['highlight']
        except Exception:
            # key off name if possible
            if profileName is None:
                # last 2 are grey and white; ignore those or we
                # get lots of old-looking players
                highlight = _gPlayerColors[
                    random.randrange(len(_gPlayerColors)-2)]
            else:
                highlight = _gPlayerColors[sum([ord(c)+1 for c in profileName])
                                           % (len(_gPlayerColors)-2)]

    return color, highlight

def getTimeString(t, centi=True):
    """
    category: General Utility Functions
    
    Given a value in milliseconds, returns a Lstr with:
    (hours if > 0):minutes:seconds:centiseconds.
    WARNING: this Lstr value is somewhat large so don't use this to
    repeatedly update node values in a timer/etc. For that purpose you
    should use timeDisplay nodes and attribute connections.
    """
    if type(t) is not int: t = int(t)
    bits = []
    subs = []
    h = (t/1000)/(60*60)
    if h != 0:
        bits.append('${H}')
        subs.append(('${H}', bs.Lstr(resource='timeSuffixHoursText',
                                     subs=[('${COUNT}', str(h))])))
    m = ((t/1000)/60)%60
    if m != 0:
        bits.append('${M}')
        subs.append(('${M}', bs.Lstr(resource='timeSuffixMinutesText',
                                     subs=[('${COUNT}', str(m))])))
        
    # we add seconds if its non-zero *or* we havn't added anything else
    if centi:
        s = (t/1000.0 % 60.0)
        if s >= 0.005 or not bits:
            bits.append('${S}')
            subs.append(('${S}', bs.Lstr(resource='timeSuffixSecondsText',
                                         subs=[('${COUNT}', ('%.2f' % s))])))
    else:
        s = (t/1000 % 60)
        if s != 0 or not bits:
            bits.append('${S}')
            subs.append(('${S}', bs.Lstr(resource='timeSuffixSecondsText',
                                         subs=[('${COUNT}', str(s))])))
    return bs.Lstr(value=' '.join(bits), subs=subs)
    
def showDamageCount(damage, position, direction):
    lifespan = 1000
    env = bs.getEnvironment()
    doBig = env['interfaceType'] == 'small' or env['vrMode']
    t = bs.newNode('text', attrs={
        'text':damage,
        'inWorld':True,
        'hAlign':'center',
        'flatness':1.0,
        'shadow':1.0 if doBig else 0.7,
        'color':(1, 0.25, 0.25, 1),
        'scale':0.015 if doBig else 0.01})
    # translate upward
    tcombine = bs.newNode("combine", owner=t, attrs={'size':3})
    tcombine.connectAttr('output', t, 'position')
    vVals = []
    p = 0; v = 0.07
    count = 6
    for i in range(count):
        vVals.append((float(i)/count, p))
        p += v
        v *= 0.5
    pStart = position[0]; pDir = direction[0]
    animate(tcombine, "input0",
            dict([[i[0]*lifespan, pStart+pDir*i[1]] for i in vVals]))
    pStart = position[1]; pDir = direction[1]
    animate(tcombine, "input1",
            dict([[i[0]*lifespan, pStart+pDir*i[1]] for i in vVals]))
    pStart = position[2]; pDir = direction[2]
    animate(tcombine, "input2",
            dict([[i[0]*lifespan, pStart+pDir*i[1]] for i in vVals]))
    animate(t, 'opacity', {0.7*lifespan:1.0, lifespan:0.0})
    bs.gameTimer(lifespan, t.delete)

def getLastPlayerNameFromInputDevice(device):
    """Returns a reasonable player name associated with a device
    (generally the last one used there)"""
    bsConfig = bs.getConfig()
    # look for a default player profile name for them..
    # otherwise default to their current random name
    profileName = '_random'
    keyName = device.getName()+' '+device.getUniqueIdentifier()
    if ('Default Player Profiles' in bsConfig
            and keyName in bsConfig['Default Player Profiles']):
        profileName = bsConfig['Default Player Profiles'][keyName]
    if profileName == '_random':
        profileName = device._getDefaultPlayerName()
    if profileName == '__account__':
        profileName = bsInternal._getAccountDisplayString()
    return profileName

def getNormalizedColor(color):
    """
    category: General Utility Functions

    Scale a color so its largest value is 1; useful for coloring lights.
    """
    colorBiased = tuple(max(c, 0.01) for c in color) # account for black
    mult = 1.0/max(colorBiased)
    return tuple(c*mult for c in colorBiased)

def garbageCollect(sessionEnd=True):
    gc.collect()
    # can be handy to print this to check for leaks between games
    if 0: print 'PY OBJ COUNT', len(gc.get_objects())
    if len(gc.garbage) > 0:
        print 'PTHON GC FOUND', len(gc.garbage), 'UNCOLLECTABLE OBJECTS:'
        for i, obj in enumerate(gc.garbage):
            print str(i)+':', obj
    if sessionEnd:
        printLiveObjectWarnings('after session shutdown')

def printRefs(obj):
    "Handy function to print a list of live references to an object"
    # hmmm i just noticed that calling this on an object
    # seemed to keep it alive..
    print 'REFERENCES FOR', obj, ':'
    refs = list(gc.get_referrers(obj))
    i = 1
    for ref in refs:
        print '     ref', i, ':', ref
        i += 1
    
def printLiveObjectWarnings(when, ignoreSession=None, ignoreActivity=None):
    sessions = []
    activities = []
    actors = []
    global _gPrintedLiveObjectWarning
    
    if _gPrintedLiveObjectWarning:
        # print 'skipping live obj check due to previous found live object(s)'
        return
    for obj in gc.get_objects():
        if isinstance(obj, bs.Actor): actors.append(obj)
        elif isinstance(obj, bs.Session): sessions.append(obj)
        elif isinstance(obj, bs.Activity): activities.append(obj)
    # complain about any remaining sessions
    for session in sessions:
        if session is ignoreSession: continue
        _gPrintedLiveObjectWarning = True
        print 'ERROR: Session found', when, ':', session
        # refs = list(gc.get_referrers(session))
        # i = 1
        # for ref in refs:
        #     if type(ref) is types.FrameType: continue
        #     print '     ref', i, ':', ref
        #     i += 1
            # if type(ref) is list or type(ref) is tuple or type(ref) is dict:
            #     refs2 = list(gc.get_referrers(ref))
            #     j = 1
            #     for ref2 in refs2:
            #         if type(ref2) is types.FrameType: continue
            #         print '        ref\'s ref', j, ':', ref2
            #         j += 1

    # complain about any remaining activities
    for activity in activities:
        if activity is ignoreActivity: continue
        _gPrintedLiveObjectWarning = True
        print 'ERROR: Activity found', when, ':', activity
        # refs = list(gc.get_referrers(activity))
        # i = 1
        # for ref in refs:
        #     if type(ref) is types.FrameType: continue
        #     print '     ref', i, ':', ref
        #     i += 1
            # if type(ref) is list or type(ref) is tuple or type(ref) is dict:
            #     refs2 = list(gc.get_referrers(ref))
            #     j = 1
            #     for ref2 in refs2:
            #         if type(ref2) is types.FrameType: continue
            #         print '        ref\'s ref', j, ':', ref2
            #         j += 1

    # complain about any remaining actors
    for actor in actors:
        _gPrintedLiveObjectWarning = True
        print 'ERROR: Actor found', when, ':', actor
        if type(actor) is bs.Actor:
            try:
                if actor.node.exists():
                    print '   - contains node:', \
                        actor.node.getNodeType(), ';', actor.node.getName()
            except Exception as e:
                print '   - exception checking actor node:', e
        # refs = list(gc.get_referrers(actor))
        # i = 1
        # for ref in refs:
        #     if type(ref) is types.FrameType: continue
        #     print '     ref', i, ':', ref
        #     i += 1
            # if type(ref) is list or type(ref) is tuple or type(ref) is dict:
            #     refs2 = list(gc.get_referrers(ref))
            #     j = 1
            #     for ref2 in refs2:
            #         if type(ref2) is types.FrameType: continue
            #         print '        ref\'s ref', j, ':', ref2
            #         j += 1


def _isValidRemainingNode(node):
    return (node.getName() in ['Globals'])

def _weakDeleteNode(node, weakRef):
    node.delete()

def _setNodeOwner(node, owner):

    # ..owner can be an activity..
    if isinstance(owner, bs.Activity):
        print ('WARNING: explicitly passing a bs.Activity as node owner is no '
               'longer allowed; that is default behavior')
        import traceback
        traceback.print_stack()

    # allow actors..
    # FIXME - should add this functionality explicitly to actors,
    # the way we do with activities. I don't like the idea of a global ref
    # list (if there's a leak it'll slow down the game eventually)
    else:
        # not *requiring* actors only just yet; just checking for it..
        if not isinstance(owner, bs.Actor):
            print 'ERROR; passed node owner not an activity/actor; got', owner
            import traceback
            traceback.print_stack()
        global gNodeOwnerWeakRefs
        global gNodeOwnerWeakRefsCleanCounter
        gNodeOwnerWeakRefs.append(weakref.ref(owner,
                                              bs.Call(_weakDeleteNode, node)))
        gNodeOwnerWeakRefsCleanCounter += 1
        # pull dead refs off our list periodically (I supposed the callback
        # could do it, but this works)
        if (gNodeOwnerWeakRefsCleanCounter > 10):
            oldSize = len(gNodeOwnerWeakRefs)
            gNodeOwnerWeakRefs = \
                [r for r in gNodeOwnerWeakRefs if r() is not None]
            gNodeOwnerWeakRefsCleanCounter = 0

class ServerCallThread(threading.Thread):
        
    def __init__(self, request, requestType, data, callback):
        threading.Thread.__init__(self)
        self._request = request
        self._requestType = requestType
        self._data = {} if data is None else copy.deepcopy(data)
        self._callback = callback
        self._context = bs.Context('current')
        # save and restore the context we were created from
        activity = bs.getActivity(exceptionOnNone=False)
        self._activity = weakref.ref(activity) if activity is not None else None
        
    def _runCallback(self, arg):
        
        # if we were created in an activity context and that activity has
        # since died, do nothing (hmm should we be using a context-call
        # instead of doing this manually?)
        if (self._activity is not None
            and (self._activity() is None
                 or self._activity().isFinalized())): return
        
        # (technically we could do the same check for session contexts,
        # but not gonna worry about it for now)
        with self._context: self._callback(arg)
        
    def run(self):
        try:
            self._data = toUTF8(self._data)
            bsInternal._setThreadName("BS_ServerCallThread")

            if self._requestType == 'get':
                response = urllib2.urlopen(urllib2.Request(
                    # fails with unicode for some reason
                    str(bsInternal._get_master_server_address()+'/'+self._request
                        +'?'+urllib.urlencode(self._data)), 
                    None,
                    { 'User-Agent' : bs.getEnvironment()['userAgentString'] }))
            elif self._requestType == 'post':
                response = urllib2.urlopen(urllib2.Request(
                    # this fails with unicode for some reason
                    str(bsInternal._get_master_server_address()+'/'+self._request),
                    urllib.urlencode(self._data),
                    { 'User-Agent' : bs.getEnvironment()['userAgentString'] }))
            else: raise Exception("Invalid requestType: "+self._requestType)
            responseData = ast.literal_eval(response.read())
            if self._callback is not None:
                bs.callInGameThread(bs.Call(self._runCallback, responseData))
        except Exception as e:
            if self._callback is not None:
                bs.callInGameThread(bs.Call(self._runCallback, None))

def serverGet(request, data, callback=None):
    ServerCallThread(request, 'get', data, callback).start()

def serverPut(request, data, callback=None):
    ServerCallThread(request, 'post', data, callback).start()

def runGPUBenchmark():
    bs.screenMessage("FIXME: not wired up yet", color=(1, 0, 0))

def runMediaReloadBenchmark():
    bs.reloadMedia()
    bsInternal._showProgressBar()
    def delayAdd(startTime):
        def foo(startTime):
            bs.screenMessage(
                _getResource('debugWindow.totalReloadTimeText')\
                .replace('${TIME}', str(bs.getRealTime()-startTime)))
            bsInternal._printLoadInfo()
            if bsInternal._getSetting("Texture Quality") != 'High':
                bs.screenMessage(_getResource(
                    'debugWindow.reloadBenchmarkBestResultsText'),
                                 color=(1, 1, 0))
        bsInternal._addCleanFrameCallback(bs.Call(foo, startTime))
    # the reload starts (should add a completion callback to the
    # reload func to fix this)
    bs.realTimer(50, bs.Call(delayAdd, bs.getRealTime()))
    
def _printCorruptFileError():
    bs.realTimer(2000, bs.Call(
        bs.screenMessage, _getResource('internal.corruptFileText')\
        .replace('${EMAIL}', 'support@froemling.net'), color=(1, 0, 0)))
    bs.realTimer(2000, bs.Call(bs.playSound, bs.getSound('error')))
    
def runCPUBenchmark():
    import bsTutorial
    class BenchmarkSession(bs.Session):
        def __init__(self):
            bs.Session.__init__(self)
            # store old graphics settings
            self._oldQuality = bsInternal._getSetting('Graphics Quality')
            bs.getConfig()['Graphics Quality'] = "Low"
            bs.applySettings()
            self.benchmarkType = 'cpu'
            self.setActivity(bs.newActivity(bsTutorial.TutorialActivity))
            
        def __del__(self):
            # when we're torn down, restore old graphics settings
            bs.getConfig()['Graphics Quality'] = self._oldQuality
            bs.applySettings()
            
        def onPlayerRequest(self, player):
            return False
    bsInternal._newHostSession(BenchmarkSession, benchmarkType='cpu')
    
def runStressTest(playlistType='Random', playlistName='__default__',
                  playerCount=8, roundDuration=30):
    bs.screenMessage('Beginning stress test.. use '
                     '\'End Game\' to stop testing.',
                     color=(1, 1, 0))
    with bs.Context('UI'):
        _startStressTest({
            'playlistType':playlistType,
            'playlistName':playlistName,
            'playerCount':playerCount,
            'roundDuration':roundDuration})
        bs.realTimer(7000, bs.Call(
            bs.screenMessage, ('stats will be written to '
                              + getHumanReadableUserScriptsPath()
                              + '/stressTestStats.csv')))
        
_gStressTestResetTimer = None

def stopStressTest():
    bsInternal._setStressTesting(False, 0)
    global _gStressTestResetTimer
    try:
        if _gStressTestResetTimer is not None:
            bs.screenMessage("Ending stress test...", color=(1, 1, 0))
    except Exception: pass
    _gStressTestResetTimer = None

def _startStressTest(args):
    bsConfig = bs.getConfig()
    playlistType = args['playlistType']
    if playlistType == 'Random':
        if (random.random() < 0.5): playlistType = 'Teams'
        else: playlistType = 'Free-For-All'
    bs.screenMessage('Running Stress Test (listType="'
                     + playlistType + '", listName="'
                     + args['playlistName']+'")...')
    if playlistType == 'Teams':
        bsConfig['Team Tournament Playlist Selection'] = args['playlistName']
        bsConfig['Team Tournament Playlist Randomize'] = 1
        bs.realTimer(1000, bs.Call(bs.pushCall, bs.Call(
            bsInternal._newHostSession, bs.TeamsSession)))
    else:
        bsConfig['Free-for-All Playlist Selection'] = args['playlistName']
        bsConfig['Free-for-All Playlist Randomize'] = 1
        bs.realTimer(1000, bs.Call(bs.pushCall, bs.Call(
            bsInternal._newHostSession, bs.FreeForAllSession)))
    bsInternal._setStressTesting(True, args['playerCount'])
    global _gStressTestResetTimer
    _gStressTestResetTimer = bs.Timer(args['roundDuration']*1000,
                                      bs.Call(_resetStressTest, args),
                                      timeType='real')

def _resetStressTest(args):
    bsInternal._setStressTesting(False, args['playerCount'])
    bs.screenMessage('Resetting stress test...')
    bsInternal._getForegroundHostSession().end()
    bs.realTimer(1000, bs.Call(_startStressTest, args))

class ControlsHelpOverlay(bsGame.Actor):
    """
    category: Game Flow Classes

    A screen overlay of game controls, showing button mappings
    based on what controllers are connected. Handy to show at the
    start of a series or whenever there might be newbies watching.
    """
    def __init__(self, position=(390, 120), scale=1.0,
                 delay=0, lifespan=None, bright=False):
        """
        Instantiate an overlay.

        delay: is the time in milliseconds before the overlay fades in.

        lifespan: if not None, the overlay will fade back out and die after
                  that long (in milliseconds).

        bright: if True, brighter colors will be used; handy when showing
                over gameplay but may be too bright for join-screens, etc.
        """
        bsGame.Actor.__init__(self)
        showTitle = True
        scale *= 0.75
        imageSize = 90.0*scale
        offs = 74.0*scale
        offs5 = 43.0*scale
        ouya = bsInternal._isRunningOnOuya()
        mw = 50
        shadOffs = 2.0*scale
        self._lifespan = lifespan
        self._dead = False
        self._bright = bright
        if showTitle:
            self._titleTextPosTop = (position[0], position[1]+139.0*scale)
            self._titleTextPosBottom = (position[0], position[1]+139.0*scale)
            c = (1, 1, 1) if bright else (0.7, 0.7, 0.7)
            self._titleText = bs.newNode('text', attrs={
                'text':bs.Lstr(value='${A}:',
                               subs=[('${A}',
                                      bs.Lstr(resource='controlsText'))]),
                'hostOnly':True,
                'scale':1.1*scale,
                'shadow':0.5,
                'flatness':1.0,
                'maxWidth':480,
                'vAlign':'center', 'hAlign':'center',
                'color':c})
        else:
            self._titleText = None
        p = (position[0], position[1]-offs)
        c = (0.4, 1, 0.4)
        self._jumpImage = bs.newNode('image', attrs={
            'texture':bs.getTexture('buttonJump'), 'absoluteScale':True,
            'hostOnly':True, 'vrDepth':10, 'position':p,
            'scale':(imageSize, imageSize), 'color':c})
        self._jumpText = bs.newNode('text', attrs={
            'vAlign':'top', 'hAlign':'center', 'scale':1.5*scale,
            'flatness':1.0, 'hostOnly':True, 'shadow':1.0, 'maxWidth':mw,
            'position':(p[0], p[1]-offs5), 'color':c})
        p = (position[0]-offs*1.1, position[1])
        c = (0.2, 0.6, 1) if ouya else (1, 0.7, 0.3)
        self._punchImage = bs.newNode('image', attrs={
            'texture':bs.getTexture('buttonPunch'), 'absoluteScale':True,
            'hostOnly':True, 'vrDepth':10, 'position':p,
            'scale':(imageSize, imageSize), 'color':c})
        self._punchText = bs.newNode('text', attrs={
            'vAlign':'top', 'hAlign':'center', 'scale':1.5*scale,
            'flatness':1.0, 'hostOnly':True,
            'shadow':1.0, 'maxWidth':mw, 'position':(p[0], p[1]-offs5),
            'color':c})
        p = (position[0]+offs*1.1, position[1])
        c = (1, 0.3, 0.3)
        self._bombImage = bs.newNode('image', attrs={
            'texture':bs.getTexture('buttonBomb'), 'absoluteScale':True,
            'hostOnly':True, 'vrDepth':10, 'position':p,
            'scale':(imageSize, imageSize), 'color':c})
        self._bombText = bs.newNode('text', attrs={
            'hAlign':'center', 'vAlign':'top', 'scale':1.5*scale,
            'flatness':1.0, 'hostOnly':True, 'shadow':1.0, 'maxWidth':mw,
            'position':(p[0], p[1]-offs5), 'color':c})
        p = (position[0], position[1]+offs)
        c = (1, 0.8, 0.3) if ouya else (0.8, 0.5, 1)
        self._pickUpImage = bs.newNode('image', attrs={
            'texture':bs.getTexture('buttonPickUp'), 'absoluteScale':True,
            'hostOnly':True, 'vrDepth':10, 'position':p,
            'scale':(imageSize, imageSize), 'color':c})
        self._pickUpText = bs.newNode('text', attrs={
            'vAlign':'top', 'hAlign':'center', 'scale':1.5*scale,
            'flatness':1.0, 'hostOnly':True, 'shadow':1.0, 'maxWidth':mw,
            'position':(p[0], p[1]-offs5), 'color':c})
        c = (0.9, 0.9, 2.0) if bright else (0.8, 0.8, 2.0, 1.0)
        self._runTextPosTop = (position[0], position[1] - 135.0*scale)
        self._runTextPosBottom = (position[0], position[1] - 172.0*scale)
        self._runText = bs.newNode('text', attrs={
            'scale':1.0*scale if bs.getEnvironment()['vrMode'] else 0.8*scale,
            'hostOnly':True,
            'shadow':1.0 if bs.getEnvironment()['vrMode'] else 0.5,
            'flatness':1.0,
            'maxWidth':380,
            'vAlign':'top', 'hAlign':'center',
            'color':c})
        c = (1, 1, 1) if bright else (0.7, 0.7, 0.7)
        self._extraText = bs.newNode('text', attrs={
            'scale':0.8*scale,
            'hostOnly':True,
            'shadow':0.5,
            'flatness':1.0,
            'maxWidth':380,
            'vAlign':'top', 'hAlign':'center',
            'color':c})
        self._nodes = [self._bombImage, self._bombText,
                       self._punchImage, self._punchText,
                       self._jumpImage, self._jumpText,
                       self._pickUpImage, self._pickUpText,
                       self._runText, self._extraText]
        if showTitle: self._nodes.append(self._titleText)
        # start everything invisible
        for n in self._nodes:
            n.opacity = 0.0
        # dont do anything until our delay has passed
        bs.gameTimer(delay, bs.WeakCall(self._startUpdating))

    def _startUpdating(self):
        # ok, our delay has passed.. now lets periodically see if we can fade in
        # (if a touch-screen is present we only want to show up if gamepads
        # are connected, etc)
        # ...also set up a timer so if we havnt faded in by the end of our
        # duration, abort.
        if self._lifespan is not None:
            self._cancelTimer = bs.Timer(self._lifespan, bs.WeakCall(
                self.handleMessage, bs.DieMessage(immediate=True)))
        self._fadeInTimer = bs.Timer(1000, bs.WeakCall(self._checkFadeIn),
                                     repeat=True)
        self._checkFadeIn() # do one check immediately

    def _checkFadeIn(self):
        import bsUI
        
        # if we have a touchscreen, we only fade in if we have a player with 
        # an input device that is *not* the touchscreen
        touchscreen = bsInternal._getInputDevice('TouchScreen', '#1',
                                                 exceptionOnNone=False)
        if touchscreen is not None:
            # we look at the session's players; not the activity's
            # - we want to get ones who are still in the process of
            # selecting a character, etc.
            inputDevices = [p.getInputDevice() for p in bs.getSession().players]
            inputDevices = [i for i in inputDevices if i is not None
                            and i.exists() and i is not touchscreen]
            fadeIn = False
            if len(inputDevices) > 0:
                # only count this one if it has non-empty button names
                # (filters out wiimotes, the remote-app, etc)
                for device in inputDevices:
                    for name in ('buttonPunch', 'buttonJump',
                                 'buttonBomb', 'buttonPickUp'):
                        if device.getButtonName(
                                bsUI.getControllerValue(device, name)) != '':
                            fadeIn = True
                            break
                    if fadeIn: break # no need to keep looking
        else:
            # no touch-screen; fade in immediately
            fadeIn = True
        if fadeIn:
            self._cancelTimer = None # didnt need this
            self._fadeInTimer = None # done with this
            self._fadeIn()
        
    def _fadeIn(self):
        for n in self._nodes:
            bs.animate(n, 'opacity', {0:0.0, 2000:1.0})
                
        # if we were given a lifespan, transition out after it..
        if self._lifespan is not None:
            bs.gameTimer(self._lifespan,
                         bs.WeakCall(self.handleMessage, bs.DieMessage()))
        self._update()
        self._updateTimer = bs.Timer(1000, bs.WeakCall(self._update),
                                     repeat=True)
    def _update(self):
        import bsUI
        if self._dead: return
        punchButtonNames = set()
        jumpButtonNames = set()
        pickUpButtonNames = set()
        bombButtonNames = set()

        # we look at the session's players; not the activity's - we want to
        # get ones who are still in the process of selecting a character, etc.
        inputDevices = [p.getInputDevice() for p in bs.getSession().players]
        inputDevices = [i for i in inputDevices if i is not None and i.exists()]

        # if there's no players with input devices yet, try to default to
        # showing keyboard controls
        if len(inputDevices) == 0:
            kb = bsInternal._getInputDevice('Keyboard', '#1',
                                            exceptionOnNone=False)
            if kb is not None: inputDevices.append(kb)
        
        # we word things specially if we have nothing but keyboards..
        allKeyboards = (len(inputDevices) > 0
                        and all(i.getName() == 'Keyboard'
                                for i in inputDevices))
        onlyRemote = (len(inputDevices) == 1
                        and all(i.getName() == 'Amazon Fire TV Remote'
                                for i in inputDevices))
        if allKeyboards:
            rightButtonNames = set()
            leftButtonNames = set()
            upButtonNames = set()
            downButtonNames = set()
            
        # for each player in the game with an input device,
        # get the name of the button for each of these 4 actions.
        # if any of them are uniform across all devices, display the name
        for device in inputDevices:
            # (we only care about movement buttons in the case of keyboards)
            if allKeyboards:
                rightButtonNames.add(device.getButtonName(
                    bsUI.getControllerValue(device, 'buttonRight')))
                leftButtonNames.add(device.getButtonName(
                    bsUI.getControllerValue(device, 'buttonLeft')))
                downButtonNames.add(device.getButtonName(
                    bsUI.getControllerValue(device, 'buttonDown')))
                upButtonNames.add(device.getButtonName(
                    bsUI.getControllerValue(device, 'buttonUp')))
            # ignore empty values; things like the remote app or
            # wiimotes can return these..
            bname = device.getButtonName(
                bsUI.getControllerValue(device, 'buttonPunch'))
            if bname != '': punchButtonNames.add(bname)
            bname = device.getButtonName(
                bsUI.getControllerValue(device, 'buttonJump'))
            if bname != '': jumpButtonNames.add(bname)
            bname = device.getButtonName(
                bsUI.getControllerValue(device, 'buttonBomb'))
            if bname != '': bombButtonNames.add(bname)
            bname = device.getButtonName(
                bsUI.getControllerValue(device, 'buttonPickUp'))
            if bname != '': pickUpButtonNames.add(bname)

        # if we have no values yet, we may want to throw out some sane defaults
        if all(len(l) == 0 for l in (punchButtonNames, jumpButtonNames,
                                     bombButtonNames, pickUpButtonNames)):
            # show ouya buttons
            if bsInternal._isRunningOnOuya():
                # FIXME - should look at the ouya controller config;
                # not just list defaults
                punchButtonNames.add(bs.getSpecialChar('ouyaButtonU'))
                jumpButtonNames.add(bs.getSpecialChar('ouyaButtonO'))
                bombButtonNames.add(bs.getSpecialChar('ouyaButtonA'))
                pickUpButtonNames.add(bs.getSpecialChar('ouyaButtonY'))
            # otherwise on android show standard buttons
            elif bs.getEnvironment()['platform'] == 'android':
                if bs.getEnvironment()['subplatform'] == 'oculus':
                    punchButtonNames.add(bs.getSpecialChar('diceButton3'))
                    jumpButtonNames.add(bs.getSpecialChar('diceButton1'))
                    bombButtonNames.add(bs.getSpecialChar('diceButton2'))
                    pickUpButtonNames.add(bs.getSpecialChar('diceButton4'))
                else:
                    punchButtonNames.add('X')
                    jumpButtonNames.add('A')
                    bombButtonNames.add('B')
                    pickUpButtonNames.add('Y')
            
        runText = bs.Lstr(value='${R}: ${B}', subs=[
            ('${R}', bs.Lstr(resource='runText')),
            ('${B}', bs.Lstr(resource='holdAnyKeyText' if allKeyboards
                             else 'holdAnyButtonText'))])
        
        # if we're all keyboards, lets show move keys too
        if allKeyboards \
           and len(upButtonNames) == 1 \
           and len(downButtonNames) == 1 \
           and len(leftButtonNames) == 1 \
           and len(rightButtonNames) == 1:
            upText = list(upButtonNames)[0]
            downText = list(downButtonNames)[0]
            leftText = list(leftButtonNames)[0]
            rightText = list(rightButtonNames)[0]
            runText = bs.Lstr(
                value='${M}: ${U}, ${L}, ${D}, ${R}\n${RUN}', subs=[
                    ('${M}', bs.Lstr(resource='moveText')), ('${U}', upText),
                    ('${L}', leftText), ('${D}', downText),
                    ('${R}', rightText), ('${RUN}', runText)])
            
        self._runText.text = runText
        if onlyRemote and self._lifespan is None:
            wText = bs.Lstr(resource='fireTVRemoteWarningText',
                            subs=[('${REMOTE_APP_NAME}', _getRemoteAppName())])
        else:
            wText = ''
        self._extraText.text = wText
        if len(punchButtonNames) == 1:
            self._punchText.text = list(punchButtonNames)[0]
        else: self._punchText.text = ''

        if len(jumpButtonNames) == 1: t = list(jumpButtonNames)[0]
        else: t = ''
        self._jumpText.text = t
        if t == '':
            self._runText.position = self._runTextPosTop
            self._extraText.position = (self._runTextPosTop[0],
                                        self._runTextPosTop[1]-50)
        else:
            self._runText.position = self._runTextPosBottom
            self._extraText.position = (self._runTextPosBottom[0],
                                        self._runTextPosBottom[1]-50)
        if len(bombButtonNames) == 1:
            self._bombText.text = list(bombButtonNames)[0]
        else: self._bombText.text = ''

        # also move our title up/down depending on if this is shown.
        if len(pickUpButtonNames) == 1:
            self._pickUpText.text = list(pickUpButtonNames)[0]
            if self._titleText is not None:
                self._titleText.position = self._titleTextPosTop
        else:
            self._pickUpText.text = ''
            if self._titleText is not None:
                self._titleText.position = self._titleTextPosBottom

    def _die(self):
        for node in self._nodes: node.delete()
        self._nodes = []
        self._updateTimer = None
        self._dead = True

    def exists(self):
        return not self._dead
    
    def handleMessage(self, m):
        self._handleMessageSanityCheck()
        if isinstance(m, bs.DieMessage):
            if m.immediate:
                self._die()
            else:
                # if they dont need immediate, fade out our nodes and die later
                for node in self._nodes:
                    bs.animate(node, 'opacity', {0:node.opacity, 3000:0.0})
                bs.gameTimer(3100, bs.WeakCall(self._die))
                
        else: bsGame.Actor.handleMessage(self, m)

class Background(bsGame.Actor):
    'Simple Fading Background Actor'

    def __init__(self, fadeTime=500, startFaded=False, showLogo=False):
        bs.Actor.__init__(self)
        self._dying = False
        self.fadeTime=fadeTime
        # we're special in that we create our node in the session
        # scene-graph instead of the activity scene-graph.
        # this way we can overlap multiple activities for fades
        # and whatnot..
        session = bs.getSession()
        self._session = weakref.ref(session)
        with bs.Context(session):
            self.node = bs.newNode('image', delegate=self, attrs={
                'fillScreen':True,
                'texture':bs.getTexture('bg'),
                'tiltTranslate':-0.3,
                'hasAlphaChannel':False,
                'color':(1, 1, 1)})
            if not startFaded:
                animate(self.node, 'opacity',
                        {0:0, self.fadeTime:1}, loop=False)
            if showLogo:
                logoTexture = bs.getTexture('logo')
                logoModel = bs.getModel('logo')
                logoModelTransparent = bs.getModel('logoTransparent')
                self.logo = bs.newNode('image', owner=self.node, attrs={
                    'texture':logoTexture,
                    'modelOpaque':logoModel,
                    'modelTransparent':logoModelTransparent,
                    'scale':(0.7, 0.7),
                    'vrDepth':-250,
                    'color':(0.15, 0.15, 0.15),
                    'position':(0, 0),
                    'tiltTranslate':-0.05,
                    'absoluteScale':False})
                self.node.connectAttr('opacity', self.logo, 'opacity')
                # add jitter/pulse for a stop-motion-y look unless we're in VR
                # in which case stillness is better
                if not bs.getEnvironment()['vrMode']:
                    self.c = bs.newNode('combine', owner=self.node,
                                        attrs={'size':2})
                    for attr in ['input0', 'input1']:
                        animate(self.c, attr, {0:0.693, 50:0.7, 500:0.693},
                                loop=True)
                    self.c.connectAttr('output', self.logo, 'scale')
                    c = bs.newNode('combine', owner=self.node, attrs={'size':2})
                    c.connectAttr('output', self.logo, 'position')
                    # gen some random keys for that stop-motion-y look
                    keys = {}
                    time = 0
                    for i in range(10):
                        keys[time] = (random.random()-0.5)*0.0015
                        time += random.random() * 100
                    animate(c, "input0", keys, loop=True)
                    keys = {}
                    time = 0
                    for i in range(10):
                        keys[time] = (random.random()-0.5)*0.0015 + 0.05
                        time += random.random() * 100
                    animate(c, "input1", keys, loop=True)

    def __del__(self):
        # normal actors don't get sent DieMessages when their
        # activity is shutting down, but we still need to do so
        # since our node lives in the session and it wouldn't die
        # otherwise
        self._die()
        bs.Actor.__del__(self)
        
    def _die(self, immediate=False):
        session = self._session()
        if session is None and self.node.exists():
            # if session is gone, our node should be too,
            # since it was part of the session's scene-graph..
            # let's make sure that's the case..
            # (since otherwise we have no way to kill it)
            bs.printError("got None session on Background _die"
                          " (and node still exists!)")
        elif session is not None:
            with bs.Context(session):
                if not self._dying and self.node.exists():
                    self._dying = True
                    if immediate:
                        self.node.delete()
                    else:
                        animate(self.node, "opacity",
                                {0:1, self.fadeTime:0}, loop=False)
                        bs.gameTimer(self.fadeTime+100, self.node.delete)
        
    def handleMessage(self, m):
        self._handleMessageSanityCheck()
        if isinstance(m, bs.DieMessage):
            self._die(m.immediate)
        else: bs.Actor.handleMessage(self, m)


class Text(bsGame.Actor):
    """ Text with some tricks """

    def __init__(self, text, position=(0, 0), hAlign='left', vAlign='none',
                 color=(1, 1, 1, 1), transition=None, transitionDelay=0,
                 flash=False, vAttach='center', hAttach='center', scale=1.0,
                 transitionOutDelay=None, maxWidth=None, shadow=0.5,
                 flatness=0.0, vrDepth=0.0, hostOnly=False, front=False):
        bs.Actor.__init__(self)
        self.node = bs.newNode('text', delegate=self, attrs={
            'text':text,
            'color':color,
            'position':position,
            'hAlign':hAlign,
            'vrDepth':vrDepth,
            'vAlign':vAlign,
            'hAttach':hAttach,
            'vAttach':vAttach,
            'shadow':shadow,
            'flatness':flatness,
            'maxWidth':0.0 if maxWidth is None else maxWidth,
            'hostOnly':hostOnly,
            'front':front,
            'scale':scale})

        if transition == 'fadeIn':
            if flash:
                raise Exception("fixme: flash and fade-in"
                                " currently cant both be on")
            c = bs.newNode('combine', owner=self.node, attrs={
                'input0':color[0], 'input1':color[1],
                'input2':color[2], 'size':4})
            keys = {transitionDelay:0, transitionDelay+500:color[3]}
            if transitionOutDelay is not None:
                keys[transitionDelay+transitionOutDelay] = color[3]
                keys[transitionDelay+transitionOutDelay+500] = 0
            animate(c, "input3", keys)
            c.connectAttr('output', self.node, 'color')

        if flash:
            mult = 2.0
            t1 = 150
            t2 = 300
            c = bs.newNode('combine', owner=self.node, attrs={'size':4})
            animate(c, "input0", {0:color[0]*mult, t1:color[0],
                                  t2:color[0]*mult}, loop=True)
            animate(c, "input1", {0:color[1]*mult, t1:color[1],
                                  t2:color[1]*mult}, loop=True)
            animate(c, "input2", {0:color[2]*mult, t1:color[2],
                                  t2:color[2]*mult}, loop=True)
            #c.input2 = color[2]
            c.input3 = color[3]
            c.connectAttr('output', self.node, 'color')

        c = self.positionCombine = bs.newNode('combine', owner=self.node,
                                              attrs={'size':2})
        if transition == 'inRight':
            keys = {transitionDelay:position[0]+1300,
                    transitionDelay+200:position[0]}
            oKeys = {transitionDelay:0.0,
                     transitionDelay+50:1.0}
            animate(c, 'input0', keys)
            c.input1 = position[1]
            animate(self.node, 'opacity', oKeys)
        elif transition == 'inLeft':
            keys = {transitionDelay:position[0]-1300,
                    transitionDelay+200:position[0]}
            oKeys = {transitionDelay:0.0, transitionDelay+50:1.0}
            if transitionOutDelay is not None:
                keys[transitionDelay+transitionOutDelay] = position[0]
                keys[transitionDelay+transitionOutDelay+200] = position[0]-1300
                oKeys[transitionDelay+transitionOutDelay+150] = 1.0
                oKeys[transitionDelay+transitionOutDelay+200] = 0.0
            animate(c, 'input0', keys)
            c.input1 = position[1]
            animate(self.node, 'opacity', oKeys)
        elif transition == 'inBottomSlow':
            keys = {transitionDelay:-100, transitionDelay+1000:position[1]}
            oKeys = {transitionDelay:0.0, transitionDelay+200:1.0}
            c.input0 = position[0]
            animate(c, 'input1', keys)
            animate(self.node, 'opacity', oKeys)
        elif transition == 'inBottom':
            keys = {transitionDelay:-100, transitionDelay+200:position[1]}
            oKeys = {transitionDelay:0.0, transitionDelay+50:1.0}
            if transitionOutDelay is not None:
                keys[transitionDelay+transitionOutDelay] = position[1]
                keys[transitionDelay+transitionOutDelay+200] = -100
                oKeys[transitionDelay+transitionOutDelay+150] = 1.0
                oKeys[transitionDelay+transitionOutDelay+200] = 0.0
            c.input0 = position[0]
            animate(c, 'input1', keys)
            animate(self.node, 'opacity', oKeys)
        elif transition == 'inTopSlow':
            keys = {transitionDelay:400, transitionDelay+3500:position[1]}
            oKeys = {transitionDelay:0.0, transitionDelay+1000:1.0}
            c.input0 = position[0]
            animate(c, 'input1', keys)
            animate(self.node, 'opacity', oKeys)
        else:
            c.input0 = position[0]
            c.input1 = position[1]
        c.connectAttr('output', self.node, 'position')

        # if we're transitioning out, die at the end of it
        if transitionOutDelay is not None:
            bs.gameTimer(transitionDelay+transitionOutDelay+1000,
                         bs.WeakCall(self.handleMessage, bs.DieMessage()))

    def handleMessage(self, m):
        self._handleMessageSanityCheck()
        if isinstance(m, bs.DieMessage):
            self.node.delete()
        else:
            bs.Actor.handleMessage(self, m)

class Image(bsGame.Actor):
    """ just an image node with a few tricks """
    def __init__(self, texture, position=(0, 0), transition=None,
                 transitionDelay=0, attach='center',
                 color=(1, 1, 1, 1), scale=(100, 100), transitionOutDelay=None,
                 modelOpaque=None, modelTransparent=None,
                 vrDepth=0, hostOnly=False, front=False):
        bs.Actor.__init__(self)
        # if they provided a dict as texture, assume its an icon..
        # otherwise its just a texture value itself
        if type(texture) == dict:
            tintColor = texture['tintColor']
            tint2Color = texture['tint2Color']
            tintTexture = texture['tintTexture']
            texture = texture['texture']
            maskTexture = bs.getTexture('characterIconMask')
        else:
            tintColor = (1, 1, 1)
            tint2Color = None
            tintTexture = None
            maskTexture = None
        

        self.node = bs.newNode('image',
                               attrs={'texture':texture,
                                      'tintColor':tintColor,
                                      'tintTexture':tintTexture,
                                      'position':position,
                                      'vrDepth':vrDepth,
                                      'scale':scale,
                                      'maskTexture':maskTexture,
                                      'color':color,
                                      'absoluteScale':True,
                                      'hostOnly':hostOnly,
                                      'front':front,
                                      'attach':attach},
                               delegate=self)

        if modelOpaque is not None: self.node.modelOpaque = modelOpaque
        if modelTransparent is not None:
            self.node.modelTransparent = modelTransparent
        if tint2Color is not None: self.node.tint2Color = tint2Color

        if transition == 'fadeIn':
            keys = {transitionDelay:0, transitionDelay+500:color[3]}
            if transitionOutDelay is not None:
                keys[transitionDelay+transitionOutDelay] = color[3]
                keys[transitionDelay+transitionOutDelay+500] = 0
            animate(self.node, 'opacity', keys)

        c = self.positionCombine = bs.newNode('combine',
                                              owner=self.node,
                                              attrs={'size':2})
        if transition == 'inRight':
            keys = {transitionDelay:position[0]+1200,
                    transitionDelay+200:position[0]}
            oKeys = {transitionDelay:0.0, transitionDelay+50:1.0}
            animate(c, 'input0', keys)
            c.input1 = position[1]
            animate(self.node, 'opacity', oKeys)
        elif transition == 'inLeft':
            keys = {transitionDelay:position[0]-1200,
                    transitionDelay+200:position[0]}
            oKeys = {transitionDelay:0.0, transitionDelay+50:1.0}
            if transitionOutDelay is not None:
                keys[transitionDelay+transitionOutDelay] = position[0]
                keys[transitionDelay+transitionOutDelay+200] = -position[0]-1200
                oKeys[transitionDelay+transitionOutDelay+150] = 1.0
                oKeys[transitionDelay+transitionOutDelay+200] = 0.0
            animate(c, 'input0', keys)
            c.input1 = position[1]
            animate(self.node, 'opacity', oKeys)
        elif transition == 'inBottomSlow':
            keys = {transitionDelay:-400, transitionDelay+3500:position[1]}
            oKeys = {transitionDelay:0.0, transitionDelay+2000:1.0}
            c.input0 = position[0]
            animate(c, 'input1', keys)
            animate(self.node, 'opacity', oKeys)
        elif transition == 'inBottom':
            keys = {transitionDelay:-400, transitionDelay+200:position[1]}
            oKeys = {transitionDelay:0.0, transitionDelay+50:1.0}
            if transitionOutDelay is not None:
                keys[transitionDelay+transitionOutDelay] = position[1]
                keys[transitionDelay+transitionOutDelay+200] = -400
                oKeys[transitionDelay+transitionOutDelay+150] = 1.0
                oKeys[transitionDelay+transitionOutDelay+200] = 0.0
            c.input0 = position[0]
            animate(c, 'input1', keys)
            animate(self.node, 'opacity', oKeys)
        elif transition == 'inTopSlow':
            keys = {transitionDelay:400, transitionDelay+3500:position[1]}
            oKeys = {transitionDelay:0.0, transitionDelay+1000:1.0}
            c.input0 = position[0]
            animate(c, 'input1', keys)
            animate(self.node, 'opacity', oKeys)
        else:
            c.input0 = position[0]
            c.input1 = position[1]
        c.connectAttr('output', self.node, 'position')

        # if we're transitioning out, die at the end of it
        if transitionOutDelay is not None:
            bs.gameTimer(transitionDelay+transitionOutDelay+1000,
                         bs.WeakCall(self.handleMessage, bs.DieMessage()))

    def handleMessage(self, m):
        self._handleMessageSanityCheck()
        if isinstance(m, bs.DieMessage):
            self.node.delete()
        else:
            bs.Actor.handleMessage(self, m)


class PopupText(bsGame.Actor):
    """
    category: Game Flow Classes

    A bit of text that pops up above a position to denote something special.
    """
    def __init__(self, text, position=(0, 0, 0), color=(1, 1, 1, 1),
                 randomOffset=0.5, offset=(0, 0, 0), scale=1.0):
        """
        Instantiate with given values.

        randomOffset is the amount of random offset from the provided position
        that will be applied. This can help multiple achievements from
        overlapping too much.
        """
        bs.Actor.__init__(self)

        if len(color) == 3: color = (color[0], color[1], color[2], 1.0)
        
        pos = (position[0]+offset[0]+randomOffset*(0.5-random.random()),
               position[1]+offset[0]+randomOffset*(0.5-random.random()),
               position[2]+offset[0]+randomOffset*(0.5-random.random()))

        self.node = bs.newNode('text',
                               attrs={'text':text,
                                      'inWorld':True,
                                      'shadow':1.0,
                                      'flatness':1.0,
                                      'hAlign':'center'},
                               delegate=self)

        lifespan = 1500.0

        # scale up
        animate(self.node, 'scale', {0:0.0,
                                   lifespan*0.11:0.020*0.7*scale,
                                   lifespan*0.16:0.013*0.7*scale,
                                   lifespan*0.25:0.014*0.7*scale})

        # translate upward
        self._tcombine = bs.newNode('combine', owner=self.node, attrs={
            'input0':pos[0], 'input2':pos[2], 'size':3})
        animate(self._tcombine, 'input1', {0:pos[1]+1.5, lifespan:pos[1]+2.0})
        self._tcombine.connectAttr('output', self.node, 'position')

        # fade our opacity in/out
        self._combine = bs.newNode('combine', owner=self.node, attrs={
            'input0':color[0], 'input1':color[1], 'input2':color[2], 'size':4})
        for i in range(4):
            animate(self._combine, 'input'+str(i), {0.13*lifespan:color[i],
                                                    0.18*lifespan:4.0*color[i],
                                                    0.22*lifespan:color[i]})
        animate(self._combine, 'input3', {0:0, 0.1*lifespan:color[3],
                                        0.7*lifespan:color[3], lifespan:0})
        self._combine.connectAttr('output', self.node, 'color')

        # kill ourself 
        self._dieTimer = bs.Timer(int(lifespan),
                                  bs.WeakCall(self.handleMessage,
                                              bs.DieMessage()))

    def handleMessage(self, msg):
        self._handleMessageSanityCheck()
        if isinstance(msg, bs.DieMessage): self.node.delete()
        else: bs.Actor.handleMessage(self, msg)
            

class TipsText(bsGame.Actor):
    """ a bit of text that shows various messages; good for
    helpful-tips kinda things """
    def __init__(self, offsY=100):
        bs.Actor.__init__(self)
        self._tipScale = 0.8
        self._tipTitleScale = 1.1
        self._offsY = offsY
        self.node = bs.newNode('text', delegate=self, attrs={
            'text':'',
            'scale':self._tipScale,
            'hAlign':'left',
            'maxWidth':800,
            'vrDepth':-20,
            'vAlign':'center',
            'vAttach':'bottom'})
        self.titleNode = bs.newNode('text', delegate=self, attrs={
            'text':bs.Lstr(value='${A}:',
                           subs=[('${A}', bs.Lstr(resource='tipText'))]),
            'scale':self._tipTitleScale,
            'maxWidth':122,
            'hAlign':'right',
            'vrDepth':-20,
            'vAlign':'center',
            'vAttach':'bottom'})
        self._messageDuration = 10000
        self._messageSpacing = 3000
        self._changeTimer = bs.Timer(self._messageDuration+self._messageSpacing,
                                     bs.WeakCall(self.changePhrase),
                                     repeat=True)
        self._combine = bs.newNode("combine", owner=self.node, attrs={
            'input0':1.0, 'input1':0.8, 'input2':1.0, 'size':4})
        self._combine.connectAttr('output', self.node, 'color')
        self._combine.connectAttr('output', self.titleNode, 'color')
        self.changePhrase()

    def changePhrase(self):
        nextTip = bs.Lstr(translate=('tips', _getNextTip()),
                          subs=[('${REMOTE_APP_NAME}', _getRemoteAppName())])
        s = self._messageSpacing
        self.node.position = (-200, self._offsY)
        self.titleNode.position = (-220, self._offsY+3)
        keys = {s:0, s+1000:1.0, s+self._messageDuration-1000:1.0,
                s+self._messageDuration:0.0}
        animate(self._combine, "input3",
                dict([[k, v*0.5] for k, v in keys.items()]))
        self.node.text = nextTip

    def handleMessage(self, m):
        self._handleMessageSanityCheck()
        if isinstance(m, bs.DieMessage):
            self.node.delete()
            self.titleNode.delete()
        else: bs.Actor.handleMessage(self, m)

class OnScreenCountdown(bsGame.Actor):
    """
    category: Game Flow Classes

    A Handy On-Screen Timer;
    useful for time-based games that count down to zero.
    """
    def __init__(self, duration, endCall=None):
        'Duration is provided in seconds'
        bs.Actor.__init__(self)
        self._timeRemaining = duration
        self._ended = False
        self._endCall = endCall
        self.node = bs.newNode('text', attrs={
            'vAttach':'top',
            'hAttach':'center',
            'hAlign':'center',
            'color':(1, 1, 0.5, 1),
            'flatness':0.5,
            'shadow':0.5,
            'position':(0, -70),
            'scale':1.4,
            'text':''})
        self.inputNode = bs.newNode('timeDisplay', attrs={
            'time2':duration*1000,
            'timeMax':duration*1000,
            'timeMin':0})
        self.inputNode.connectAttr('output', self.node, 'text')
        self._countDownSounds = {10:bs.getSound('announceTen'),
                                 9:bs.getSound('announceNine'),
                                 8:bs.getSound('announceEight'),
                                 7:bs.getSound('announceSeven'),
                                 6:bs.getSound('announceSix'),
                                 5:bs.getSound('announceFive'),
                                 4:bs.getSound('announceFour'),
                                 3:bs.getSound('announceThree'),
                                 2:bs.getSound('announceTwo'),
                                 1:bs.getSound('announceOne')}
        
    def start(self):
        'Starts the timer.'
        g = bs.getSharedObject('globals')
        g.connectAttr('gameTime', self.inputNode, 'time1')
        self.inputNode.time2 = g.gameTime + (self._timeRemaining+1) * 1000
        self._timer = bs.Timer(1000, self._update, repeat=True, timeType='game')

    def onFinalize(self):
        bs.Actor.onFinalize(self)
        # release callbacks/refs
        self._endCall = None
        
    def _update(self, forceValue=None):
        if forceValue is not None: t = forceValue
        else:
            self._timeRemaining = max(0, self._timeRemaining - 1)
            t = self._timeRemaining

        # if there's a countdown sound for this time that we
        # havn't played yet, play it
        if t == 10:
            self.node.scale *= 1.2
            c = bs.newNode('combine', owner=self.node, attrs={'size':4})
            c.connectAttr('output', self.node, 'color')
            animate(c, "input0", {0:1, 150:1}, loop=True)
            animate(c, "input1", {0:1, 150:0.5}, loop=True)
            animate(c, "input2", {0:0.1, 150:0.0}, loop=True)
            c.input3 = 1.0
        if t <= 10 and not self._ended:
            bs.playSound(bs.getSound('tick'))
        
        if t in self._countDownSounds:
            bs.playSound(self._countDownSounds[t])
            
        if t <= 0 and not self._ended:
            self._ended = True
            if self._endCall is not None: self._endCall()

class OnScreenTimer(bsGame.Actor):
    """
    category: Game Flow Classes

    A Handy On-Screen Timer.
    Useful for time-based games where time increases.
    """
    def __init__(self):
        bs.Actor.__init__(self)
        self._startTime = None
        self.node = bs.newNode('text', attrs={
            'vAttach':'top',
            'hAttach':'center',
            'hAlign':'center',
            'color':(1, 1, 0.5, 1),
            'flatness':0.5,
            'shadow':0.5,
            'position':(0, -70),
            'scale':1.4,
            'text':''})
        self.inputNode = bs.newNode('timeDisplay', attrs={
            'timeMin':0,
            'showSubSeconds':True})
        self.inputNode.connectAttr('output', self.node, 'text')
        
    def start(self):
        'Starts the timer.'
        self._startTime = bs.getGameTime()
        self.inputNode.time1 = self._startTime
        bs.getSharedObject('globals').connectAttr('gameTime',
                                                  self.inputNode, 'time2')
        
    def hasStarted(self):
        'Returns whether this timer has started yet.'
        return False if self._startTime is None else True
    
    def stop(self, endTime=None):
        """Ends the timer. If 'endTime' is not None, it is used when calculating
        the final display time; otherwise the current time is used"""
        if endTime is None: endTime = bs.getGameTime()
        self._timer = None
        if self._startTime is None:
            print 'Warning: OnScreenTimer.stop() called without start() first'
        else:
            self.inputNode.timeMax = endTime-self._startTime
        
    def getStartTime(self):
        'Returns the game-time when start() was called'
        if self._startTime is None:
            print 'WARNING: getStartTime() called on un-started timer'
            return bs.getGameTime()
        return self._startTime
    
    def handleMessage(self, msg):
        # if we're asked to die, just kill our node/timer
        if isinstance(msg, bs.DieMessage):
            self._timer = None
            self.node.delete()
            
class ZoomText(bsGame.Actor):
    """
    category: Game Flow Classes

    Big Zooming Text Actor.
    Used for things such as the 'BOB WINS' victory messages.
    """

    def __init__(self, text, position=(0, 0), shiftPosition=None,
                 shiftDelay=None, lifespan=None, flash=True, trail=True,
                 hAlign="center", color=(0.9, 0.4, 0.0), jitter=0.0,
                 trailColor=(1.0, 0.35, 0.1, 0.0), scale=1.0, projectScale=1.0,
                 tiltTranslate=0.0, maxWidth=None):
        bs.Actor.__init__(self)
        self._dying = False
        positionAdjusted = (position[0], position[1]-100)
        if shiftDelay is None: shiftDelay = 2500
        if shiftDelay < 0:
            bs.printError('got shiftDelay < 0')
            shiftDelay = 0
        self._projectScale = projectScale
        self.node = bs.newNode('text', delegate=self, attrs={
            'position':positionAdjusted,
            'big':True,
            'text':text,
            'trail':trail,
            'vrDepth':0,
            'shadow':0.0 if trail else 0.3,
            'scale':scale,
            'maxWidth':maxWidth if maxWidth is not None else 0.0,
            'tiltTranslate':tiltTranslate,
            'hAlign':hAlign,
            'vAlign':'center'})

        # we never jitter in vr mode..
        if bs.getEnvironment()['vrMode']:
            jitter = 0.0
            
        # if they want jitter, animate its position slightly...
        if jitter > 0.0:
            self._jitter(positionAdjusted, jitter*scale)

        # if they want shifting, move to the shift position and
        # then resume jittering
        if shiftPosition is not None:
            positionAdjusted2 = (shiftPosition[0], shiftPosition[1]-100)
            bs.gameTimer(shiftDelay, bs.WeakCall(self._shift, positionAdjusted,
                                                 positionAdjusted2))
            if jitter > 0.0:
                bs.gameTimer(shiftDelay+250, bs.WeakCall(self._jitter,
                                                         positionAdjusted2,
                                                         jitter*scale))
        colorCombine = bs.newNode('combine', owner=self.node, attrs={
            'input2':color[2],
            'input3':1.0,
            'size':4})
        if trail:
            trailColor = bs.newNode('combine', owner=self.node, attrs={
                'size':3,
                'input0':trailColor[0],
                'input1':trailColor[1],
                'input2':trailColor[2]})
            trailColor.connectAttr('output', self.node, 'trailColor')
            foo = 0.85
            animate(self.node, 'trailProjectScale', {
                0:0*projectScale, int(foo*201):0.6*projectScale,
                int(foo*347):0.8*projectScale, int(foo*478):0.9*projectScale,
                int(foo*595):0.93*projectScale, int(foo*748):0.95*projectScale,
                int(foo*941):0.95*projectScale})
        if flash:
            mult = 2.0
            t1 = 150
            t2 = 300
            animate(colorCombine, 'input0', {0:color[0]*mult, t1:color[0],
                                             t2:color[0]*mult}, loop=True)
            animate(colorCombine, 'input1', {0:color[1]*mult, t1:color[1],
                                             t2:color[1]*mult}, loop=True)
            animate(colorCombine, 'input2', {0:color[2]*mult, t1:color[2],
                                             t2:color[2]*mult}, loop=True)
        else:
            colorCombine.input0 = color[0]
            colorCombine.input1 = color[1]
        colorCombine.connectAttr('output', self.node, 'color')
        animate(self.node, 'projectScale',
                {0:0, 270:1.05*projectScale, 300:1*projectScale})

        # if they give us a lifespan, kill ourself down the line
        if lifespan is not None:
            bs.gameTimer(lifespan, bs.WeakCall(self.handleMessage,
                                               bs.DieMessage()))

    def handleMessage(self, m):
        self._handleMessageSanityCheck()
        if isinstance(m, bs.DieMessage):
            if not self._dying and self.node.exists():
                self._dying = True
                if m.immediate:
                    self.node.delete()
                else:
                    animate(self.node, 'projectScale',
                            {0:1*self._projectScale,
                             600:1.2*self._projectScale})
                    animate(self.node, 'opacity', {0:1, 300:0})
                    animate(self.node, 'trailOpacity', {0:1, 600:0})
                    bs.gameTimer(700, self.node.delete)
        else:
            bs.Actor.handleMessage(self, m)

    def _jitter(self, position, jitterAmount):
        if not self.node.exists(): return
        c = bs.newNode('combine', owner=self.node, attrs={'size':2})
        for index, attr in enumerate(['input0', 'input1']):
            keys = {}
            time = 0
            # gen some random keys for that stop-motion-y look
            for i in range(10):
                keys[time] = (position[index]
                              + (random.random()-0.5)*jitterAmount*1.6)
                time += random.random() * 100
            animate(c, attr, keys, loop=True)
        c.connectAttr('output', self.node, 'position')

    def _shift(self, position1, position2):
        if not self.node.exists(): return
        c = bs.newNode('combine', owner=self.node, attrs={'size':2})
        animate(c, 'input0', {0:position1[0], 250:position2[0]})
        animate(c, 'input1', {0:position1[1], 250:position2[1]})
        c.connectAttr('output', self.node, 'position')

_gAdAmt = None
_gLastAdPurpose = 'invalid'

# this gets updated on successful ad views..
_lastAdCompletionTime = None
_lastAdShort = False
_attemptedFirstAd = False

def _showAd(purpose, onCompletionCall=None, passActuallyShowed=False):
    global _gLastAdPurpose
    _gLastAdPurpose = purpose
    bsInternal._showAd(purpose, onCompletionCall, passActuallyShowed)
    
def _callAfterAd(c):
    
    show = True
    # no ads without net-connections, etc..
    if not bsInternal._canShowAd(): show = False
    if _havePro(): show = False # pro disables interstitials
    
    try:
        isTournament = (bsInternal._getForegroundHostSession()._tournamentID
                        is not None)
    except Exception:
        isTournament = False
    if isTournament: show = False # never show ads during tournaments
    
    if show:
        try: launchCount = bs.getConfig()['launchCount']
        except Exception: launchCount = 0
        global _gAdAmt
        global _attemptedFirstAd
        # if we're seeing short ads we may want to space them differently..
        intervalMult = bsInternal._getAccountMiscReadVal(
            'ads.shortIntervalMult', 1.0) if _lastAdShort else 1.0
        if _gAdAmt is None:
            if launchCount <= 1:
                _gAdAmt = bsInternal._getAccountMiscReadVal(
                    'ads.startVal1', 0.99)
            else:
                _gAdAmt = bsInternal._getAccountMiscReadVal(
                    'ads.startVal2', 1.0)
            interval = None
        else:
            # so far we're cleared to show; now calc our ad-show-threshold and
            # see if we should *actually* show ( we reach our threshold faster
            # the longer we've been playing..)
            base = 'ads' if bsInternal._hasVideoAds() else 'ads2'
            minLC = bsInternal._getAccountMiscReadVal(base+'.minLC', 0.0)
            maxLC = bsInternal._getAccountMiscReadVal(base+'.maxLC', 5.0)
            minLCScale = \
                bsInternal._getAccountMiscReadVal(base+'.minLCScale', 0.25)
            maxLCScale = \
                bsInternal._getAccountMiscReadVal(base+'.maxLCScale', 0.34)
            minLCInterval = \
                bsInternal._getAccountMiscReadVal(base+'.minLCInterval', 360)
            maxLCInterval = \
                bsInternal._getAccountMiscReadVal(base+'.maxLCInterval', 300)
            if launchCount < minLC: lcAmt = 0.0
            elif launchCount > maxLC: lcAmt = 1.0
            else: lcAmt = (float(launchCount)-minLC)/(maxLC-minLC)
            incr = (1.0-lcAmt)*minLCScale+lcAmt*maxLCScale
            interval = (1.0-lcAmt)*minLCInterval+lcAmt*maxLCInterval
            _gAdAmt += incr
        if _gAdAmt >= 1.0:
            _gAdAmt = _gAdAmt % 1.0
            _attemptedFirstAd = True
        # after we've reached the traditional show-threshold once,
        # try again whenver its been INTERVAL since our last successful show
        elif _attemptedFirstAd and (_lastAdCompletionTime is None or (
                interval is not None and bs.getRealTime() - \
                _lastAdCompletionTime > (interval * 1000 * intervalMult))):
            # reset our other counter too in this case..
            _gAdAmt = 0.0
        else:
            show = False
        _firstAdAttempt = False

    # if we're *still* cleared to show, actually tell the system to show..
    if show:
        # as a safety-check, set up an object that will run
        # the completion callback if we've returned and sat for 10 seconds
        # (in case some random ad network doesn't properly deliver its
        # completion callback)
        class _Payload(object):
            def __init__(self, call):
                self._call = call
                self._ran = False
            def run(self, fallback=False):
                if not self._ran:
                    if fallback:
                        print ('ERROR: relying on fallback ad-callback! '
                               'last network: '+_gLastAdNetwork+' (set '
                               +str(int(time.time()-_gLastAdNetworkSetTime))
                               +'s ago); purpose='+_gLastAdPurpose)
                    bs.pushCall(self._call)
                    self._ran = True
        p = _Payload(c)
        with bs.Context('UI'):
            bs.realTimer(5000, lambda: p.run(fallback=True))
        _showAd('between_game', onCompletionCall=p.run)
    else: bs.pushCall(c) # just run the callback without the ad

_gLastAdNetwork = 'unknown'
_gLastAdNetworkSetTime = time.time()

def _havePro():
    # check our tickets-based pro upgrade and our two real-IAP based upgrades
    return (bsInternal._getPurchased('upgrades.pro')
            or bsInternal._getPurchased('static.pro')
            or bsInternal._getPurchased('static.pro_sale'))

def _haveProOptions():
    # we expose pro options if the server tells us to
    # (which is generally just when we own pro),
    # or also if we've been grandfathered in.
    return True if (
        bsInternal._getAccountMiscReadVal2('proOptionsUnlocked', False)
        or bs.getConfig().get('lc14292', 0) > 1) else False
    
_gLastPostPurchaseMessageTime = None
def _showPostPurchaseMessage():
    global _gLastPostPurchaseMessageTime
    curTime = bs.getRealTime()
    if (_gLastPostPurchaseMessageTime is None
            or curTime-_gLastPostPurchaseMessageTime > 3000):
        _gLastPostPurchaseMessageTime = curTime
        with bs.Context('UI'):
            bs.screenMessage(bs.Lstr(resource='updatingAccountText',
                                     fallbackResource='purchasingText'),
                             color=(0, 1, 0))
            bs.playSound(bs.getSound('click01'))
_gSales = []

def _handleSaleInfo(info):
    pass

def _adCompleteGeneral():
    pass

# if we try to run promo-codes due to launch-args/etc we might not be signed;
# in yet; go ahead and queue them up in that case..
_pendingPromoCodes = []

def _onAccountStateChanged():

    # run any pending promo codes we had queued up while not signed in
    global _pendingPromoCodes
    if bsInternal._getAccountState() == 'SIGNED_IN' and _pendingPromoCodes:
        for code in _pendingPromoCodes:
            bs.screenMessage(
                bs.Lstr(resource='submittingPromoCodeText'), color=(0, 1, 0))
            bsInternal._addTransaction({'type':'PROMO_CODE',
                                        'expireTime':time.time()+5,
                                        'code':code})
        bsInternal._runTransactions()
        _pendingPromoCodes = []

def _checkPendingCodes():
    # if we're still not signed in and have pending codes,
    # inform the user that they need to sign in to use them
    if _pendingPromoCodes:
        bs.screenMessage(
            bs.Lstr(resource='signInForPromoCodeText'), color=(1, 0, 0))
        bs.playSound(bs.getSound('error'))
    
def _handleDeepLink(url):
    if url.startswith('bombsquad://code/'):
        code = url.replace('bombsquad://code/', '')
        # if we're not signed in, queue up the code to run the next time we are
        # and issue a warning if we havn't signed in within the next few seconds
        if bsInternal._getAccountState() != 'SIGNED_IN':
            _pendingPromoCodes.append(code)
            bs.realTimer(6000, _checkPendingCodes)
            return
        bs.screenMessage(
            bs.Lstr(resource='submittingPromoCodeText'), color=(0, 1, 0))
        bsInternal._addTransaction({'type':'PROMO_CODE',
                                    'expireTime':time.time()+5,
                                    'code':code})
        bsInternal._runTransactions()
    else:
        bs.screenMessage(bs.Lstr(resource='errorText'), color=(1, 0, 0))
        bs.playSound(bs.getSound('error'))

def uni(s):
    """
    category: General Utility Functions

    Given a string or unicode object, returns a unicode version of it
    """
    if type(s) is not unicode: return s.decode('utf-8', errors='ignore')
    else: return s

def utf8(s):
    """
    category: General Utility Functions

    Given a string or unicode object, returns a string
    (encoding with utf-8 if need be)
    """
    if type(s) is unicode: return s.encode('utf-8', errors='ignore')
    else: return s

def isCustomUnicodeChar(c):
    if type(c) is not unicode or len(c) != 1:
        raise Exception("Invalid Input; not unicode or not length 1")
    return True if ord(c) >= 0xE000 and ord(c) <= 0xF8FF else False

def jsonPrep(data):
    """ converts data to a form that should
    translate into and out of json seamlessly;
    Also fixes bad utf8 to keep json from choking.
    Can be used to test json-based messaging before
    fully switching over to it """
    if isinstance(data, dict):
        return dict((jsonPrep(key), jsonPrep(value)) \
                    for key, value in data.items())
    elif isinstance(data, list):
        return [jsonPrep(element) for element in data]
    elif isinstance(data, tuple):
        return [jsonPrep(element) for element in data]
    elif isinstance(data, str):
        return data.decode('utf-8', errors='ignore')
    else:
        return data

def toUTF8(data):
    """ converts any unicode data to utf8 """
    if isinstance(data, dict):
        return dict((toUTF8(key), toUTF8(value)) \
                    for key, value in data.items())
    elif isinstance(data, list):
        return [toUTF8(element) for element in data]
    elif isinstance(data, tuple):
        return tuple(toUTF8(element) for element in data)
    elif isinstance(data, unicode):
        return data.encode('utf-8', errors='ignore')
    else:
        return data

def _getIPAddressType(addr):
    """ Returns socket.AF_INET6 or socket.AF_INET4.
    May return false positives for ipv6 on windows """
    import socket
    
    socketType = None
    
    # first see if this is a valid ipv4 addr
    try:
        socket.inet_aton(addr)
        socketType = socket.AF_INET
    except Exception as e:
        pass
    
    # hmm apparently not ipv4; lets try ipv6
    if socketType is None:
        try:
            # windows doesn't have inet_pton (at least prior to python 3.4);
            # ..in that case let's just assume its a valid v6 address if it
            # passes a rudimentary check
            if hasattr(socket, 'inet_pton'):
                socket.inet_pton(socket.AF_INET6, addr)
            else:
                # no inet_pton; just do a rudimentary check
                if ':' not in addr:
                    raise Exception('not an ipv6 address')
            socketType = socket.AF_INET6
        except Exception as e:
            pass
        
    if socketType is None:
        raise Exception("addr seems to be neither v4 or v6: "+str(addr))
    
    return socketType

_gServerConfigDirty = False

def _configServer():
    """apply server config changes that can always take effect immediately
    (party name, etc)"""
    config = copy.deepcopy(_gServerConfig)

    # NOTE - soon clients should always be able to view in their own languages
    # so this will become unnecessary.
    # FIXME - subsequent changes to this dont get
    # propogated to the server currently
    _setLanguage(config.get('language', 'English'))
    
    bsInternal._setTelnetAccessEnabled(config.get('enableTelnet', False))
        
    bs.getConfig()['Auto Balance Teams'] = config.get('autoBalanceTeams', True)

    bsInternal._setPublicPartyMaxSize(config.get('maxPartySize', 9))
    bsInternal._setPublicPartyName(config.get('partyName', 'party'))
    bsInternal._setPublicPartyStatsURL(config.get('statsURL', ''));
    # call set-enabled last (will push state)
    bsInternal._setPublicPartyEnabled(config.get('partyIsPublic', True));

    if not _gRunServerFirstRun:
        print 'server config updated.'

    # FIXME - we could avoid setting this as dirty if the only changes have been
    # ones here we can apply immediately.  (could reduce cases where players
    # have to rejoin)
    global _gServerConfigDirty
    _gServerConfigDirty = True
    
_gRunServerFirstRun = True

def _runServer():
    """kick off a host-session based on the current server config"""
    import bsTeamGame
    
    global _gRunServerFirstRun
    global _gServerConfigDirty

    config = copy.deepcopy(_gServerConfig)

    # convert string session type to the class..
    # (hmm should we just keep this as a string?)
    sessionTypeName = config.get('sessionType', 'ffa')
    if sessionTypeName == 'ffa': sessionType = bs.FreeForAllSession
    elif sessionTypeName == 'teams': sessionType = bs.TeamsSession
    else: raise Exception('invalid sessionType value: '+sessionTypeName)

    if bsInternal._getAccountState() != 'SIGNED_IN':
        print ('WARNING: _runServer() expects to run '
               'with a signed in server account')

    if _gRunServerFirstRun:
        env = bs.getEnvironment()
        print ('BombSquad headless ' if bs.getEnvironment()['subplatform']
               == 'headless' else 'BombSquad ') + str(env['version'])+\
               ' ('+str(env['buildNumber'])+') entering server-mode '+\
               time.strftime('%c')

    playlistShuffle = config.get('playlistShuffle', True)
    bs.getConfig()['Show Tutorial'] = False
    bs.getConfig()['Free-for-All Playlist Selection'] = \
        config.get('playlistName', '__default__') if sessionTypeName == 'ffa' \
        else '__default__'
    bs.getConfig()['Free-for-All Playlist Randomize'] = playlistShuffle
    bs.getConfig()['Team Tournament Playlist Selection'] = \
        config.get('playlistName', '__default__') \
        if sessionTypeName == 'teams' else '__default__'
    bs.getConfig()['Team Tournament Playlist Randomize'] = playlistShuffle
    bs.getConfig()['Port'] = config.get('port', 43210)
    
    # set series lengths
    bsTeamGame.gTeamSeriesLength = config.get('teamsSeriesLength', 7)
    bsTeamGame.gFFASeriesLength = config.get('ffaSeriesScoreToWin', 24)

    # and here we go..
    bsInternal._newHostSession(sessionType)

    # also lets fire off an access check if this is our first time
    # through (and they want a public party)...
    if _gRunServerFirstRun:
        def accessCheckResponse(data):
            port = bsInternal._getGamePort()
            if data is None:
                print 'error on UDP port access check (internet down?)'
            else:
                if data['accessible']:
                    print 'UDP port', port, ('access check successful. Your '
                                             'server appears to be joinable '
                                             'from the internet.')
                else:
                    print 'UDP port', port, ('access check failed. Your server '
                                             'does not appear to be joinable '
                                             'from the internet.')
        serverGet('bsAccessCheck', {'port':bsInternal._getGamePort()},
                  callback=accessCheckResponse)
    _gRunServerFirstRun = False
    _gServerConfigDirty = False
_gRunServerWaitTimer = None
_gRunServerPlaylistFetch = None
_gLaunchedServer = False

def configServer(configFile=None):
    """ utility function to run the game in server-mode """

    global _gServerConfig
    global _gLaunchedServer
    
    # read and store the new server config and then delete the file it came from
    if configFile is not None:
        f = open(configFile)
        _gServerConfig = json.loads(f.read())
        f.close()
        os.remove(configFile)
    else:
        _gServerConfig = {}

    # make note if they want us to import a playlist;
    # we'll need to do that first if so
    global _gRunServerPlaylistFetch
    playlist_code = _gServerConfig.get('playlistCode')
    if playlist_code is not None:
        _gRunServerPlaylistFetch = {'sentRequest':False,
                                    'gotResponse':False,
                                    'playlistCode':str(playlist_code)}
    
    # apply config stuff that can take effect immediately (party name, etc)
    _configServer()
    
    # launch the server only the first time through;
    # after that it will be self-sustaining
    if not _gLaunchedServer:
        
        # now sit around until we're signed in and then kick off the server
        global _gRunServerWaitTimer
        with bs.Context('UI'):
            def doIt():
                global _gRunServerWaitTimer
                global _gRunServerPlaylistFetch
                if bsInternal._getAccountState() == 'SIGNED_IN':
                    can_launch = False
                    # if we're trying to fetch a playlist, we do that first
                    if _gRunServerPlaylistFetch is not None:
                        
                        # send request if we havn't
                        if not _gRunServerPlaylistFetch['sentRequest']:
                            
                            def onPlaylistFetchResponse(result):
                                if result is None:
                                    print 'Error fetching playlist; aborting.'
                                    sys.exit(-1)
                                    
                                # once we get here we simply modify our
                                # config to use this playlist
                                typeName = ('teams' if result['playlistType']
                                            == 'Team Tournament' else 'ffa'
                                            if result['playlistType'] ==
                                            'Free-for-All' else '??')
                                print ('Playlist \''+result['playlistName']
                                       +'\' ('+typeName
                                       +') downloaded; running...')
                                _gRunServerPlaylistFetch['gotResponse'] = True
                                _gServerConfig['sessionType'] = typeName
                                _gServerConfig['playlistName'] = \
                                    result['playlistName']
                            print ('Requesting shared-playlist '+str(
                                _gRunServerPlaylistFetch['playlistCode'])+'...')
                            _gRunServerPlaylistFetch['sentRequest'] = True
                            bsInternal._addTransaction(
                                { 'type':'IMPORT_PLAYLIST',
                                  'code':
                                  _gRunServerPlaylistFetch['playlistCode'],
                                  'overwrite':True},
                                callback=onPlaylistFetchResponse)
                            bsInternal._runTransactions()
                        # if we got a valid result, forget the fetch ever
                        # existed and move on..
                        if _gRunServerPlaylistFetch['gotResponse']:
                            _gRunServerPlaylistFetch = None
                            can_launch = True
                    else:
                        can_launch = True
                    if can_launch:
                        _gRunServerWaitTimer = None
                        bs.pushCall(_runServer)
            _gRunServerWaitTimer = bs.Timer(250, doIt,
                                            timeType='real', repeat=True)
        _gLaunchedServer = True
    
