import bs
import bsGame
import bsMap
import time
import os
import math
import bsInternal

def _safeSetAttr(node,attr,value):
    if node.exists(): setattr(node,attr,value)
            
class ButtonPress(object):
    def __init__(self,button,delay=0,release=True,releaseDelay=0):
        self._button = button
        self._delay = delay
        self._release = release
        self._releaseDelay = releaseDelay
    def run(self,a):
        s = a._currentSpaz
        if self._button == 'punch':
            call = s.onPunchPress
            releaseCall = s.onPunchRelease
            img = a._punchImage
            color = a._punchImageColor
        elif self._button == 'jump':
            call = s.onJumpPress
            releaseCall = s.onJumpRelease
            img = a._jumpImage
            color = a._jumpImageColor
        elif self._button == 'bomb':
            call = s.onBombPress
            releaseCall = s.onBombRelease
            img = a._bombImage
            color = a._bombImageColor
        elif self._button == 'pickUp':
            call = s.onPickUpPress
            releaseCall = s.onPickUpRelease
            img = a._pickUpImage
            color = a._pickUpImageColor
        elif self._button == 'run':
            call = bs.Call(s.onRun,1.0)
            releaseCall = bs.Call(s.onRun,0.0)
            img = None
            color = None
        else: raise Exception("invalid button: "+self._button)

        brightness = 4.0
        if color is not None:
            cBright = list(color)
            cBright[0] *= brightness
            cBright[1] *= brightness
            cBright[2] *= brightness
        
        if self._delay == 0:
            call()
            if img is not None:
                img.color = cBright
                img.vrDepth = -40
        else:
            bs.gameTimer(self._delay,call)
            if img is not None:
                bs.gameTimer(self._delay,bs.Call(_safeSetAttr,img,'color',cBright))
                bs.gameTimer(self._delay,bs.Call(_safeSetAttr,img,'vrDepth',-30))
        if self._release:
            if self._delay == 0 and self._releaseDelay == 0:
                releaseCall()
            else:
                bs.gameTimer(self._delay+self._releaseDelay,releaseCall)
            if img is not None:
                bs.gameTimer(self._delay+self._releaseDelay+100,bs.Call(_safeSetAttr,img,'color',color))
                bs.gameTimer(self._delay+self._releaseDelay+100,bs.Call(_safeSetAttr,img,'vrDepth',-20))


class ButtonRelease(object):
    def __init__(self,button,delay=0):
        self._button = button
        self._delay = delay
    def run(self,a):
        s = a._currentSpaz
        if self._button == 'punch':
            call = s.onPunchRelease
            img = a._punchImage
            color = a._punchImageColor
        elif self._button == 'jump':
            call = s.onJumpRelease
            img = a._jumpImage
            color = a._jumpImageColor
        elif self._button == 'bomb':
            call = s.onBombRelease
            img = a._bombImage
            color = a._bombImageColor
        elif self._button == 'pickUp':
            call = s.onPickUpPress
            img = a._pickUpImage
            color = a._pickUpImageColor
        elif self._button == 'run':
            call = bs.Call(s.onRun,0.0)
            img = None
            color = None
        else: raise Exception("invalid button: "+self._button)
        if self._delay == 0: call()
        else: bs.gameTimer(self._delay,call)
        if img is not None:
            bs.gameTimer(self._delay+100,bs.Call(_safeSetAttr,img,'color',color))
            bs.gameTimer(self._delay+100,bs.Call(_safeSetAttr,img,'vrDepth',-20))

class TutorialActivity(bs.Activity):

    def __init__(self,settings={}):
        bs.Activity.__init__(self,settings)

        self._benchmarkType = getattr(bs.getSession(),'benchmarkType',None)
        
        self._lastStartTime = None
        self._cycleTimes = []
        
        self._allowPausing = True
        self._allowKickIdlePlayers = False

        self._issuedWarning = False
        
        self._mapType = bsMap.RampageMap
        self._mapType.preload()

        self._jumpButtonTex = bs.getTexture('buttonJump')
        self._pickUpButtonTex = bs.getTexture('buttonPickUp')
        self._bombButtonTex = bs.getTexture('buttonBomb')
        self._punchButtonTex = bs.getTexture('buttonPunch')
        self._r = 'tutorial'
        # self._R = bsUtils._getResource('tutorial')
        self._haveSkipped = False
        self._stickImagePositionX = self._stickImagePositionY = 0.0

        self._spawnSound = bs.getSound('spawn')
        
    def onTransitionIn(self):
        bs.Activity.onTransitionIn(self)
        bs.playMusic('CharSelect',continuous=True)
        self._map = self._mapType()

    def onBegin(self):
        bs.Activity.onBegin(self)

        bsInternal._setAnalyticsScreen('Tutorial Start')
        bsInternal._incrementAnalyticsCount('Tutorial start')
        
        if 0:
            # buttons on top
            textY = 140
            buttonsY = 250
        else:
            # buttons on bottom
            textY = 260
            buttonsY = 160
        
        # need different versions of this: taps/buttons/keys
        t = self._text = bs.newNode('text',
                                    attrs={'text':'',
                                           'scale':1.9,
                                           'position':(0,textY),
                                           'maxWidth':500,
                                           'flatness':0.0,
                                           'shadow':0.5,
                                           'hAlign':'center',
                                           'vAlign':'center',
                                           'vAttach':'center'})
        #bs.animate(t,'opacity',{1000:0.0,1200:1.0})

        # bs.newNode('text',
        #            attrs={'text':'TUTORIAL IS OUT OF ORDER AT THE MOMENT;\nI\'LL GET IT FIXED SOON..',
        #                   'scale':1.4,
        #                   'position':(0,textY-200),
        #                   'maxWidth':500,
        #                   'flatness':0.0,
        #                   'color':(1,0.3,0),
        #                   'shadow':0.5,
        #                   'hAlign':'center',
        #                   'vAlign':'center',
        #                   'vAttach':'center'})
        

        # need different versions of this: taps/buttons/keys
        # txt = self._R.cpuBenchmarkText if self._benchmarkType == 'cpu' else self._R.toSkipPressAnythingText
        txt = bs.Lstr(resource=self._r+'.cpuBenchmarkText') if self._benchmarkType == 'cpu' else bs.Lstr(resource=self._r+'.toSkipPressAnythingText')
        t = self._skipText = bs.newNode('text',
                                        attrs={'text':txt,
                                               'maxWidth':900,
                                               'scale':1.1,
                                               'vrDepth':100,
                                               'position':(0,30),
                                               'hAlign':'center',
                                               'vAlign':'center',
                                               'vAttach':'bottom'})
        bs.animate(t,'opacity',{1000:0.0,2000:0.7})
        t = self._skipCountText = bs.newNode('text',
                                                 attrs={'text':'',
                                                        'scale':1.4,
                                                        'vrDepth':90,
                                                        'position':(0,70),
                                                        'hAlign':'center',
                                                        'vAlign':'center',
                                                        'vAttach':'bottom'})

        env = bs.getEnvironment()
        ouya = (env['platform'] == 'android' and env['subplatform'] == 'ouya')
        
        self._scale = scale = 0.6
        centerOffs = 130.0*scale
        offs = 65.0*scale
        position=(0,buttonsY)
        imageSize = 90.0*scale
        imageSize2 = 220.0*scale
        nubSize = 110.0*scale
        p = (position[0]+centerOffs,position[1]-offs)

        def _sc(r,g,b,a=None):
            return (0.6*r,0.6*g,0.6*b)
        
        self._jumpImageColor = c = _sc(0.4,1,0.4)
        self._jumpImage = bs.newNode('image',
                               attrs={'texture':self._jumpButtonTex,'absoluteScale':True,
                                        'vrDepth':-20,
                                       'position':p,'scale':(imageSize,imageSize),'color':c})
        p = (position[0]+centerOffs-offs,position[1])
        self._punchImageColor = c = _sc(0.2,0.6,1) if ouya else _sc(1,0.7,0.3)
        self._punchImage = bs.newNode('image',
                               attrs={'texture':bs.getTexture('buttonPunch'),'absoluteScale':True,
                                        'vrDepth':-20,
                                      'position':p,'scale':(imageSize,imageSize),'color':c})
        p = (position[0]+centerOffs+offs,position[1])
        self._bombImageColor = c = _sc(1,0.3,0.3)
        self._bombImage = bs.newNode('image',
                               attrs={'texture':bs.getTexture('buttonBomb'),'absoluteScale':True,
                                        'vrDepth':-20,
                                      'position':p,'scale':(imageSize,imageSize),'color':c})
        p = (position[0]+centerOffs,position[1]+offs)
        self._pickUpImageColor = c = _sc(1,0.8,0.3) if ouya else _sc(0.5,0.5,1)
        self._pickUpImage = bs.newNode('image',
                                 attrs={'texture':bs.getTexture('buttonPickUp'),'absoluteScale':True,
                                        'vrDepth':-20,
                                        'position':p,'scale':(imageSize,imageSize),'color':c})

        self._stickBasePosition = p = (position[0]-centerOffs,position[1])
        self._stickBaseImageColor = c = (0.25,0.25,0.25,1.0)
        self._stickBaseImage = bs.newNode('image',
                                          attrs={'texture':bs.getTexture('nub'),'absoluteScale':True,
                                                 'vrDepth':-40,
                                                 'position':p,'scale':(imageSize2,imageSize2),'color':c})
        self._stickNubPosition = p = (position[0]-centerOffs,position[1])
        self._stickNubImageColor = c = (0.4,0.4,0.4,1.0)
        self._stickNubImage = bs.newNode('image',
                                          attrs={'texture':bs.getTexture('nub'),'absoluteScale':True,
                                                 'position':p,'scale':(nubSize,nubSize),'color':c})
        self._controlUINodes = [self._jumpImage,self._punchImage,self._bombImage,self._pickUpImage,
                              self._stickBaseImage,self._stickNubImage]
        for n in self._controlUINodes:
            n.opacity = 0.0

        self._spazzes = {}
        
        # class Delay(object):
        #     def __init__(self,time):
        #         self._time = time
        #     def run(self,activity):
        #         return self._timee

        # class SetText(object):
        #     def __init__(self,text):
        #         self._text = text
        #     def run(self,activity):
        #         activity._text.text = self._text

        # self._entries = [Delay(1000),
        #                  SetText('Hi there!'),
        #                  Delay(2000),
        #                  SetText('Stuff and things'),
        #                  Delay(2000),
        #                  SetText('More stuff and whatnot')
        #              ]
        self._testFile = '/Users/ericf/Library/Containers/net.froemling.bombsquad/Data/Library/Application Support/BombSquad/foo.py'
        #self._testFileModTime = os.path.getmtime(self._testFile)

        self._readEntries()
        # self._runNextEntry()

    def _setStickImagePosition(self,x,y):

        # clamp this to a circle
        lenSquared = x*x+y*y;
        if lenSquared > 1.0:
            l = math.sqrt(lenSquared)
            mult = 1.0/l;
            x *= mult;
            y *= mult;
        
        self._stickImagePositionX = x
        self._stickImagePositionY = y
        offs = 50.0
        p = [self._stickNubPosition[0]+x*offs*self._scale,
             self._stickNubPosition[1]+y*offs*self._scale]
        c = list(self._stickNubImageColor)
        if abs(x) > 0.1 or abs(y) > 0.1:
            c[0] *= 2.0
            c[1] *= 4.0
            c[2] *= 2.0
        self._stickNubImage.position = p
        self._stickNubImage.color = c
        c = list(self._stickBaseImageColor)
        if abs(x) > 0.1 or abs(y) > 0.1:
            c[0] *= 1.5
            c[1] *= 1.5
            c[2] *= 1.5
        self._stickBaseImage.color = c
        
    def _readEntries(self):
        self._entries = []
        try:
            #print 'starting..'
            # f = open('/Users/ericf/Library/Containers/net.froemling.bombsquad/Data/Library/Application Support/BombSquad/foo.py')
            # s = f.read()
            # f.close()
            # exec(compile(s, 'foo.py', 'exec'))
            # execfile(self._testFile)

            class Reset(object):
                def __init__(self):
                    pass
                def run(self,a):

                    # if we're looping, print out how long each cycle took
                    # print out how long each cycle took..
                    if a._lastStartTime is not None:
                        diff = bs.getRealTime()-a._lastStartTime
                        a._cycleTimes.append(diff)
                        bs.screenMessage("cycle time: "+str(diff)+" (average: "+str(sum(a._cycleTimes)/len(a._cycleTimes))+")")
                    a._lastStartTime = bs.getRealTime()

                    a._text.text = ''
                    for spaz in a._spazzes.values():
                        spaz.handleMessage(bs.DieMessage(immediate=True))
                    a._spazzes = {}
                    a._currentSpaz = None
                    for n in a._controlUINodes:
                        n.opacity = 0.0
                    a._setStickImagePosition(0,0)

            class SetSpeed(object):
                def __init__(self,speed):
                    self._speed = speed
                def run(self,a):
                    import bsInternal
                    print 'setting to',self._speed
                    bsInternal._setDebugSpeedExponent(self._speed)

            class RemoveGloves(object):
                def __init__(self):
                    pass
                def run(self,a):
                    #print 'WOuld remove gloves'
                    a._currentSpaz._glovesWearOff()

            # grumble - sometimes our real punches aren't landing due to simulator
            # variance so we force the issue if need be..
            class FakePunch(object):
                def __init__(self):
                    pass
                def run(self,a):
                    print 'WOULD FAKE PUNCH'

            class KillSpaz(object):
                def __init__(self,num,explode=False):
                    self._num = num
                    self._explode = explode
                def run(self,a):
                    #a._spazzes[self._num].hitPoints *= 0.1
                    if self._explode:
                        a._spazzes[self._num].shatter()
                    del a._spazzes[self._num]

            class SpawnSpaz(object):
                def __init__(self,num,position,color=(1,1,1),makeCurrent=False,relativeTo=None,name='',flash=True, angle=0):
                    self._num = num
                    self._position = position
                    self._makeCurrent = makeCurrent
                    self._color = color
                    self._relativeTo = relativeTo
                    self._name = name
                    self._flash = flash
                    self._angle = angle
                def run(self,a):

                    # if they gave a 'relative to' spaz, position is relative to them
                    if self._relativeTo is not None:
                        theirPos = a._spazzes[self._relativeTo].node.position
                        pos = (theirPos[0]+self._position[0],
                               theirPos[1]+self._position[1],
                               theirPos[2]+self._position[2])
                    else: pos = self._position

                    # if there's already a spaz at this spot, insta-kill it
                    if self._num in a._spazzes:
                        a._spazzes[self._num].handleMessage(bs.DieMessage(immediate=True))

                    s = a._spazzes[self._num] = bs.Spaz(color=self._color, startInvincible=self._flash, demoMode=True)
                    # FIXME - should extend spaz to support Lstr names
                    s.node.name = self._name.evaluate() if type(self._name) is bs.Lstr else self._name
                    s.node.nameColor = self._color
                    s.handleMessage(bs.StandMessage(pos,self._angle))
                    if self._makeCurrent:
                        a._currentSpaz = s
                    if self._flash: bs.playSound(a._spawnSound,position=pos)

            class Powerup(object):
                def __init__(self,num,position,color=(1,1,1),makeCurrent=False,relativeTo=None):
                    self._position = position
                    self._relativeTo = relativeTo
                def run(self,a):
                    # if they gave a 'relative to' spaz, position is relative to them
                    if self._relativeTo is not None:
                        theirPos = a._spazzes[self._relativeTo].node.position
                        pos = (theirPos[0]+self._position[0],
                               theirPos[1]+self._position[1],
                               theirPos[2]+self._position[2])
                    else: pos = self._position

                    bs.Powerup(position=pos,powerupType='punch').autoRetain()

            class Delay(object):
                def __init__(self,time,):
                    self._time = time
                def run(self,a):
                    return self._time

            class AnalyticsScreen(object):
                def __init__(self,screen):
                    self._screen = screen
                def run(self,a):
                    bsInternal._setAnalyticsScreen(self._screen)

            class DelayOld(object):
                def __init__(self,time,):
                    self._time = time
                def run(self,a):
                    return int(0.9*self._time)

            class DelayOld2(object):
                def __init__(self,time,):
                    self._time = time
                def run(self,a):
                    return int(0.8*self._time)

            class End(object):
                def __init__(self):
                    pass
                def run(self,a):
                    bsInternal._incrementAnalyticsCount('Tutorial finish')
                    a.end()

            class Move(object):
                def __init__(self,x,y):
                    self._x = float(x)
                    self._y = float(y)
                def run(self,a):
                    s = a._currentSpaz
                    # FIXME - game should take floats for this..
                    # xClamped = max(-32767,min(32767,int(self._x*32768.0)))
                    # yClamped = max(-32767,min(32767,int(self._y*32768.0)))
                    xClamped = self._x
                    yClamped = self._y
                    #print 'MOVING',xClamped,yClamped
                    s.onMoveLeftRight(xClamped)
                    s.onMoveUpDown(yClamped)
                    a._setStickImagePosition(self._x,self._y)

            class MoveLR(object):
                def __init__(self,x):
                    self._x = float(x)
                def run(self,a):
                    s = a._currentSpaz
                    # FIXME - game should take floats for this..
                    #xClamped = max(-32767,min(32767,int(self._x*32768.0)))
                    xClamped = self._x
                    s.onMoveLeftRight(xClamped)
                    a._setStickImagePosition(self._x,a._stickImagePositionY)

            class MoveUD(object):
                def __init__(self,y):
                    self._y = float(y)
                def run(self,a):
                    s = a._currentSpaz
                    # FIXME - game should take floats for this..
                    #yClamped = max(-32767,min(32767,int(self._y*32768.0)))
                    yClamped = self._y
                    #print 'MOVING UD',yClamped
                    #print 'MOVING',xClamped,yClamped
                    s.onMoveUpDown(yClamped)
                    a._setStickImagePosition(a._stickImagePositionX,self._y)

            class Bomb(ButtonPress):
                def __init__(self,delay=0,release=True,releaseDelay=500):
                    ButtonPress.__init__(self,'bomb',delay=delay,release=release,releaseDelay=releaseDelay)

            class Jump(ButtonPress):
                def __init__(self,delay=0,release=True,releaseDelay=500):
                    ButtonPress.__init__(self,'jump',delay=delay,release=release,releaseDelay=releaseDelay)

            class Punch(ButtonPress):
                def __init__(self,delay=0,release=True,releaseDelay=500):
                    ButtonPress.__init__(self,'punch',delay=delay,release=release,releaseDelay=releaseDelay)

            class PickUp(ButtonPress):
                def __init__(self,delay=0,release=True,releaseDelay=500):
                    ButtonPress.__init__(self,'pickUp',delay=delay,release=release,releaseDelay=releaseDelay)

            class Run(ButtonPress):
                def __init__(self,delay=0,release=True,releaseDelay=500):
                    ButtonPress.__init__(self,'run',delay=delay,release=release,releaseDelay=releaseDelay)

            class BombRelease(ButtonRelease):
                def __init__(self,delay=0):
                    ButtonRelease.__init__(self,'bomb',delay=delay)

            class JumpRelease(ButtonRelease):
                def __init__(self,delay=0):
                    ButtonRelease.__init__(self,'jump',delay=delay)

            class PunchRelease(ButtonRelease):
                def __init__(self,delay=0):
                    ButtonRelease.__init__(self,'punch',delay=delay)

            class PickUpRelease(ButtonRelease):
                def __init__(self,delay=0):
                    ButtonRelease.__init__(self,'pickUp',delay=delay)

            class RunRelease(ButtonRelease):
                def __init__(self,delay=0):
                    ButtonRelease.__init__(self,'run',delay=delay)


            class ShowControls(object):
                def __init__(self):
                    pass
                def run(self,a):
                    for n in a._controlUINodes:
                        bs.animate(n,'opacity',{0:0.0,1000:1.0})

            class Text(object):
                def __init__(self,text):
                    self._text = text
                def run(self,a):
                    pass
                    a._text.text = self._text

            class PrintPos(object):
                def __init__(self,spazNum=None):
                    self._spazNum = spazNum
                def run(self,a):
                    if self._spazNum is None:
                        s = a._currentSpaz
                    else:
                        s = a._spazzes[self._spazNum]
                    t = list(s.node.position)
                    print 'RestorePos('+str((t[0],t[1]-1.0,t[2]))+'),'

            class RestorePos(object):
                def __init__(self,pos):
                    self._pos = pos
                def run(self,a):
                    s = a._currentSpaz
                    s.handleMessage(bs.StandMessage(self._pos,0))

            class Celebrate(object):
                def __init__(self,celebrateType='both',spazNum=None,duration=1000):
                    self._spazNum = spazNum
                    self._celebrateType = celebrateType
                    self._duration = duration
                def run(self,a):
                    if self._spazNum is None:
                        s = a._currentSpaz
                    else:
                        s = a._spazzes[self._spazNum]
                    if self._celebrateType == 'right':
                        s.node.handleMessage('celebrateR',self._duration)
                    elif self._celebrateType == 'left':
                        s.node.handleMessage('celebrateL',self._duration)
                    elif self._celebrateType == 'both':
                        s.node.handleMessage('celebrate',self._duration)
                    else: raise Exception("invalid celebrate type "+self._celebrateType)

            self._entries = [Reset(),
                             SpawnSpaz(0,(0,5.5,-3.0),makeCurrent=True),
                             DelayOld(1000),
                             AnalyticsScreen('Tutorial Section 1'),
                             Text(bs.Lstr(resource=self._r+'.phrase01Text')), # hi there
                             Celebrate('left'),
                             DelayOld(2000),
                             Text(bs.Lstr(resource=self._r+'.phrase02Text',subs=[('${APP_NAME}',bs.Lstr(resource='titleText'))])), # welcome to bombsquad
                             DelayOld(80),Run(release=False),Jump(release=False),MoveLR(1),MoveUD(0),DelayOld(70),RunRelease(),JumpRelease(),DelayOld(60),MoveUD(1),DelayOld(30),MoveLR(0),DelayOld(90),MoveLR(-1),DelayOld(20),MoveUD(0),
                             DelayOld(70),MoveUD(-1),DelayOld(20),MoveLR(0),DelayOld(80),MoveUD(0),
                             DelayOld(1500),
                             Text(bs.Lstr(resource=self._r+'.phrase03Text')), # here's a few tips
                             DelayOld(1000),
                             ShowControls(),
                             DelayOld(1000),
                             Jump(),
                             DelayOld(1000),
                             Jump(),
                             DelayOld(1000),
                             AnalyticsScreen('Tutorial Section 2'),
                             Text(bs.Lstr(resource=self._r+'.phrase04Text',subs=[('${APP_NAME}',bs.Lstr(resource='titleText'))])), # many things are based on physics
                             DelayOld(20),MoveUD(0),DelayOld(60),MoveLR(0),DelayOld(10),MoveLR(0),MoveUD(0),DelayOld(10),MoveLR(0),MoveUD(0),DelayOld(20),MoveUD(-0.0575579),DelayOld(10),MoveUD(-0.207831),DelayOld(30),MoveUD(-0.309793),DelayOld(10),MoveUD(-0.474502),
                             DelayOld(10),MoveLR(0.00390637),MoveUD(-0.647053),DelayOld(20),MoveLR(-0.0745262),MoveUD(-0.819605),DelayOld(10),MoveLR(-0.168645),MoveUD(-0.937254),DelayOld(30),MoveLR(-0.294137),MoveUD(-1),DelayOld(10),MoveLR(-0.411786),DelayOld(10),MoveLR(-0.639241),
                             DelayOld(30),MoveLR(-0.75689),DelayOld(10),MoveLR(-0.905911),DelayOld(20),MoveLR(-1),DelayOld(50),MoveUD(-0.960784),DelayOld(20),MoveUD(-0.819605),MoveUD(-0.61568),DelayOld(20),MoveUD(-0.427442),DelayOld(20),MoveUD(-0.231361),DelayOld(10),MoveUD(-0.00390637),DelayOld(30),MoveUD(0.333354),
                             MoveUD(0.584338),DelayOld(20),MoveUD(0.764733),DelayOld(30),MoveLR(-0.803949),MoveUD(0.913755),DelayOld(10),MoveLR(-0.647084),MoveUD(0.992187),DelayOld(20),MoveLR(-0.435316),MoveUD(1),DelayOld(20),MoveLR(-0.168645),MoveUD(0.976501),
                             MoveLR(0.0744957),MoveUD(0.905911),DelayOld(20),MoveLR(0.270577),MoveUD(0.843165),DelayOld(20),MoveLR(0.435286),MoveUD(0.780419),DelayOld(10),MoveLR(0.66274),MoveUD(0.647084),DelayOld(30),MoveLR(0.803919),MoveUD(0.458846),
                             MoveLR(0.929411),MoveUD(0.223548),DelayOld(20),MoveLR(0.95294),MoveUD(0.137272),DelayOld(20),MoveLR(1),MoveUD(-0.0509659),DelayOld(20),MoveUD(-0.247047),DelayOld(20),MoveUD(-0.443129),DelayOld(20),MoveUD(-0.694113),MoveUD(-0.921567),
                             DelayOld(30),MoveLR(0.858821),MoveUD(-1),DelayOld(10),MoveLR(0.68627),DelayOld(10),MoveLR(0.364696),DelayOld(20),MoveLR(0.0509659),DelayOld(20),MoveLR(-0.223548),DelayOld(10),MoveLR(-0.600024),MoveUD(-0.913724),DelayOld(30),MoveLR(-0.858852),MoveUD(-0.717643),
                             MoveLR(-1),MoveUD(-0.474502),DelayOld(20),MoveUD(-0.396069),DelayOld(20),MoveUD(-0.286264),DelayOld(20),MoveUD(-0.137242),DelayOld(20),MoveUD(0.0353099),DelayOld(10),MoveUD(0.32551),DelayOld(20),MoveUD(0.592181),DelayOld(10),MoveUD(0.851009),DelayOld(10),MoveUD(1),
                             DelayOld(30),MoveLR(-0.764733),DelayOld(20),MoveLR(-0.403943),MoveLR(-0.145116),DelayOld(30),MoveLR(0.0901822),MoveLR(0.32548),DelayOld(30),MoveLR(0.560778),MoveUD(0.929441),DelayOld(20),MoveLR(0.709799),MoveUD(0.73336),MoveLR(0.803919),
                             MoveUD(0.545122),DelayOld(20),MoveLR(0.882351),MoveUD(0.356883),DelayOld(10),MoveLR(0.968627),MoveUD(0.113742),DelayOld(20),MoveLR(0.992157),MoveUD(-0.0823389),DelayOld(30),MoveUD(-0.309793),DelayOld(10),MoveUD(-0.545091),DelayOld(20),MoveLR(0.882351),
                             MoveUD(-0.874508),DelayOld(20),MoveLR(0.756859),MoveUD(-1),DelayOld(10),MoveLR(0.576464),DelayOld(20),MoveLR(0.254891),DelayOld(10),MoveLR(-0.0274667),DelayOld(10),MoveLR(-0.356883),DelayOld(30),MoveLR(-0.592181),MoveLR(-0.827479),MoveUD(-0.921567),
                             DelayOld(20),MoveLR(-1),MoveUD(-0.749016),DelayOld(20),MoveUD(-0.61568),DelayOld(10),MoveUD(-0.403912),DelayOld(20),MoveUD(-0.207831),DelayOld(10),MoveUD(0.121586),DelayOld(30),MoveUD(0.34904),DelayOld(10),MoveUD(0.560808),DelayOld(10),MoveUD(0.827479),DelayOld(30),MoveUD(1),
                             DelayOld(20),MoveLR(-0.976501),MoveLR(-0.670614),DelayOld(20),MoveLR(-0.239235),DelayOld(20),MoveLR(0.160772),DelayOld(20),MoveLR(0.443129),DelayOld(10),MoveLR(0.68627),MoveUD(0.976501),DelayOld(30),MoveLR(0.929411),MoveUD(0.73336),MoveLR(1),
                             MoveUD(0.482376),DelayOld(20),MoveUD(0.34904),DelayOld(10),MoveUD(0.160802),DelayOld(30),MoveUD(-0.0744957),DelayOld(10),MoveUD(-0.333323),DelayOld(20),MoveUD(-0.647053),DelayOld(20),MoveUD(-0.937254),DelayOld(10),MoveLR(0.858821),MoveUD(-1),DelayOld(10),MoveLR(0.576464),
                             DelayOld(30),MoveLR(0.184301),DelayOld(10),MoveLR(-0.121586),DelayOld(10),MoveLR(-0.474532),DelayOld(30),MoveLR(-0.670614),MoveLR(-0.851009),DelayOld(30),MoveLR(-1),MoveUD(-0.968627),DelayOld(20),MoveUD(-0.843135),DelayOld(10),MoveUD(-0.631367),DelayOld(20),MoveUD(-0.403912),
                             MoveUD(-0.176458),DelayOld(20),MoveUD(0.0902127),DelayOld(20),MoveUD(0.380413),DelayOld(10),MoveUD(0.717673),DelayOld(30),MoveUD(1),DelayOld(10),MoveLR(-0.741203),DelayOld(20),MoveLR(-0.458846),DelayOld(10),MoveLR(-0.145116),DelayOld(10),MoveLR(0.0980255),DelayOld(20),MoveLR(0.294107),
                             DelayOld(30),MoveLR(0.466659),MoveLR(0.717643),MoveUD(0.796106),DelayOld(20),MoveLR(0.921567),MoveUD(0.443159),DelayOld(20),MoveLR(1),MoveUD(0.145116),DelayOld(10),MoveUD(-0.0274361),DelayOld(30),MoveUD(-0.223518),MoveUD(-0.427442),
                             DelayOld(20),MoveUD(-0.874508),DelayOld(20),MoveUD(-1),DelayOld(10),MoveLR(0.929411),DelayOld(20),MoveLR(0.68627),DelayOld(20),MoveLR(0.364696),DelayOld(20),MoveLR(0.0431227),DelayOld(10),MoveLR(-0.333354),DelayOld(20),MoveLR(-0.639241),DelayOld(20),MoveLR(-0.968657),MoveUD(-0.968627),
                             DelayOld(20),MoveLR(-1),MoveUD(-0.890194),MoveUD(-0.866665),DelayOld(20),MoveUD(-0.749016),DelayOld(20),MoveUD(-0.529405),DelayOld(20),MoveUD(-0.30195),DelayOld(10),MoveUD(-0.00390637),DelayOld(10),MoveUD(0.262764),DelayOld(30),MoveLR(-0.600024),MoveUD(0.458846),
                             DelayOld(10),MoveLR(-0.294137),MoveUD(0.482376),DelayOld(20),MoveLR(-0.200018),MoveUD(0.505905),DelayOld(10),MoveLR(-0.145116),MoveUD(0.545122),DelayOld(20),MoveLR(-0.0353099),MoveUD(0.584338),DelayOld(20),MoveLR(0.137242),MoveUD(0.592181),
                             DelayOld(20),MoveLR(0.30195),DelayOld(10),MoveLR(0.490188),DelayOld(10),MoveLR(0.599994),MoveUD(0.529435),DelayOld(30),MoveLR(0.66274),MoveUD(0.3961),DelayOld(20),MoveLR(0.670583),MoveUD(0.231391),MoveLR(0.68627),MoveUD(0.0745262),
                             Move(0,-0.01),
                             DelayOld(100),
                             Move(0,0),
                             DelayOld(1000),
                             Text(bs.Lstr(resource=self._r+'.phrase05Text')), # for example when you punch..
                             DelayOld(510),
                             Move(0,-0.01),
                             DelayOld(100),
                             Move(0,0),
                             DelayOld(500),

                             SpawnSpaz(0,(-0.09249162673950195, 4.337906360626221, -2.3),makeCurrent=True,flash=False),
                             SpawnSpaz(1,(-3.1, 4.3, -2.0),makeCurrent=False,color=(1,1,0.4),
                                       # name=R.randomName1Text),
                                       name=bs.Lstr(resource=self._r+'.randomName1Text')),
                             Move(-1.0,0),
                             DelayOld(1050),
                             Move(0,-0.01),
                             DelayOld(100),
                             Move(0,0),
                             DelayOld(1000),
                             Text(bs.Lstr(resource=self._r+'.phrase06Text')), # your damage is based
                             DelayOld(1200),
                             Move(-0.05,0),
                             DelayOld(200),
                             Punch(),
                             DelayOld(800),
                             Punch(),
                             DelayOld(800),
                             Punch(),
                             DelayOld(800),
                             Move(0,-0.01),
                             DelayOld(100),
                             Move(0,0),
                             Text(bs.Lstr(resource=self._r+'.phrase07Text',subs=[('${NAME}',bs.Lstr(resource=self._r+'.randomName1Text'))])), # see that didnt hurt fred
                             DelayOld(2000),
                             Celebrate('right',spazNum=1),
                             DelayOld(1400),
                             Text(bs.Lstr(resource=self._r+'.phrase08Text')), # lets jump and spin to get more speed
                             DelayOld(30),MoveLR(0),DelayOld(40),MoveLR(0),DelayOld(40),MoveLR(0),DelayOld(130),MoveLR(0),DelayOld(100),MoveLR(0),
                             DelayOld(10),MoveLR(0.0480667),DelayOld(40),MoveLR(0.056093),MoveLR(0.0681173),DelayOld(30),MoveLR(0.0801416),DelayOld(10),MoveLR(0.184301),
                             DelayOld(10),MoveLR(0.207831),DelayOld(20),MoveLR(0.231361),DelayOld(30),MoveLR(0.239204),DelayOld(30),MoveLR(0.254891),DelayOld(40),MoveLR(0.270577),
                             DelayOld(10),MoveLR(0.30195),DelayOld(20),MoveLR(0.341166),DelayOld(30),MoveLR(0.388226),MoveLR(0.435286),DelayOld(30),MoveLR(0.490188),
                             DelayOld(10),MoveLR(0.560778),DelayOld(20),MoveLR(0.599994),DelayOld(10),MoveLR(0.647053),DelayOld(10),MoveLR(0.68627),DelayOld(30),MoveLR(0.733329),
                             DelayOld(20),MoveLR(0.764702),DelayOld(10),MoveLR(0.827448),DelayOld(20),MoveLR(0.874508),DelayOld(20),MoveLR(0.929411),DelayOld(10),MoveLR(1),
                             DelayOld(830),MoveUD(0.0274667),DelayOld(10),MoveLR(0.95294),MoveUD(0.113742),DelayOld(30),MoveLR(0.780389),MoveUD(0.184332),
                             DelayOld(10),MoveLR(0.27842),MoveUD(0.0745262),DelayOld(20),MoveLR(0),MoveUD(0),DelayOld(390),MoveLR(0),
                             MoveLR(0),DelayOld(20),MoveLR(0),DelayOld(20),MoveLR(0),DelayOld(10),MoveLR(-0.0537431),DelayOld(20),MoveLR(-0.215705),
                             DelayOld(30),MoveLR(-0.388256),MoveLR(-0.529435),DelayOld(30),MoveLR(-0.694143),DelayOld(20),MoveLR(-0.851009),MoveUD(0.0588397),
                             DelayOld(10),MoveLR(-1),MoveUD(0.0745262),Run(release=False),DelayOld(200),MoveUD(0.0509964),DelayOld(30),MoveUD(0.0117801),
                             DelayOld(20),MoveUD(-0.0901822),MoveUD(-0.372539),DelayOld(30),MoveLR(-0.898068),MoveUD(-0.890194),Jump(release=False),
                             DelayOld(20),MoveLR(-0.647084),MoveUD(-1),MoveLR(-0.427473),DelayOld(20),MoveLR(-0.00393689),DelayOld(10),MoveLR(0.537248),
                             DelayOld(30),MoveLR(1),DelayOld(50),RunRelease(),JumpRelease(),DelayOld(50),MoveUD(-0.921567),MoveUD(-0.749016),
                             DelayOld(30),MoveUD(-0.552934),DelayOld(10),MoveUD(-0.247047),DelayOld(20),MoveUD(0.200018),DelayOld(20),MoveUD(0.670614),MoveUD(1),
                             DelayOld(70),MoveLR(0.97647),DelayOld(20),MoveLR(0.764702),DelayOld(20),MoveLR(0.364696),DelayOld(20),MoveLR(0.00390637),MoveLR(-0.309824),
                             DelayOld(20),MoveLR(-0.576495),DelayOld(30),MoveLR(-0.898068),DelayOld(10),MoveLR(-1),MoveUD(0.905911),DelayOld(20),MoveUD(0.498062),
                             DelayOld(20),MoveUD(0.0274667),MoveUD(-0.403912),DelayOld(20),MoveUD(-1),Run(release=False),Jump(release=False),
                             DelayOld(10),Punch(release=False),DelayOld(70),JumpRelease(),DelayOld(110),MoveLR(-0.976501),RunRelease(),PunchRelease(),
                             DelayOld(10),MoveLR(-0.952971),DelayOld(20),MoveLR(-0.905911),MoveLR(-0.827479),DelayOld(20),MoveLR(-0.75689),DelayOld(30),MoveLR(-0.73336),
                             MoveLR(-0.694143),DelayOld(20),MoveLR(-0.670614),DelayOld(30),MoveLR(-0.66277),DelayOld(10),MoveUD(-0.960784),DelayOld(20),MoveLR(-0.623554),
                             MoveUD(-0.874508),DelayOld(10),MoveLR(-0.545122),MoveUD(-0.694113),DelayOld(20),MoveLR(-0.505905),MoveUD(-0.474502),
                             DelayOld(20),MoveLR(-0.458846),MoveUD(-0.356853),MoveLR(-0.364727),MoveUD(-0.27842),DelayOld(20),MoveLR(0.00390637),
                             Move(0,0),
                             DelayOld(1000),
                             Text(bs.Lstr(resource=self._r+'.phrase09Text')), # ah thats better
                             DelayOld(1900),
                             AnalyticsScreen('Tutorial Section 3'),
                             Text(bs.Lstr(resource=self._r+'.phrase10Text')), # running also helps
                             DelayOld(100),

                             SpawnSpaz(0,(-3.2, 4.3, -4.4),makeCurrent=True,flash=False),
                             SpawnSpaz(1,(3.3, 4.2, -5.8),makeCurrent=False,color=(0.9,0.5,1.0),
                                       name=bs.Lstr(resource=self._r+'.randomName2Text')),
                             DelayOld(1800),
                             Text(bs.Lstr(resource=self._r+'.phrase11Text')), # hold ANY button to run
                             DelayOld(300),
                             MoveUD(0),DelayOld(20),MoveUD(-0.0520646),DelayOld(20),MoveLR(0),MoveUD(-0.223518),Run(release=False),Jump(release=False),DelayOld(10),MoveLR(0.0980255),MoveUD(-0.309793),DelayOld(30),MoveLR(0.160772),MoveUD(-0.427442),
                             DelayOld(20),MoveLR(0.231361),MoveUD(-0.545091),DelayOld(10),MoveLR(0.317637),MoveUD(-0.678426),DelayOld(20),MoveLR(0.396069),MoveUD(-0.819605),MoveLR(0.482345),MoveUD(-0.913724),DelayOld(20),MoveLR(0.560778),MoveUD(-1),
                             DelayOld(20),MoveLR(0.607837),DelayOld(10),MoveLR(0.623524),DelayOld(30),MoveLR(0.647053),DelayOld(20),MoveLR(0.670583),MoveLR(0.694113),DelayOld(30),MoveLR(0.733329),DelayOld(20),MoveLR(0.764702),MoveLR(0.788232),DelayOld(20),MoveLR(0.827448),DelayOld(10),MoveLR(0.858821),
                             DelayOld(20),MoveLR(0.921567),DelayOld(30),MoveLR(0.97647),MoveLR(1),DelayOld(130),MoveUD(-0.960784),DelayOld(20),MoveUD(-0.921567),DelayOld(30),MoveUD(-0.866665),MoveUD(-0.819605),DelayOld(30),MoveUD(-0.772546),MoveUD(-0.725486),DelayOld(30),MoveUD(-0.631367),
                             DelayOld(10),MoveUD(-0.552934),DelayOld(20),MoveUD(-0.474502),DelayOld(10),MoveUD(-0.403912),DelayOld(30),MoveUD(-0.356853),DelayOld(30),MoveUD(-0.34901),DelayOld(20),MoveUD(-0.333323),DelayOld(20),MoveUD(-0.32548),DelayOld(10),MoveUD(-0.30195),DelayOld(20),MoveUD(-0.27842),DelayOld(30),MoveUD(-0.254891),
                             MoveUD(-0.231361),DelayOld(30),MoveUD(-0.207831),DelayOld(20),MoveUD(-0.199988),MoveUD(-0.176458),DelayOld(30),MoveUD(-0.137242),MoveUD(-0.0823389),DelayOld(20),MoveUD(-0.0274361),DelayOld(20),MoveUD(0.00393689),DelayOld(40),MoveUD(0.0353099),DelayOld(20),MoveUD(0.113742),
                             DelayOld(10),MoveUD(0.137272),DelayOld(20),MoveUD(0.160802),MoveUD(0.184332),DelayOld(20),MoveUD(0.207862),DelayOld(30),MoveUD(0.247078),MoveUD(0.262764),DelayOld(20),MoveUD(0.270608),DelayOld(30),MoveUD(0.294137),MoveUD(0.32551),DelayOld(30),MoveUD(0.37257),
                             Celebrate('left',1),
                             DelayOld(20),MoveUD(0.498062),MoveUD(0.560808),DelayOld(30),MoveUD(0.654927),MoveUD(0.694143),DelayOld(30),MoveUD(0.741203),DelayOld(20),MoveUD(0.780419),MoveUD(0.819636),DelayOld(20),MoveUD(0.843165),DelayOld(20),MoveUD(0.882382),DelayOld(10),MoveUD(0.913755),
                             DelayOld(30),MoveUD(0.968657),MoveUD(1),DelayOld(560),Punch(release=False),DelayOld(210),MoveUD(0.968657),DelayOld(30),MoveUD(0.75689),PunchRelease(),DelayOld(20),MoveLR(0.95294),MoveUD(0.435316),RunRelease(),JumpRelease(),
                             MoveLR(0.811762),MoveUD(0.270608),DelayOld(20),MoveLR(0.670583),MoveUD(0.160802),DelayOld(20),MoveLR(0.466659),MoveUD(0.0588397),DelayOld(10),MoveLR(0.317637),MoveUD(-0.00390637),DelayOld(20),MoveLR(0.0801416),DelayOld(10),MoveLR(0),
                             DelayOld(20),MoveLR(0),DelayOld(30),MoveLR(0),DelayOld(30),MoveLR(0),DelayOld(20),MoveLR(0),DelayOld(100),MoveLR(0),DelayOld(30),MoveUD(0),DelayOld(30),MoveUD(0),DelayOld(50),MoveUD(0),MoveUD(0),DelayOld(30),MoveLR(0),
                             MoveUD(-0.0520646),MoveLR(0),MoveUD(-0.0640889),DelayOld(20),MoveLR(0),MoveUD(-0.0881375),DelayOld(30),MoveLR(-0.0498978),MoveUD(-0.199988),MoveLR(-0.121586),MoveUD(-0.207831),DelayOld(20),MoveLR(-0.145116),
                             MoveUD(-0.223518),DelayOld(30),MoveLR(-0.152959),MoveUD(-0.231361),MoveLR(-0.192175),MoveUD(-0.262734),DelayOld(30),MoveLR(-0.200018),MoveUD(-0.27842),DelayOld(20),MoveLR(-0.239235),MoveUD(-0.30195),MoveUD(-0.309793),
                             DelayOld(40),MoveUD(-0.333323),DelayOld(10),MoveUD(-0.34901),DelayOld(30),MoveUD(-0.372539),MoveUD(-0.396069),DelayOld(20),MoveUD(-0.443129),DelayOld(20),MoveUD(-0.458815),DelayOld(10),MoveUD(-0.474502),DelayOld(50),MoveUD(-0.482345),DelayOld(30),MoveLR(-0.215705),DelayOld(30),MoveLR(-0.200018),
                             DelayOld(10),MoveLR(-0.192175),DelayOld(10),MoveLR(-0.176489),DelayOld(30),MoveLR(-0.152959),DelayOld(20),MoveLR(-0.145116),MoveLR(-0.121586),MoveUD(-0.458815),DelayOld(30),MoveLR(-0.098056),MoveUD(-0.419599),DelayOld(10),MoveLR(-0.0745262),MoveUD(-0.333323),
                             DelayOld(10),MoveLR(0.00390637),MoveUD(0),DelayOld(990),MoveLR(0),DelayOld(660),MoveUD(0),
                             AnalyticsScreen('Tutorial Section 4'),
                             Text(bs.Lstr(resource=self._r+'.phrase12Text')), # for extra-awesome punches,...
                             DelayOld(200),

                             SpawnSpaz(0,(2.368781805038452, 4.337533950805664, -4.360159873962402),makeCurrent=True,flash=False),
                             SpawnSpaz(1,(-3.2, 4.3, -4.5),makeCurrent=False,color=(1.0,0.7,0.3),
                                       # name=R.randomName3Text),
                                       name=bs.Lstr(resource=self._r+'.randomName3Text')),
                             DelayOld(100),
                             Powerup(1,(2.5,0.0,0),relativeTo=0),
                             Move(1,0),
                             DelayOld(1700),
                             Move(0,-0.1),
                             DelayOld(100),
                             Move(0,0),
                             DelayOld(500),
                             DelayOld(320),MoveLR(0),DelayOld(20),MoveLR(0),DelayOld(10),MoveLR(0),DelayOld(20),MoveLR(-0.333354),MoveLR(-0.592181),DelayOld(20),MoveLR(-0.788263),DelayOld(20),MoveLR(-1),MoveUD(0.0353099),MoveUD(0.0588397),DelayOld(10),Run(release=False),
                             DelayOld(780),MoveUD(0.0274667),MoveUD(0.00393689),DelayOld(10),MoveUD(-0.00390637),DelayOld(440),MoveUD(0.0353099),DelayOld(20),MoveUD(0.0588397),DelayOld(10),MoveUD(0.0902127),DelayOld(260),MoveUD(0.0353099),DelayOld(30),MoveUD(0.00393689),DelayOld(10),MoveUD(-0.00390637),MoveUD(-0.0274361),
                             Celebrate('left',1),
                             DelayOld(10),MoveUD(-0.0823389),DelayOld(30),MoveUD(-0.176458),MoveUD(-0.286264),DelayOld(20),MoveUD(-0.498032),Jump(release=False),MoveUD(-0.764702),DelayOld(30),MoveLR(-0.858852),MoveUD(-1),MoveLR(-0.780419),DelayOld(20),MoveLR(-0.717673),
                             DelayOld(10),MoveLR(-0.552965),DelayOld(10),MoveLR(-0.341197),DelayOld(10),MoveLR(-0.0274667),DelayOld(10),MoveLR(0.27842),DelayOld(20),MoveLR(0.811762),MoveLR(1),RunRelease(),JumpRelease(),DelayOld(260),MoveLR(0.95294),DelayOld(30),MoveLR(0.756859),
                             DelayOld(10),MoveLR(0.317637),MoveLR(-0.00393689),DelayOld(10),MoveLR(-0.341197),DelayOld(10),MoveLR(-0.647084),MoveUD(-0.921567),DelayOld(10),MoveLR(-1),MoveUD(-0.599994),MoveUD(-0.474502),DelayOld(10),MoveUD(-0.309793),DelayOld(10),MoveUD(-0.160772),
                             MoveUD(-0.0352794),Delay(10),MoveUD(0.176489),Delay(10),MoveUD(0.607868),Run(release=False),Jump(release=False),DelayOld(20),MoveUD(1),DelayOld(30),MoveLR(-0.921598),DelayOld(10),Punch(release=False),MoveLR(-0.639241),DelayOld(10),MoveLR(-0.223548),
                             DelayOld(10),MoveLR(0.254891),DelayOld(10),MoveLR(0.741172),MoveLR(1),DelayOld(40),JumpRelease(),DelayOld(40),MoveUD(0.976501),DelayOld(10),MoveUD(0.73336),DelayOld(10),MoveUD(0.309824),DelayOld(20),MoveUD(-0.184301),DelayOld(20),MoveUD(-0.811762),MoveUD(-1),
                             KillSpaz(1,explode=True),
                             DelayOld(10),RunRelease(),PunchRelease(),DelayOld(110),MoveLR(0.97647),MoveLR(0.898038),DelayOld(20),MoveLR(0.788232),DelayOld(20),MoveLR(0.670583),DelayOld(10),MoveLR(0.505875),DelayOld(10),MoveLR(0.32548),DelayOld(20),MoveLR(0.137242),DelayOld(10),MoveLR(-0.00393689),
                             DelayOld(10),MoveLR(-0.215705),MoveLR(-0.356883),DelayOld(20),MoveLR(-0.451003),DelayOld(10),MoveLR(-0.552965),DelayOld(20),MoveLR(-0.670614),MoveLR(-0.780419),DelayOld(10),MoveLR(-0.898068),DelayOld(20),MoveLR(-1),DelayOld(370),MoveLR(-0.976501),DelayOld(10),MoveLR(-0.952971),
                             DelayOld(10),MoveLR(-0.929441),MoveLR(-0.898068),DelayOld(30),MoveLR(-0.874538),DelayOld(10),MoveLR(-0.851009),DelayOld(10),MoveLR(-0.835322),MoveUD(-0.968627),DelayOld(10),MoveLR(-0.827479),MoveUD(-0.960784),DelayOld(20),MoveUD(-0.945097),DelayOld(70),MoveUD(-0.937254),
                             DelayOld(20),MoveUD(-0.913724),DelayOld(20),MoveUD(-0.890194),MoveLR(-0.780419),MoveUD(-0.827448),DelayOld(20),MoveLR(0.317637),MoveUD(0.3961),MoveLR(0.0195929),MoveUD(0.056093),DelayOld(20),MoveUD(0),DelayOld(750),MoveLR(0),
                             Text(bs.Lstr(resource=self._r+'.phrase13Text',subs=[('${NAME}',bs.Lstr(resource=self._r+'.randomName3Text'))])), # whoops sorry bill
                             RemoveGloves(),
                             DelayOld(2000),
                             AnalyticsScreen('Tutorial Section 5'),
                             Text(bs.Lstr(resource=self._r+'.phrase14Text',subs=[('${NAME}',bs.Lstr(resource=self._r+'.randomName4Text'))])), # you can pick up and throw things such as chuck here
                             SpawnSpaz(0,(-4.0, 4.3, -2.5),makeCurrent=True,flash=False,angle=90),
                             SpawnSpaz(1,(5,0,-1.0),relativeTo=0,makeCurrent=False,color=(0.4,1.0,0.7),
                                       # name=R.randomName4Text),
                                       name=bs.Lstr(resource=self._r+'.randomName4Text')),
                             DelayOld(1000),
                             Celebrate('left',1,duration=1000),
                             Move(1,0.2),
                             DelayOld(2000),
                             PickUp(),
                             DelayOld(200),
                             Move(0.5,1.0),
                             DelayOld(1200),
                             PickUp(),
                             Move(0,0),
                             DelayOld(1000),
                             Celebrate('left'),
                             DelayOld(1500),
                             Move(0,-1.0),
                             DelayOld(800),
                             Move(0,0),
                             DelayOld(800),

                             SpawnSpaz(0,(1.5, 4.3, -4.0),makeCurrent=True,flash=False,angle=0),
                             AnalyticsScreen('Tutorial Section 6'),
                             Text(bs.Lstr(resource=self._r+'.phrase15Text')), # lastly theres bombs
                             DelayOld(1900),
                             Text(bs.Lstr(resource=self._r+'.phrase16Text')), # throwing bombs takes practice
                             DelayOld(2000),
                             Bomb(),
                             Move(-0.1,-0.1),
                             DelayOld(100),
                             Move(0,0),
                             DelayOld(500),
                             DelayOld(1000),
                             Bomb(),
                             DelayOld(2000),
                             Text(bs.Lstr(resource=self._r+'.phrase17Text')), # not a very good throw
                             DelayOld(3000),
                             Text(bs.Lstr(resource=self._r+'.phrase18Text')), # moving helps you get distance
                             DelayOld(1000),
                             Bomb(),
                             DelayOld(500),
                             Move(-0.3,0),
                             DelayOld(100),
                             Move(-0.6,0),
                             DelayOld(100),
                             Move(-1,0),
                             DelayOld(800),
                             Bomb(),
                             DelayOld(400),
                             Move(0,-0.1),
                             DelayOld(100),
                             Move(0,0),
                             DelayOld(2500),
                             Text(bs.Lstr(resource=self._r+'.phrase19Text')), # jumping helps you get height
                             DelayOld(2000),
                             Bomb(),
                             DelayOld(500),
                             Move(1,0),
                             DelayOld(300),
                             Jump(releaseDelay=250),
                             DelayOld(500),
                             Jump(releaseDelay=250),
                             DelayOld(550),
                             Jump(releaseDelay=250),
                             DelayOld(160),
                             Punch(),
                             DelayOld(500),
                             Move(0,-0.1),
                             DelayOld(100),
                             Move(0,0),
                             DelayOld(2000),
                             Text(bs.Lstr(resource=self._r+'.phrase20Text')), # whiplash your bombs
                             DelayOld(1000),
            Bomb(release=False),DelayOld2(80),RunRelease(),BombRelease(),DelayOld2(620),MoveLR(0),DelayOld2(10),MoveLR(0),DelayOld2(40),MoveLR(0),DelayOld2(10),MoveLR(-0.0537431),MoveUD(0),DelayOld2(20),MoveLR(-0.262764),DelayOld2(20),MoveLR(-0.498062),
            DelayOld2(10),MoveLR(-0.639241),DelayOld2(20),MoveLR(-0.73336),DelayOld2(10),MoveLR(-0.843165),MoveUD(-0.0352794),DelayOld2(30),MoveLR(-1),DelayOld2(10),MoveUD(-0.0588092),DelayOld2(10),MoveUD(-0.160772),DelayOld2(20),MoveUD(-0.286264),DelayOld2(20),MoveUD(-0.427442),DelayOld2(10),MoveUD(-0.623524),
            DelayOld2(20),MoveUD(-0.843135),DelayOld2(10),MoveUD(-1),DelayOld2(40),MoveLR(-0.890225),DelayOld2(10),MoveLR(-0.670614),DelayOld2(20),MoveLR(-0.435316),DelayOld2(20),MoveLR(-0.184332),DelayOld2(10),MoveLR(0.00390637),DelayOld2(20),MoveLR(0.223518),DelayOld2(10),MoveLR(0.388226),DelayOld2(20),MoveLR(0.560778),
            DelayOld2(20),MoveLR(0.717643),DelayOld2(10),MoveLR(0.890194),DelayOld2(20),MoveLR(1),DelayOld2(30),MoveUD(-0.968627),DelayOld2(20),MoveUD(-0.898038),DelayOld2(10),MoveUD(-0.741172),DelayOld2(20),MoveUD(-0.498032),DelayOld2(20),MoveUD(-0.247047),DelayOld2(10),MoveUD(0.00393689),DelayOld2(20),MoveUD(0.239235),
            DelayOld2(20),MoveUD(0.458846),DelayOld2(10),MoveUD(0.70983),DelayOld2(30),MoveUD(1),DelayOld2(10),MoveLR(0.827448),DelayOld2(10),MoveLR(0.678426),DelayOld2(20),MoveLR(0.396069),DelayOld2(10),MoveLR(0.0980255),DelayOld2(20),MoveLR(-0.160802),DelayOld2(20),MoveLR(-0.388256),DelayOld2(10),MoveLR(-0.545122),
            DelayOld2(30),MoveLR(-0.73336),DelayOld2(10),MoveLR(-0.945128),DelayOld2(10),MoveLR(-1),DelayOld2(50),MoveUD(0.960814),DelayOld2(20),MoveUD(0.890225),DelayOld2(10),MoveUD(0.749046),DelayOld2(20),MoveUD(0.623554),DelayOld2(20),MoveUD(0.498062),DelayOld2(10),MoveUD(0.34904),DelayOld2(20),MoveUD(0.239235),
            DelayOld2(20),MoveUD(0.137272),DelayOld2(10),MoveUD(0.0117801),DelayOld2(20),MoveUD(-0.0117496),DelayOld2(10),MoveUD(-0.0274361),DelayOld2(90),MoveUD(-0.0352794),Run(release=False),Jump(release=False),Delay(80),Punch(release=False),DelayOld2(60),MoveLR(-0.968657),DelayOld2(20),MoveLR(-0.835322),
            DelayOld2(10),MoveLR(-0.70983),JumpRelease(),DelayOld2(30),MoveLR(-0.592181),MoveUD(-0.0588092),DelayOld2(10),MoveLR(-0.490219),MoveUD(-0.0744957),DelayOld2(10),MoveLR(-0.41963),DelayOld2(20),MoveLR(0),MoveUD(0),DelayOld2(20),MoveUD(0),
                             PunchRelease(),
                             RunRelease(),
                             DelayOld(500),
                             Move(0,-0.1),
                             DelayOld(100),
                             Move(0,0),
                             DelayOld(2000),
                             AnalyticsScreen('Tutorial Section 7'),
                             Text(bs.Lstr(resource=self._r+'.phrase21Text')), # timing your bombs can be tricky
                             Move(-1,0),
                             DelayOld(1000),
                             Move(0,-0.1),
                             DelayOld(100),
                             Move(0,0),

                             SpawnSpaz(0,(-0.7, 4.3, -3.9),makeCurrent=True,flash=False,angle=-30),
                             SpawnSpaz(1,(6.5,0,-0.75),relativeTo=0,makeCurrent=False,color=(0.3,0.8,1.0),
                                       # name=R.randomName5Text),
                                       name=bs.Lstr(resource=self._r+'.randomName5Text')),
                             DelayOld2(1000),
                             Move(-1,0),
                             DelayOld2(1800),
                             Bomb(),
                             Move(0,0),
                             DelayOld2(300),
                             Move(1,0),
                             DelayOld2(600),
                             Jump(),
                             DelayOld2(150),
                             Punch(),
                             DelayOld2(800),
                             Move(-1,0),
                             DelayOld2(1000),
                             Move(0,0),
                             DelayOld2(1500),
                             Text(bs.Lstr(resource=self._r+'.phrase22Text')), # dang
                             Delay(1500),
                             Text(''),
                             Delay(200),
                             Text(bs.Lstr(resource=self._r+'.phrase23Text')), # try cooking off
                             Delay(1500),
                             Bomb(),
                             Delay(800),
                             Move(1,0.12),
                             Delay(1100),
                             Jump(),
                             Delay(100),
                             Punch(),
                             Delay(100),
                             #SetSpeed(-1),
                             Move(0,-0.1),
                             Delay(100),
                             Move(0,0),
                             Delay(2000),
                             Text(bs.Lstr(resource=self._r+'.phrase24Text')), # hooray nicely cooked
                             Celebrate(),
                             #SetSpeed(3),
                             DelayOld(2000),
                             KillSpaz(1),
                             Text(""),
                             Move(0.5,-0.5),
                             DelayOld(1000),
                             Move(0,-0.1),
                             DelayOld(100),
                             Move(0,0),
                             DelayOld(1000),
                             AnalyticsScreen('Tutorial Section 8'),
                             Text(bs.Lstr(resource=self._r+'.phrase25Text')), # well thats just about it
                             DelayOld(2000),
                             Text(bs.Lstr(resource=self._r+'.phrase26Text')), # go get em tiger
                             DelayOld(2000),
                             Text(bs.Lstr(resource=self._r+'.phrase27Text')), # remember you training
                             DelayOld(3000),
                             Text(bs.Lstr(resource=self._r+'.phrase28Text')), # well maybe
                             DelayOld(1600),
                             Text(bs.Lstr(resource=self._r+'.phrase29Text')), # good luck
                             Celebrate('right',duration=10000),
                             DelayOld(1000),
                             AnalyticsScreen('Tutorial Complete'),

                             End(),
            #                  DelayOld(10000),
            #                  Reset(),
                         ]

        except Exception,e:
            import traceback
            traceback.print_exc(e)

        # if we read some, exec them..
        if self._entries:
            self._runNextEntry()
        # otherwise try again in a few seconds..
        else:
            #print 'no entries read; will try again soon...'
            self._readEntriesTimer = bs.Timer(3000,bs.WeakCall(self._readEntries))

        
    def _runNextEntry(self):
        
        while self._entries:

            # if our test file mod time has changed..
            # modTime = os.path.getmtime(self._testFile)
            # if modTime != self._testFileModTime:
            #     self._testFileModTime = modTime
            #     break
            
            entry = self._entries.pop(0)
            try:
                result = entry.run(self)
            except Exception,e:
                import traceback
                traceback.print_exc(e)
                break
                
            # if the entry returns an int value, set a timer..
            # otherwise just keep going..
            if result is not None:
                #int(result*0.9)
                self._entryTimer = bs.Timer(result,bs.WeakCall(self._runNextEntry))
                return
            
        # done with these entries.. start over soon
        self._readEntriesTimer = bs.Timer(1000,bs.WeakCall(self._readEntries))
        
    def _updateSkipVotes(self):
        count = sum(1 for player in self.players if player.gameData['pressed'])
        # self._skipCountText.text = self._R.skipVoteCountText.replace('${COUNT}',str(count)).replace('${TOTAL}',str(len(self.players))) if count > 0 else ''
        self._skipCountText.text = bs.Lstr(resource=self._r+'.skipVoteCountText',subs=[('${COUNT}',str(count)),('${TOTAL}',str(len(self.players)))]) if count > 0 else ''
        if count >= len(self.players) and len(self.players) > 0 and not self._haveSkipped:
            bsInternal._incrementAnalyticsCount('Tutorial skip')
            bsInternal._setAnalyticsScreen('Tutorial Skip')
            self._haveSkipped = True
            bs.playSound(bs.getSound('swish'))
            # self._skipCountText.text = self._R.skippingText
            self._skipCountText.text = bs.Lstr(resource=self._r+'.skippingText')
            self._skipText.text = ''
            self.end()
            

    def _playerPressedButton(self,player):

        # special case: if there's only one player we give the player a warning on their first press
        # (some players were thinking the onscreen guide meant they were supposed to press something)
        if len(self.players) == 1 and not self._issuedWarning:
            self._issuedWarning = True
            # self._skipText.text = self._R.skipConfirmText
            self._skipText.text = bs.Lstr(resource=self._r+'.skipConfirmText')
            self._skipText.color = (1,1,1)
            self._skipText.scale = 1.3
            incr = 50
            t = incr
            for i in range(6):
                bs.gameTimer(t,bs.Call(setattr,self._skipText,'color',(1,0.5,0.1)))
                t += incr
                bs.gameTimer(t,bs.Call(setattr,self._skipText,'color',(1,1,0)))
                t += incr
            bs.gameTimer(6000,bs.WeakCall(self._revertConfirm))
            return
            
        player.gameData['pressed'] = True

        # test...
        if not all(player.exists() for player in self.players):
            bs.printError("Nonexistant player in _playerPressedButton: "+str([str(p) for p in self.players])+': we are '+str(player))

        self._updateSkipVotes()

    def _revertConfirm(self):
        # self._skipText.text = self._R.toSkipPressAnythingText
        self._skipText.text = bs.Lstr(resource=self._r+'.toSkipPressAnythingText')
        self._skipText.color = (1,1,1)
        self._issuedWarning = False
        
    def onPlayerJoin(self,player):
        bs.Activity.onPlayerJoin(self,player)
        player.gameData['pressed'] = False
        # we just wanna know if this player presses anything..
        player.assignInputCall(('jumpPress','punchPress','bombPress','pickUpPress'),bs.Call(self._playerPressedButton,player))

    def onPlayerLeave(self,player):

        # test...
        if not all(player.exists() for player in self.players):
            bs.printError("Nonexistant player in onPlayerLeave: "+str([str(p) for p in self.players])+': we are '+str(player))

        bs.Activity.onPlayerLeave(self,player)
        # our leaving may influence the vote total needed/etc
        self._updateSkipVotes()
        
        # if all our players leave and we're in a co-op session lets leave the session
        # (otherwise we might lead into a co-op game with zero players or something)
        # if len(self.players) == 0 and isinstance(self.getSession,bs.CoopSession):
        #     self.getSession().end()

    def __del__(self):
        bs.Activity.__del__(self)
