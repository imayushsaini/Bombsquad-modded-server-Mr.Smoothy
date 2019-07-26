import bs
import bsUtils
import random
import bsVector

_maps = {}

def preloadPreviewMedia():
    bs.getModel('levelSelectButtonOpaque')
    bs.getModel('levelSelectButtonTransparent')
    for m in _maps.values():
        mapTexName = m.getPreviewTextureName()
        if mapTexName is not None: bs.getTexture(mapTexName)
    
def registerMap(m):
    """ Register a map class with the game. """
    if _maps.has_key(m.name):
        raise Exception("map \"" + m.name + "\" already registered")
    _maps[m.name] = m

def getFilteredMapName(name):
    """ filters a map name to account for name changes, etc
    so old configs still work """
    # some legacy name fallbacks... can remove these eventually
    if name == 'AlwaysLand' or name == 'Happy Land': name = u'Happy Thoughts'
    if name == 'Hockey Arena': name = u'Hockey Stadium'
    return name

def getMapDisplayString(name):
    return bs.Lstr(translate=('mapsNames', name))

def getMapsSupportingPlayType(playType):
    """
    category: Media Functions

    Return a list of bs.Map types supporting a specified play-type (a string).
    Maps supporting a given play-type must provide a particular set of
    features or lend themselves to a certain style of play.

    Play Types:
    
    'melee' - general fighting map - has 2+ 'spawn' pts, 1+ 'powerupSpawn' pts

    'teamFlag' - for CTF, etc - has 2+ 'spawn' pts,
                 2+ 'flag' pts, and 1+ 'powerupSpawn' pts

    'keepAway'- has 2+ 'spawn' pts, 1+ 'flagDefault' pts,
                and 1+ 'powerupSpawn' pts

    'conquest' - has 2+ 'flag' pts, 2+ 'spawnByFlag' pts,
                 and 1+ 'powerupSpawn' pts

    'kingOfTheHill' - has 2+ 'spawn' pts, 1+ 'flagDefault' pts,
                      and 1+ 'powerupSpawn' pts

    'hockey' - has 2 'goal' pts, 2+ 'spawn' pts, 1+ 'flagDefault' pts,
               1+ 'powerupSpawn' pts

    'football' - has 2 'goal' pts, 2+ 'spawn' pts, 1+ 'flagDefault' pts,
                 1+ 'powerupSpawn' pts
    
    'race' - has 2+ 'racePoint' pts
    """
    maps = [m[0] for m in _maps.items() if playType in m[1].playTypes]
    maps.sort()
    return maps

def _getUnOwnedMaps():
    import bsUI
    import bsInternal
    unOwnedMaps = set()
    if bs.getEnvironment()['subplatform'] != 'headless':
        for mapSection in bsUI._getStoreLayout()['maps']:
            for m in mapSection['items']:
                if not bsInternal._getPurchased(m):
                    mInfo = bsUI._getStoreItem(m)
                    unOwnedMaps.add(mInfo['mapType'].name)
    return unOwnedMaps

def getMapClass(name):
    """ return a map type given a name """
    name = getFilteredMapName(name)
    try: return _maps[name]
    except Exception: raise Exception("Map not found: '"+name+"'")
    
class Map(bs.Actor):
    """
    category: Game Flow Classes

    A collection of terrain nodes, metadata, and other
    functionality comprising a game map.
    """
    defs = None
    name = "Map"
    playTypes = []

    @classmethod
    def preload(cls,onDemand=False):
        """ Preload map media.
        This runs the class's onPreload function if need be to prep it to run.
        Preloading can be fired for a soon-needed map to speed its creation.
        This is a classmethod since it is not run on map instances but rather on
        the class as a whole before instances are made"""
        # store whether we're preloaded in the current activity
        activity = bs.getActivity()
        if activity is None: raise Exception("not in an activity")
        try: preloads = activity._mapPreloadData
        except Exception: preloads = activity._mapPreloadData = {}
        if not cls.name in preloads:
            if onDemand:
                print 'WARNING: map '+cls.name+(' was not preloaded; you can '
                                                'reduce hitches by preloading'
                                                ' your map.')
            preloads[cls.name] = cls.onPreload()
        return preloads[cls.name]

    @classmethod
    def getPreviewTextureName(cls):
        """
        Return the name of the preview texture for this map.
        """
        return None

    @classmethod
    def onPreload(cls):
        """
        Called when the map is being preloaded;
        it should load any media it requires to
        class attributes on itself.
        """
        pass

    @classmethod
    def getName(cls):
        """
        Return the unique name of this map, in English.
        """
        return cls.name

    @classmethod
    def getMusicType(cls):
        """
        Returns a particular music-type string that should be played on
        this map; or None if the default music should be used.
        """
        return None

    def __init__(self, vrOverlayCenterOffset=None):
        """
        Instantiate a map.
        """
        import bsInternal
        bs.Actor.__init__(self)
        self.preloadData = self.preload(onDemand=True)
       
        def text():
                #bySoby
                
                
                t = bs.newNode('text',
                       attrs={ 'text':' join Mr.Smoothy | FFA | Server \n to avoid spam and play fluently',
                              'scale':1.0,
                              'maxWidth':0,
                              'position':(0,137),
                              'shadow':0.5,
                              'color':((0+random.random()*1.0),(0+random.random()*1.0),(0+random.random()*1.0)),
                              'flatness':0.5,
                              'hAlign':'center',
                              'vAttach':'bottom'})
                bs.animate(t,'opacity',{0: 0.0,500: 1.0,4500: 1.0,5000: 0.0})
                bs.gameTimer(5000,t.delete)
                t = bs.newNode('text',
                       attrs={ 'text':u'\ue043FREE ADMIN CLOSING SOOON\ue043\n BECOME MEMBER TO GET FREE ADMIN \n https://discord.gg/ucyaesh\ue043',
                              'scale':1.7,
                              'maxWidth':0,
                              'position':(0,137),
                              'shadow':0.5,
                              'color':((0+random.random()*1.0),(0+random.random()*1.0),(0+random.random()*1.0)),
                              'flatness':0.5,
                              'hAlign':'center',
                              'vAttach':'bottom'})
                bs.animate(t,'opacity',{9000: 0.0,9500: 1.0,13500: 1.0,14000: 0.0})
                bs.gameTimer(14000,t.delete)
                t = bs.newNode('text',
                       attrs={ 'text':'PAY ONLY TO Mr.Smoothy  \n be aware of fake Mr.Smoothy \n join discord https://discord.gg/ucyaesh',
                              'scale':1.0,
                              'maxWidth':0,
                              'position':(0,137),
                              'shadow':0.5,
                              'color':((0+random.random()*1.0),(0+random.random()*1.0),(0+random.random()*1.0)),
                              'flatness':0.5,
                              'hAlign':'center',
                              'vAttach':'bottom'})
                bs.animate(t,'opacity',{17500: 0.0,18000: 1.0,22000: 1.0,22500: 0.0})
                bs.gameTimer(22500,t.delete)
                t = bs.newNode('text',
                       attrs={ 'text':'discord mr.smoothy#5824\n w.app +91 9457179878 to get membership',
                              'scale':1.0,
                              'maxWidth':0,
                              'position':(0,137),
                              'shadow':0.5,
                              'color':((0+random.random()*1.0),(0+random.random()*1.0),(0+random.random()*1.0)),
                              'flatness':0.5,
                              'hAlign':'center',
                              'vAttach':'bottom'})
                bs.animate(t,'opacity',{26500: 0.0,27000: 1.0,31000: 1.0,31500: 0.0})
                bs.gameTimer(31500,t.delete)
                t = bs.newNode('text',
                       attrs={ 'text':'join discord channel to get membership \n discord link in stats button https://discord.gg/ucyaesh',
                              'scale':1.0,
                              'maxWidth':0,
                              'position':(0,137),
                              'shadow':0.5,
                              'color':((0+random.random()*1.0),(0+random.random()*1.0),(0+random.random()*1.0)),
                              'flatness':0.5,
                              'hAlign':'center',
                              'vAttach':'bottom'})
                bs.animate(t,'opacity',{35500: 0.0,36000: 1.0,40000: 1.0,40500: 0.0})
                bs.gameTimer(40500,t.delete)
                t = bs.newNode('text',
                       attrs={ 'text':'/help to check available commands https://discord.gg/ucyaesh',
                              'scale':1.0,
                              'maxWidth':0,
                              'position':(0,137),
                              'shadow':0.5,
                              'color':((0+random.random()*1.0),(0+random.random()*1.0),(0+random.random()*1.0)),
                              'flatness':0.5,
                              'hAlign':'center',
                              'vAttach':'bottom'})
                bs.animate(t,'opacity',{44500: 0.0,45000: 1.0,49000: 1.0,49500: 0.0})
                bs.gameTimer(49500,t.delete)
                
        bs.gameTimer(3500,bs.Call(text))
        bs.gameTimer(73000,bs.Call(text),repeat = True)
   
       # bs.call(sainimark)
#check the video how u can paste and where to paste
        # set some defaults
        bsGlobals = bs.getSharedObject('globals')
        # area-of-interest bounds
        aoiBounds = self.getDefBoundBox("areaOfInterestBounds")
        if aoiBounds is None:
            print 'WARNING: no "aoiBounds" found for map:',self.getName()
            aoiBounds = (-1,-1,-1,1,1,1)
        bsGlobals.areaOfInterestBounds = aoiBounds
        # map bounds
        mapBounds = self.getDefBoundBox("levelBounds")
        if mapBounds is None:
            print 'WARNING: no "levelBounds" found for map:',self.getName()
            mapBounds = (-30,-10,-30,30,100,30)
        bsInternal._setMapBounds(mapBounds)
        # shadow ranges
        try: bsGlobals.shadowRange = [
                self.defs.points[v][1] for v in 
                ['shadowLowerBottom','shadowLowerTop',
                 'shadowUpperBottom','shadowUpperTop']]
        except Exception: pass
        # in vr, set a fixed point in space for the overlay to show up at..
        # by default we use the bounds center but allow the map to override it
        center = ((aoiBounds[0]+aoiBounds[3])*0.5,
                  (aoiBounds[1]+aoiBounds[4])*0.5,
                  (aoiBounds[2]+aoiBounds[5])*0.5)
        if vrOverlayCenterOffset is not None:
            center = (center[0]+vrOverlayCenterOffset[0],
                      center[1]+vrOverlayCenterOffset[1],
                      center[2]+vrOverlayCenterOffset[2])
        bsGlobals.vrOverlayCenter = center
        bsGlobals.vrOverlayCenterEnabled = True
        self.spawnPoints = self.getDefPoints("spawn") or [(0,0,0,0,0,0)]
        self.ffaSpawnPoints = self.getDefPoints("ffaSpawn") or [(0,0,0,0,0,0)]
        self.spawnByFlagPoints = (self.getDefPoints("spawnByFlag")
                                  or [(0,0,0,0,0,0)])
        self.flagPoints = self.getDefPoints("flag") or [(0,0,0)]
        self.flagPoints = [p[:3] for p in self.flagPoints] # just want points
        self.flagPointDefault = self.getDefPoint("flagDefault") or (0,1,0)
        self.powerupSpawnPoints = self.getDefPoints("powerupSpawn") or [(0,0,0)]
        self.powerupSpawnPoints = \
            [p[:3] for p in self.powerupSpawnPoints] # just want points
        self.tntPoints = self.getDefPoints("tnt") or []
        self.tntPoints = [p[:3] for p in self.tntPoints] # just want points
        self.isHockey = False
        self.isFlying = False
        self._nextFFAStartIndex = 0

    def _isPointNearEdge(self,p,running=False):
        "For bot purposes.."
        return False

    def getDefBoundBox(self,name):
        """Returns a 6 member bounds tuple or None if it is not defined."""
        try:
            b = self.defs.boxes[name]
            return (b[0]-b[6]/2.0,b[1]-b[7]/2.0,b[2]-b[8]/2.0,
                    b[0]+b[6]/2.0,b[1]+b[7]/2.0,b[2]+b[8]/2.0);
        except Exception:
            return None
        
    def getDefPoint(self,name):
        """Returns a single defined point or a default value in its absence."""
        try:
            return self.defs.points[name]
        except Exception:
            return None

    def getDefPoints(self,name):
        """
        Returns a list of points - as many sequential ones are defined
        (flag1, flag2, flag3), etc.
        """
        if self.defs and self.defs.points.has_key(name+"1"):
            pointList = []
            i = 1
            while self.defs.points.has_key(name+str(i)):
                p = self.defs.points[name+str(i)]
                if len(p) == 6:
                    pointList.append(p)
                else:
                    if len(p) != 3: raise Exception("invalid point")
                    pointList.append(p+(0,0,0))
                i += 1
            return pointList
        else:
            return None
        
    def getStartPosition(self,teamIndex):
        """
        Returns a random starting position in the map for the given team index.
        """
        pt = self.spawnPoints[teamIndex%len(self.spawnPoints)]
        xRange = (-0.5,0.5) if pt[3] == 0 else (-pt[3],pt[3])
        zRange = (-0.5,0.5) if pt[5] == 0 else (-pt[5],pt[5])
        pt = (pt[0]+random.uniform(*xRange),
              pt[1], pt[2]+random.uniform(*zRange))
        return pt

    def getFFAStartPosition(self,players):
        """
        Returns a random starting position in one of the FFA spawn areas.
        If a list of bs.Players is provided; the returned points will be
        as far from these players as possible.
        """
        # get positions for existing players
        playerPts = []
        for player in players:
            try:
                if player.actor is not None and player.actor.isAlive():
                    pt = bsVector.Vector(*player.actor.node.position)
                    playerPts.append(pt)
            except Exception,e:
                print 'EXC in getFFAStartPosition:',e

        def _getPt():
            pt = self.ffaSpawnPoints[self._nextFFAStartIndex]
            self._nextFFAStartIndex = ((self._nextFFAStartIndex+1)
                                       %len(self.ffaSpawnPoints))
            xRange = (-0.5, 0.5) if pt[3] == 0 else (-pt[3], pt[3])
            zRange = (-0.5, 0.5) if pt[5] == 0 else (-pt[5], pt[5])
            pt = (pt[0]+random.uniform(*xRange), pt[1],
                  pt[2]+random.uniform(*zRange))
            return pt

        if len(playerPts) == 0:
            return _getPt()
        else:
            # lets calc several start points and then pick whichever is
            # farthest from all existing players
            farthestPtDist = -1.0
            farthestPt = None
            for i in range(10):
                testPt = bsVector.Vector(*_getPt())
                closestPlayerDist = 9999.0
                closestPlayerPt = None
                for pp in playerPts:
                    dist = (pp-testPt).length()
                    if dist < closestPlayerDist:
                        closestPlayerDist = dist
                        closestPlayerPt = pp
                if closestPlayerDist > farthestPtDist:
                    farthestPtDist = closestPlayerDist
                    farthestPt = testPt
            return tuple(farthestPt.data)

    def getFlagPosition(self,teamIndex):
        """
        Return a flag position on the map for the given team index.
        Pass None to get the default flag point.
        (used for things such as king-of-the-hill)
        """
        if teamIndex is None:
            return self.flagPointDefault[:3]
        else:
            return self.flagPoints[teamIndex%len(self.flagPoints)][:3]

    def handleMessage(self, msg):
        if isinstance(msg, bs.DieMessage): self.node.delete()
        else: bs.Actor.handleMessage(self, msg)

######### now lets go ahead and register some maps #########

class HockeyStadium(Map):
    import hockeyStadiumDefs as defs
    name = "Hockey Stadium"
    playTypes = ['melee','hockey','teamFlag','keepAway']

    @classmethod
    def getPreviewTextureName(cls):
        return 'hockeyStadiumPreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['models'] = (bs.getModel('hockeyStadiumOuter'),
                                       bs.getModel('hockeyStadiumInner'),
                                       bs.getModel('hockeyStadiumStands'))
        data['vrFillModel'] = bs.getModel('footballStadiumVRFill')
        data['collideModel'] = bs.getCollideModel('hockeyStadiumCollide')
        data['tex'] = bs.getTexture('hockeyStadium')
        data['standsTex'] = bs.getTexture('footballStadium')
        m = bs.Material()
        m.addActions(actions=('modifyPartCollision', 'friction',0.01))
        data['iceMaterial'] = m
        return data
    
    def __init__(self):
        Map.__init__(self)
        self.node = bs.newNode("terrain", delegate=self, attrs={
            'model':self.preloadData['models'][0],
            'collideModel':self.preloadData['collideModel'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial'),
                         self.preloadData['iceMaterial']]})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['vrFillModel'],
            'vrOnly':True,
            'lighting':False,
            'background':True,
            'colorTexture':self.preloadData['standsTex']})
        self.floor = bs.newNode("terrain", attrs={
            "model":self.preloadData['models'][1],
            "colorTexture":self.preloadData['tex'],
            "opacity":0.92,
            "opacityInLowOrMediumQuality":1.0,
            "materials":[bs.getSharedObject('footingMaterial'),
                         self.preloadData['iceMaterial']]})
        self.stands = bs.newNode("terrain", attrs={
            "model":self.preloadData['models'][2],
            "visibleInReflections":False,
            "colorTexture":self.preloadData['standsTex']})
        bsGlobals = bs.getSharedObject('globals')
        bsGlobals.floorReflection = True
        bsGlobals.debrisFriction = 0.3
        bsGlobals.debrisKillHeight = -0.3
        bsGlobals.tint = (1.2,1.3,1.33)
        bsGlobals.ambientColor = (1.15,1.25,1.6)
        bsGlobals.vignetteOuter = (0.66,0.67,0.73)
        bsGlobals.vignetteInner = (0.93,0.93,0.95)
        bsGlobals.vrCameraOffset = (0,-0.8,-1.1)
        bsGlobals.vrNearClip = 0.5
        self.isHockey = True

registerMap(HockeyStadium)

class FootballStadium(Map):
    import footballStadiumDefs as defs
    name = "Football Stadium"
    playTypes = ['melee', 'football', 'teamFlag', 'keepAway']

    @classmethod
    def getPreviewTextureName(cls):
        return 'footballStadiumPreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['model'] = bs.getModel("footballStadium")
        data['vrFillModel'] = bs.getModel('footballStadiumVRFill')
        data['collideModel'] = bs.getCollideModel("footballStadiumCollide")
        data['tex'] = bs.getTexture("footballStadium")
        return data

    def __init__(self):
        Map.__init__(self)
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'model':self.preloadData['model'],
            'collideModel':self.preloadData['collideModel'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial')]})
        bs.newNode('terrain',
                   attrs={'model':self.preloadData['vrFillModel'],
                          'lighting':False,
                          'vrOnly':True,
                          'background':True,
                          'colorTexture':self.preloadData['tex']})
        g = bs.getSharedObject('globals')
        g.tint = (1.3, 1.2, 1.0)
        g.ambientColor = (1.3, 1.2, 1.0)
        g.vignetteOuter = (0.57, 0.57, 0.57)
        g.vignetteInner = (0.9, 0.9, 0.9)
        g.vrCameraOffset = (0, -0.8, -1.1)
        g.vrNearClip = 0.5

    def _isPointNearEdge(self,p,running=False):
        boxPosition = self.defs.boxes['edgeBox'][0:3]
        boxScale = self.defs.boxes['edgeBox'][6:9]
        x = (p.x() - boxPosition[0])/boxScale[0]
        z = (p.z() - boxPosition[2])/boxScale[2]
        return (x < -0.5 or x > 0.5 or z < -0.5 or z > 0.5)

registerMap(FootballStadium)

class BridgitMap(Map):
    import bridgitLevelDefs as defs
    name = "Bridgit"
    playTypes = ["melee","teamFlag",'keepAway']

    @classmethod
    def getPreviewTextureName(cls):
        return 'bridgitPreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['modelTop'] = bs.getModel("bridgitLevelTop")
        data['modelBottom'] = bs.getModel("bridgitLevelBottom")
        data['modelBG'] = bs.getModel("natureBackground")
        data['bgVRFillModel'] = bs.getModel('natureBackgroundVRFill')
        data['collideModel'] = bs.getCollideModel("bridgitLevelCollide")
        data['tex'] = bs.getTexture("bridgitLevelColor")
        data['modelBGTex'] = bs.getTexture("natureBackgroundColor")
        data['collideBG'] = bs.getCollideModel("natureBackgroundCollide")
        data['railingCollideModel'] = \
            bs.getCollideModel("bridgitLevelRailingCollide")
        data['bgMaterial'] = bs.Material()
        data['bgMaterial'].addActions(actions=('modifyPartCollision',
                                               'friction', 10.0))
        return data

    def __init__(self):
        Map.__init__(self)
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'collideModel':self.preloadData['collideModel'],
            'model':self.preloadData['modelTop'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial')]})
        self.bottom = bs.newNode('terrain', attrs={
            'model':self.preloadData['modelBottom'],
            'lighting':False,
            'colorTexture':self.preloadData['tex']})
        self.foo = bs.newNode('terrain', attrs={
            'model':self.preloadData['modelBG'],
            'lighting':False,
            'background':True,
            'colorTexture':self.preloadData['modelBGTex']})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['bgVRFillModel'],
            'lighting':False,
            'vrOnly':True,
            'background':True,
            'colorTexture':self.preloadData['modelBGTex']})
        self.railing = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['railingCollideModel'],
            'materials':[bs.getSharedObject('railingMaterial')],
            'bumper':True})
        self.bgCollide = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['collideBG'],
            'materials':[bs.getSharedObject('footingMaterial'),
                         self.preloadData['bgMaterial'],
                         bs.getSharedObject('deathMaterial')]})
        bsGlobals = bs.getSharedObject('globals')
        bsGlobals.tint = (1.1, 1.2, 1.3)
        bsGlobals.ambientColor = (1.1, 1.2, 1.3)
        bsGlobals.vignetteOuter = (0.65, 0.6, 0.55)
        bsGlobals.vignetteInner = (0.9, 0.9, 0.93)

registerMap(BridgitMap)

class BigGMap(Map):
    import bigGDefs as defs
    name = 'Big G'
    playTypes = ['race', 'melee', 'keepAway', 'teamFlag',
                 'kingOfTheHill', 'conquest']

    @classmethod
    def getPreviewTextureName(cls):
        return 'bigGPreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['modelTop'] = bs.getModel('bigG')
        data['modelBottom'] = bs.getModel('bigGBottom')
        data['modelBG'] = bs.getModel('natureBackground')
        data['bgVRFillModel'] = bs.getModel('natureBackgroundVRFill')
        data['collideModel'] = bs.getCollideModel('bigGCollide')
        data['tex'] = bs.getTexture('bigG')
        data['modelBGTex'] = bs.getTexture('natureBackgroundColor')
        data['collideBG'] = bs.getCollideModel('natureBackgroundCollide')
        data['bumperCollideModel'] = bs.getCollideModel('bigGBumper')
        data['bgMaterial'] = bs.Material()
        data['bgMaterial'].addActions(actions=('modifyPartCollision',
                                               'friction', 10.0))
        return data

    def __init__(self):
        Map.__init__(self)
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'collideModel':self.preloadData['collideModel'],
            'color':(0.7,0.7,0.7),
            'model':self.preloadData['modelTop'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial')]})
        self.bottom = bs.newNode('terrain', attrs={
            'model':self.preloadData['modelBottom'],
            'color':(0.7,0.7,0.7),
            'lighting':False,
            'colorTexture':self.preloadData['tex']})
        self.foo = bs.newNode('terrain', attrs={
            'model':self.preloadData['modelBG'],
            'lighting':False,
            'background':True,
            'colorTexture':self.preloadData['modelBGTex']})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['bgVRFillModel'],
            'lighting':False,
            'vrOnly':True,
            'background':True,
            'colorTexture':self.preloadData['modelBGTex']})
        self.railing = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['bumperCollideModel'],
            'materials':[bs.getSharedObject('railingMaterial')],
            'bumper':True})
        self.bgCollide = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['collideBG'],
            'materials':[bs.getSharedObject('footingMaterial'),
                         self.preloadData['bgMaterial'],
                         bs.getSharedObject('deathMaterial')]})
        bsGlobals = bs.getSharedObject('globals')
        bsGlobals.tint = (1.1, 1.2, 1.3)
        bsGlobals.ambientColor = (1.1, 1.2, 1.3)
        bsGlobals.vignetteOuter = (0.65, 0.6, 0.55)
        bsGlobals.vignetteInner = (0.9, 0.9, 0.93)

registerMap(BigGMap)

class RoundaboutMap(Map):
    import roundaboutLevelDefs as defs
    name = 'Roundabout'
    playTypes = ['melee','keepAway','teamFlag']

    @classmethod
    def getPreviewTextureName(cls):
        return 'roundaboutPreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['model'] = bs.getModel('roundaboutLevel')
        data['modelBottom'] = bs.getModel('roundaboutLevelBottom')
        data['modelBG'] = bs.getModel('natureBackground')
        data['bgVRFillModel'] = bs.getModel('natureBackgroundVRFill')
        data['collideModel'] = bs.getCollideModel('roundaboutLevelCollide')
        data['tex'] = bs.getTexture('roundaboutLevelColor')
        data['modelBGTex'] = bs.getTexture('natureBackgroundColor')
        data['collideBG'] = bs.getCollideModel('natureBackgroundCollide')
        data['railingCollideModel'] = \
            bs.getCollideModel('roundaboutLevelBumper')
        data['bgMaterial'] = bs.Material()
        data['bgMaterial'].addActions(actions=('modifyPartCollision',
                                               'friction', 10.0))
        return data
    
    def __init__(self):
        Map.__init__(self,vrOverlayCenterOffset=(0,-1,1))
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'collideModel':self.preloadData['collideModel'],
            'model':self.preloadData['model'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial')]})
        self.bottom = bs.newNode('terrain', attrs={
            'model':self.preloadData['modelBottom'],
            'lighting':False,
            'colorTexture':self.preloadData['tex']})
        self.bg = bs.newNode('terrain', attrs={
            'model':self.preloadData['modelBG'],
            'lighting':False,
            'background':True,
            'colorTexture':self.preloadData['modelBGTex']})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['bgVRFillModel'],
            'lighting':False,
            'vrOnly':True,
            'background':True,
            'colorTexture':self.preloadData['modelBGTex']})
        self.bgCollide = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['collideBG'],
            'materials':[bs.getSharedObject('footingMaterial'),
                         self.preloadData['bgMaterial'],
                         bs.getSharedObject('deathMaterial')]})
        self.railing = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['railingCollideModel'],
            'materials':[bs.getSharedObject('railingMaterial')],
            'bumper':True})
        bsGlobals = bs.getSharedObject('globals')
        bsGlobals.tint = (1.0, 1.05, 1.1)
        bsGlobals.ambientColor = (1.0, 1.05, 1.1)
        bsGlobals.shadowOrtho = True
        bsGlobals.vignetteOuter = (0.63, 0.65, 0.7)
        bsGlobals.vignetteInner = (0.97, 0.95, 0.93)

registerMap(RoundaboutMap)

class MonkeyFaceMap(Map):
    import monkeyFaceLevelDefs as defs
    name = 'Monkey Face'
    playTypes = ['melee','keepAway','teamFlag']

    @classmethod
    def getPreviewTextureName(cls):
        return 'monkeyFacePreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['model'] = bs.getModel('monkeyFaceLevel')
        data['bottomModel'] = bs.getModel('monkeyFaceLevelBottom')
        data['modelBG'] = bs.getModel('natureBackground')
        data['bgVRFillModel'] = bs.getModel('natureBackgroundVRFill')
        data['collideModel'] = bs.getCollideModel('monkeyFaceLevelCollide')
        data['tex'] = bs.getTexture('monkeyFaceLevelColor')
        data['modelBGTex'] = bs.getTexture('natureBackgroundColor')
        data['collideBG'] = bs.getCollideModel('natureBackgroundCollide')
        data['railingCollideModel'] = \
            bs.getCollideModel('monkeyFaceLevelBumper')
        data['bgMaterial'] = bs.Material()
        data['bgMaterial'].addActions(actions=('modifyPartCollision',
                                               'friction', 10.0))
        return data
    
    def __init__(self):
        Map.__init__(self)
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'collideModel':self.preloadData['collideModel'],
            'model':self.preloadData['model'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial')]})
        self.bottom = bs.newNode('terrain', attrs={
            'model':self.preloadData['bottomModel'],
            'lighting':False,
            'colorTexture':self.preloadData['tex']})
        self.foo = bs.newNode('terrain', attrs={
            'model':self.preloadData['modelBG'],
            'lighting':False,
            'background':True,
            'colorTexture':self.preloadData['modelBGTex']})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['bgVRFillModel'],
            'lighting':False,
            'vrOnly':True,
            'background':True,
            'colorTexture':self.preloadData['modelBGTex']})
        self.bgCollide = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['collideBG'],
            'materials':[bs.getSharedObject('footingMaterial'),
                         self.preloadData['bgMaterial'],
                         bs.getSharedObject('deathMaterial')]})
        self.railing = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['railingCollideModel'],
            'materials':[bs.getSharedObject('railingMaterial')],
            'bumper':True})
        bsGlobals = bs.getSharedObject('globals')
        bsGlobals.tint = (1.1, 1.2, 1.2)
        bsGlobals.ambientColor = (1.2, 1.3, 1.3)
        bsGlobals.vignetteOuter = (0.60, 0.62, 0.66)
        bsGlobals.vignetteInner = (0.97, 0.95, 0.93)
        bsGlobals.vrCameraOffset = (-1.4, 0, 0)

registerMap(MonkeyFaceMap)

class ZigZagMap(Map):
    import zigZagLevelDefs as defs
    name = 'Zigzag'
    playTypes = ['melee', 'keepAway', 'teamFlag', 'conquest', 'kingOfTheHill']

    @classmethod
    def getPreviewTextureName(cls):
        return 'zigzagPreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['model'] = bs.getModel('zigZagLevel')
        data['modelBottom'] = bs.getModel('zigZagLevelBottom')
        data['modelBG'] = bs.getModel('natureBackground')
        data['bgVRFillModel'] = bs.getModel('natureBackgroundVRFill')
        data['collideModel'] = bs.getCollideModel('zigZagLevelCollide')
        data['tex'] = bs.getTexture('zigZagLevelColor')
        data['modelBGTex'] = bs.getTexture('natureBackgroundColor')
        data['collideBG'] = bs.getCollideModel('natureBackgroundCollide')
        data['railingCollideModel'] = bs.getCollideModel('zigZagLevelBumper')
        data['bgMaterial'] = bs.Material()
        data['bgMaterial'].addActions(actions=('modifyPartCollision',
                                               'friction', 10.0))
        return data
    
    def __init__(self):
        Map.__init__(self)
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'collideModel':self.preloadData['collideModel'],
            'model':self.preloadData['model'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial')]})
        self.foo = bs.newNode('terrain', attrs={
            'model':self.preloadData['modelBG'],
            'lighting':False,
            'colorTexture':self.preloadData['modelBGTex']})
        self.bottom = bs.newNode('terrain', attrs={
            'model':self.preloadData['modelBottom'],
            'lighting':False,
            'colorTexture':self.preloadData['tex']})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['bgVRFillModel'],
            'lighting':False,
            'vrOnly':True,
            'background':True,
            'colorTexture':self.preloadData['modelBGTex']})
        self.bgCollide = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['collideBG'],
            'materials':[bs.getSharedObject('footingMaterial'),
                         self.preloadData['bgMaterial'],
                         bs.getSharedObject('deathMaterial')]})
        self.railing = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['railingCollideModel'],
            'materials':[bs.getSharedObject('railingMaterial')],
            'bumper':True})
        bsGlobals = bs.getSharedObject('globals')
        bsGlobals.tint = (1.0, 1.15, 1.15)
        bsGlobals.ambientColor = (1.0, 1.15, 1.15)
        bsGlobals.vignetteOuter = (0.57, 0.59, 0.63)
        bsGlobals.vignetteInner = (0.97, 0.95, 0.93)
        bsGlobals.vrCameraOffset = (-1.5, 0, 0)

registerMap(ZigZagMap)

class ThePadMap(Map):
    import thePadLevelDefs as defs
    name = 'The Pad'
    playTypes = ['melee','keepAway','teamFlag','kingOfTheHill']

    @classmethod
    def getPreviewTextureName(cls):
        return 'thePadPreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['model'] = bs.getModel('thePadLevel')
        data['bottomModel'] = bs.getModel('thePadLevelBottom')
        data['collideModel'] = bs.getCollideModel('thePadLevelCollide')
        data['tex'] = bs.getTexture('thePadLevelColor')
        data['bgTex'] = bs.getTexture('menuBG')
        # fixme should chop this into vr/non-vr sections for efficiency
        data['bgModel'] = bs.getModel('thePadBG')
        data['railingCollideModel'] = bs.getCollideModel('thePadLevelBumper')
        data['vrFillMoundModel'] = bs.getModel('thePadVRFillMound')
        data['vrFillMoundTex'] = bs.getTexture('vrFillMound')
        return data

    def __init__(self):
        Map.__init__(self)
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'collideModel':self.preloadData['collideModel'],
            'model':self.preloadData['model'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial')]})
        self.bottom = bs.newNode('terrain', attrs={
            'model':self.preloadData['bottomModel'],
            'lighting':False,
            'colorTexture':self.preloadData['tex']})
        self.foo = bs.newNode('terrain', attrs={
            'model':self.preloadData['bgModel'],
            'lighting':False,
            'background':True,
            'colorTexture':self.preloadData['bgTex']})
        self.railing = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['railingCollideModel'],
            'materials':[bs.getSharedObject('railingMaterial')],
            'bumper':True})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['vrFillMoundModel'],
            'lighting':False,
            'vrOnly':True,
            'color':(0.56,0.55,0.47),
            'background':True,
            'colorTexture':self.preloadData['vrFillMoundTex']})
        bsGlobals = bs.getSharedObject('globals')
        bsGlobals.tint = (1.1, 1.1, 1.0)
        bsGlobals.ambientColor = (1.1, 1.1, 1.0)
        bsGlobals.vignetteOuter = (0.7, 0.65, 0.75)
        bsGlobals.vignetteInner = (0.95, 0.95, 0.93)

registerMap(ThePadMap)

class DoomShroomMap(Map):
    import doomShroomLevelDefs as defs
    name = 'Doom Shroom'
    playTypes = ['melee', 'keepAway', 'teamFlag']

    @classmethod
    def getPreviewTextureName(cls):
        return 'doomShroomPreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['model'] = bs.getModel('doomShroomLevel')
        data['collideModel'] = bs.getCollideModel('doomShroomLevelCollide')
        data['tex'] = bs.getTexture('doomShroomLevelColor')
        data['bgTex'] = bs.getTexture('doomShroomBGColor')
        data['bgModel'] = bs.getModel('doomShroomBG')
        data['vrFillModel'] = bs.getModel('doomShroomVRFill')
        data['stemModel'] = bs.getModel('doomShroomStem')
        data['collideBG'] = bs.getCollideModel('doomShroomStemCollide')
        return data
    
    def __init__(self):
        Map.__init__(self)
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'collideModel':self.preloadData['collideModel'],
            'model':self.preloadData['model'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial')]})
        self.foo = bs.newNode('terrain', attrs={
            'model':self.preloadData['bgModel'],
            'lighting':False,
            'background':True,
            'colorTexture':self.preloadData['bgTex']})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['vrFillModel'],
            'lighting':False,
            'vrOnly':True,
            'background':True,
            'colorTexture':self.preloadData['bgTex']})
        self.stem = bs.newNode('terrain', attrs={
            'model':self.preloadData['stemModel'],
            'lighting':False,
            'colorTexture':self.preloadData['tex']})
        self.bgCollide = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['collideBG'],
            'materials':[bs.getSharedObject('footingMaterial'),
                         bs.getSharedObject('deathMaterial')]})
        bsGlobals = bs.getSharedObject('globals')
        bsGlobals.tint = (0.82, 1.10, 1.15)
        bsGlobals.ambientColor = (0.9, 1.3, 1.1)
        bsGlobals.shadowOrtho = False
        bsGlobals.vignetteOuter = (0.76, 0.76, 0.76)
        bsGlobals.vignetteInner = (0.95, 0.95, 0.99)

    def _isPointNearEdge(self,p,running=False):
        x = p.x()
        z = p.z()
        xAdj = x*0.125
        zAdj = (z+3.7)*0.2
        if running:
            xAdj *= 1.4
            zAdj *= 1.4
        return (xAdj*xAdj+zAdj*zAdj > 1.0)

registerMap(DoomShroomMap)

class LakeFrigidMap(Map):
    import lakeFrigidDefs as defs
    name = 'Lake Frigid'
    playTypes = ['melee', 'keepAway', 'teamFlag', 'race']

    @classmethod
    def getPreviewTextureName(cls):
        return 'lakeFrigidPreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['model'] = bs.getModel('lakeFrigid')
        data['modelTop'] = bs.getModel('lakeFrigidTop')
        data['modelReflections'] = bs.getModel('lakeFrigidReflections')
        data['collideModel'] = bs.getCollideModel('lakeFrigidCollide')
        data['tex'] = bs.getTexture('lakeFrigid')
        data['texReflections'] = bs.getTexture('lakeFrigidReflections')
        data['vrFillModel'] = bs.getModel('lakeFrigidVRFill')
        m = bs.Material()
        m.addActions(actions=('modifyPartCollision','friction',0.01))
        data['iceMaterial'] = m
        return data

    def __init__(self):
        Map.__init__(self)
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'collideModel':self.preloadData['collideModel'],
            'model':self.preloadData['model'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial'),
                         self.preloadData['iceMaterial']]})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['modelTop'],
            'lighting':False,
            'colorTexture':self.preloadData['tex']})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['modelReflections'],
            'lighting':False,
            'overlay':True,
            'opacity':0.15,
            'colorTexture':self.preloadData['texReflections']})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['vrFillModel'],
            'lighting':False,
            'vrOnly':True,
            'background':True,
            'colorTexture':self.preloadData['tex']})
        g = bs.getSharedObject('globals')
        g.tint = (1, 1, 1)
        g.ambientColor = (1, 1, 1)
        g.shadowOrtho = True
        g.vignetteOuter = (0.86, 0.86, 0.86)
        g.vignetteInner = (0.95, 0.95, 0.99)
        g.vrNearClip = 0.5
        self.isHockey = True

registerMap(LakeFrigidMap)

class TipTopMap(Map):
    import tipTopLevelDefs as defs
    name = 'Tip Top'
    playTypes = ['melee', 'keepAway', 'teamFlag', 'kingOfTheHill']

    @classmethod
    def getPreviewTextureName(cls):
        return 'tipTopPreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['model'] = bs.getModel('tipTopLevel')
        data['bottomModel'] = bs.getModel('tipTopLevelBottom')
        data['collideModel'] = bs.getCollideModel('tipTopLevelCollide')
        data['tex'] = bs.getTexture('tipTopLevelColor')
        data['bgTex'] = bs.getTexture('tipTopBGColor')
        data['bgModel'] = bs.getModel('tipTopBG')
        data['railingCollideModel'] = bs.getCollideModel('tipTopLevelBumper')
        return data
    
    def __init__(self):
        Map.__init__(self,vrOverlayCenterOffset=(0,-0.2,2.5))
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'collideModel':self.preloadData['collideModel'],
            'model':self.preloadData['model'],
            'colorTexture':self.preloadData['tex'],
            'color':(0.7,0.7,0.7),
            'materials':[bs.getSharedObject('footingMaterial')]})
        self.bottom = bs.newNode('terrain', attrs={
            'model':self.preloadData['bottomModel'],
            'lighting':False,
            'color':(0.7,0.7,0.7),
            'colorTexture':self.preloadData['tex']})
        self.bg = bs.newNode('terrain', attrs={
            'model':self.preloadData['bgModel'],
            'lighting':False,
            'color':(0.4,0.4,0.4),
            'background':True,
            'colorTexture':self.preloadData['bgTex']})
        self.railing = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['railingCollideModel'],
            'materials':[bs.getSharedObject('railingMaterial')],
            'bumper':True})
        bsGlobals = bs.getSharedObject('globals')
        bsGlobals.tint = (0.8, 0.9, 1.3)
        bsGlobals.ambientColor = (0.8, 0.9, 1.3)
        bsGlobals.vignetteOuter = (0.79, 0.79, 0.69)
        bsGlobals.vignetteInner = (0.97, 0.97, 0.99)

registerMap(TipTopMap)


class CragCastleMap(Map):
    import cragCastleDefs as defs
    name = 'Crag Castle'
    playTypes = ['melee','keepAway','teamFlag','conquest']

    @classmethod
    def getPreviewTextureName(cls):
        return 'cragCastlePreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['model'] = bs.getModel('cragCastleLevel')
        data['bottomModel'] = bs.getModel('cragCastleLevelBottom')
        data['collideModel'] = bs.getCollideModel('cragCastleLevelCollide')
        data['tex'] = bs.getTexture('cragCastleLevelColor')
        data['bgTex'] = bs.getTexture('menuBG')
        # fixme should chop this into vr/non-vr sections
        data['bgModel'] = bs.getModel('thePadBG')
        data['railingCollideModel'] = \
            bs.getCollideModel('cragCastleLevelBumper')
        data['vrFillMoundModel'] = bs.getModel('cragCastleVRFillMound')
        data['vrFillMoundTex'] = bs.getTexture('vrFillMound')
        return data
    
    def __init__(self):
        Map.__init__(self)
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'collideModel':self.preloadData['collideModel'],
            'model':self.preloadData['model'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial')]})
        self.bottom = bs.newNode('terrain', attrs={
            'model':self.preloadData['bottomModel'],
            'lighting':False,
            'colorTexture':self.preloadData['tex']})
        self.bg = bs.newNode('terrain', attrs={
            'model':self.preloadData['bgModel'],
            'lighting':False,
            'background':True,
            'colorTexture':self.preloadData['bgTex']})
        self.railing = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['railingCollideModel'],
            'materials':[bs.getSharedObject('railingMaterial')],
            'bumper':True})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['vrFillMoundModel'],
            'lighting':False,
            'vrOnly':True,
            'color':(0.2,0.25,0.2),
            'background':True,
            'colorTexture':self.preloadData['vrFillMoundTex']})
        bsGlobals = bs.getSharedObject('globals')
        bsGlobals.shadowOrtho = True
        bsGlobals.shadowOffset = (0,0, -5.0)
        bsGlobals.tint = (1.15, 1.05, 0.75)
        bsGlobals.ambientColor = (1.15,1.05,0.75)
        bsGlobals.vignetteOuter = (0.6, 0.65, 0.6)
        bsGlobals.vignetteInner = (0.95, 0.95, 0.95)
        bsGlobals.vrNearClip = 1.0

registerMap(CragCastleMap)

class TowerDMap(Map):
    import towerDLevelDefs as defs
    name = 'Tower D'
    playTypes = []

    @classmethod
    def getPreviewTextureName(cls):
        return 'towerDPreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['model'] = bs.getModel('towerDLevel')
        data['modelBottom'] = bs.getModel('towerDLevelBottom')
        data['collideModel'] = bs.getCollideModel('towerDLevelCollide')
        data['tex'] = bs.getTexture('towerDLevelColor')
        data['bgTex'] = bs.getTexture('menuBG')
        # fixme should chop this into vr/non-vr sections
        data['bgModel'] = bs.getModel('thePadBG')
        data['playerWallCollideModel'] = bs.getCollideModel('towerDPlayerWall')
        data['playerWallMaterial'] = bs.Material()
        data['playerWallMaterial'].addActions(actions=(('modifyPartCollision',
                                                        'friction', 0.0)))
        # anything that needs to hit the wall can apply this material
        data['collideWithWallMaterial'] = bs.Material()
        data['playerWallMaterial'].addActions(
            conditions=('theyDontHaveMaterial',data['collideWithWallMaterial']),
            actions=(('modifyPartCollision','collide',False)))
        data['vrFillMoundModel'] = bs.getModel('stepRightUpVRFillMound')
        data['vrFillMoundTex'] = bs.getTexture('vrFillMound')
        return data

    def __init__(self):
        Map.__init__(self,vrOverlayCenterOffset=(0,1,1))
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'collideModel':self.preloadData['collideModel'],
            'model':self.preloadData['model'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial')]})
        self.nodeBottom = bs.newNode('terrain', delegate=self, attrs={
            'model':self.preloadData['modelBottom'],
            'lighting':False,
            'colorTexture':self.preloadData['tex']})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['vrFillMoundModel'],
            'lighting':False,
            'vrOnly':True,
            'color':(0.53,0.57,0.5),
            'background':True,
            'colorTexture':self.preloadData['vrFillMoundTex']})
        self.bg = bs.newNode('terrain', attrs={
            'model':self.preloadData['bgModel'],
            'lighting':False,
            'background':True,
            'colorTexture':self.preloadData['bgTex']})
        self.playerWall = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['playerWallCollideModel'],
            'affectBGDynamics':False,
            'materials':[self.preloadData['playerWallMaterial']]})
        bsGlobals = bs.getSharedObject('globals')
        bsGlobals.tint = (1.15, 1.11, 1.03)
        bsGlobals.ambientColor = (1.2, 1.1, 1.0)
        bsGlobals.vignetteOuter = (0.7, 0.73, 0.7)
        bsGlobals.vignetteInner = (0.95, 0.95, 0.95)

    def _isPointNearEdge(self,p,running=False):
        # see if we're within edgeBox
        boxes = self.defs.boxes
        boxPosition = boxes['edgeBox'][0:3]
        boxScale = boxes['edgeBox'][6:9]
        boxPosition2 = boxes['edgeBox2'][0:3]
        boxScale2 = boxes['edgeBox2'][6:9]
        x = (p.x() - boxPosition[0])/boxScale[0]
        z = (p.z() - boxPosition[2])/boxScale[2]
        x2 = (p.x() - boxPosition2[0])/boxScale2[0]
        z2 = (p.z() - boxPosition2[2])/boxScale2[2]
        # if we're outside of *both* boxes we're near the edge
        return ((x < -0.5 or x > 0.5 or z < -0.5 or z > 0.5)
                and (x2 < -0.5 or x2 > 0.5 or z2 < -0.5 or z2 > 0.5))

registerMap(TowerDMap)

class AlwaysLandMap(Map):
    import alwaysLandLevelDefs as defs
    name = 'Happy Thoughts'
    playTypes = ['melee', 'keepAway', 'teamFlag', 'conquest', 'kingOfTheHill']

    @classmethod
    def getPreviewTextureName(cls):
        return 'alwaysLandPreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['model'] = bs.getModel('alwaysLandLevel')
        data['bottomModel'] = bs.getModel('alwaysLandLevelBottom')
        data['bgModel'] = bs.getModel('alwaysLandBG')
        data['collideModel'] = bs.getCollideModel('alwaysLandLevelCollide')
        data['tex'] = bs.getTexture('alwaysLandLevelColor')
        data['bgTex'] = bs.getTexture('alwaysLandBGColor')
        data['vrFillMoundModel'] = bs.getModel('alwaysLandVRFillMound')
        data['vrFillMoundTex'] = bs.getTexture('vrFillMound')
        return data

    @classmethod
    def getMusicType(cls):
        return 'Flying'
    
    def __init__(self):
        Map.__init__(self,vrOverlayCenterOffset=(0,-3.7,2.5))
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'collideModel':self.preloadData['collideModel'],
            'model':self.preloadData['model'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial')]})
        self.bottom = bs.newNode('terrain', attrs={
            'model':self.preloadData['bottomModel'],
            'lighting':False,
            'colorTexture':self.preloadData['tex']})
        self.foo = bs.newNode('terrain', attrs={
            'model':self.preloadData['bgModel'],
            'lighting':False,
            'background':True,
            'colorTexture':self.preloadData['bgTex']})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['vrFillMoundModel'],
            'lighting':False,
            'vrOnly':True,
            'color':(0.2,0.25,0.2),
            'background':True,
            'colorTexture':self.preloadData['vrFillMoundTex']})
        g = bs.getSharedObject('globals')
        g.happyThoughtsMode = True
        g.shadowOffset = (0.0, 8.0, 5.0)
        g.tint = (1.3, 1.23, 1.0)
        g.ambientColor = (1.3, 1.23, 1.0)
        g.vignetteOuter = (0.64, 0.59, 0.69)
        g.vignetteInner = (0.95, 0.95, 0.93)
        g.vrNearClip = 1.0
        self.isFlying = True

        # throw out some tips on flying
        t = bs.newNode('text', attrs={
            'text':bs.Lstr(resource='pressJumpToFlyText'),
            'scale':1.2,
            'maxWidth':800,
            'position':(0,200),
            'shadow':0.5,
            'flatness':0.5,
            'hAlign':'center',
            'vAttach':'bottom'})
        c = bs.newNode('combine', owner=t, attrs={
            'size':4,
            'input0':0.3,
            'input1':0.9,
            'input2':0.0})
        bsUtils.animate(c, 'input3', {3000:0, 4000:1, 9000:1, 10000:0})
        c.connectAttr('output', t, 'color')
        bs.gameTimer(10000, t.delete)
        
registerMap(AlwaysLandMap)

class StepRightUpMap(Map):
    import stepRightUpLevelDefs as defs
    name = 'Step Right Up'
    playTypes = ['melee', 'keepAway', 'teamFlag', 'conquest']

    @classmethod
    def getPreviewTextureName(cls):
        return 'stepRightUpPreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['model'] = bs.getModel('stepRightUpLevel')
        data['modelBottom'] = bs.getModel('stepRightUpLevelBottom')
        data['collideModel'] = bs.getCollideModel('stepRightUpLevelCollide')
        data['tex'] = bs.getTexture('stepRightUpLevelColor')
        data['bgTex'] = bs.getTexture('menuBG')
        # fixme should chop this into vr/non-vr chunks
        data['bgModel'] = bs.getModel('thePadBG')
        data['vrFillMoundModel'] = bs.getModel('stepRightUpVRFillMound')
        data['vrFillMoundTex'] = bs.getTexture('vrFillMound')
        return data
    
    def __init__(self):
        Map.__init__(self,vrOverlayCenterOffset=(0,-1,2))
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'collideModel':self.preloadData['collideModel'],
            'model':self.preloadData['model'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial')]})
        self.nodeBottom = bs.newNode('terrain', delegate=self, attrs={
            'model':self.preloadData['modelBottom'],
            'lighting':False,
            'colorTexture':self.preloadData['tex']})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['vrFillMoundModel'],
            'lighting':False,
            'vrOnly':True,
            'color':(0.53,0.57,0.5),
            'background':True,
            'colorTexture':self.preloadData['vrFillMoundTex']})
        self.bg = bs.newNode('terrain', attrs={
            'model':self.preloadData['bgModel'],
            'lighting':False,
            'background':True,
            'colorTexture':self.preloadData['bgTex']})
        bsGlobals = bs.getSharedObject('globals')
        bsGlobals.tint = (1.2, 1.1, 1.0)
        bsGlobals.ambientColor = (1.2, 1.1, 1.0)
        bsGlobals.vignetteOuter = (0.7, 0.65, 0.75)
        bsGlobals.vignetteInner = (0.95, 0.95, 0.93)

registerMap(StepRightUpMap)

class CourtyardMap(Map):
    import courtyardLevelDefs as defs
    name = 'Courtyard'
    playTypes = ['melee', 'keepAway', 'teamFlag']

    @classmethod
    def getPreviewTextureName(cls):
        return 'courtyardPreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['model'] = bs.getModel('courtyardLevel')
        data['modelBottom'] = bs.getModel('courtyardLevelBottom')
        data['collideModel'] = bs.getCollideModel('courtyardLevelCollide')
        data['tex'] = bs.getTexture('courtyardLevelColor')
        data['bgTex'] = bs.getTexture('menuBG')
        # fixme - chop this into vr and non-vr chunks
        data['bgModel'] = bs.getModel('thePadBG')
        data['playerWallCollideModel'] = \
            bs.getCollideModel('courtyardPlayerWall')
        data['playerWallMaterial'] = bs.Material()
        data['playerWallMaterial'].addActions(actions=(('modifyPartCollision',
                                                        'friction', 0.0)))
        # anything that needs to hit the wall should apply this.
        data['collideWithWallMaterial'] = bs.Material()
        data['playerWallMaterial'].addActions(
            conditions=('theyDontHaveMaterial',
                        data['collideWithWallMaterial']),
            actions=('modifyPartCollision', 'collide', False))
        data['vrFillMoundModel'] = bs.getModel('stepRightUpVRFillMound')
        data['vrFillMoundTex'] = bs.getTexture('vrFillMound')
        return data

    def __init__(self):
        Map.__init__(self)
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'collideModel':self.preloadData['collideModel'],
            'model':self.preloadData['model'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial')]})
        self.bg = bs.newNode('terrain', attrs={
            'model':self.preloadData['bgModel'],
            'lighting':False,
            'background':True,
            'colorTexture':self.preloadData['bgTex']})
        self.bottom = bs.newNode('terrain', attrs={
            'model':self.preloadData['modelBottom'],
            'lighting':False,
            'colorTexture':self.preloadData['tex']})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['vrFillMoundModel'],
            'lighting':False,
            'vrOnly':True,
            'color':(0.53,0.57,0.5),
            'background':True,
            'colorTexture':self.preloadData['vrFillMoundTex']})
        # in co-op mode games, put up a wall to prevent players
        # from getting in the turrets (that would foil our brilliant AI)
        if isinstance(bs.getSession(), bs.CoopSession):
            self.playerWall = bs.newNode('terrain', attrs={
                'collideModel':self.preloadData['playerWallCollideModel'],
                'affectBGDynamics':False,
                'materials':[self.preloadData['playerWallMaterial']]})
        bsGlobals = bs.getSharedObject('globals')
        bsGlobals.tint = (1.2, 1.17, 1.1)
        bsGlobals.ambientColor = (1.2, 1.17, 1.1)
        bsGlobals.vignetteOuter = (0.6, 0.6, 0.64)
        bsGlobals.vignetteInner = (0.95, 0.95, 0.93)

    def _isPointNearEdge(self, p, running=False):
        # count anything off our ground level as safe (for our platforms)
        # see if we're within edgeBox
        boxPosition = self.defs.boxes['edgeBox'][0:3]
        boxScale = self.defs.boxes['edgeBox'][6:9]
        x = (p.x() - boxPosition[0])/boxScale[0]
        z = (p.z() - boxPosition[2])/boxScale[2]
        return (x < -0.5 or x > 0.5 or z < -0.5 or z > 0.5)

registerMap(CourtyardMap)

class RampageMap(Map):
    import rampageLevelDefs as defs
    name = 'Rampage'
    playTypes = ['melee', 'keepAway', 'teamFlag']

    @classmethod
    def getPreviewTextureName(cls):
        return 'rampagePreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['model'] = bs.getModel('rampageLevel')
        data['bottomModel'] = bs.getModel('rampageLevelBottom')
        data['collideModel'] = bs.getCollideModel('rampageLevelCollide')
        data['tex'] = bs.getTexture('rampageLevelColor')
        data['bgTex'] = bs.getTexture('rampageBGColor')
        data['bgTex2'] = bs.getTexture('rampageBGColor2')
        data['bgModel'] = bs.getModel('rampageBG')
        data['bgModel2'] = bs.getModel('rampageBG2')
        data['vrFillModel'] = bs.getModel('rampageVRFill')
        data['railingCollideModel'] = bs.getCollideModel('rampageBumper')
        return data
    
    def __init__(self):
        Map.__init__(self, vrOverlayCenterOffset=(0,0,2))
        self.node = bs.newNode('terrain', delegate=self, attrs={
            'collideModel':self.preloadData['collideModel'],
            'model':self.preloadData['model'],
            'colorTexture':self.preloadData['tex'],
            'materials':[bs.getSharedObject('footingMaterial')]})
        self.bg = bs.newNode('terrain', attrs={
            'model':self.preloadData['bgModel'],
            'lighting':False,
            'background':True,
            'colorTexture':self.preloadData['bgTex']})
        self.bottom = bs.newNode('terrain', attrs={
            'model':self.preloadData['bottomModel'],
            'lighting':False,
            'colorTexture':self.preloadData['tex']})
        self.bg2 = bs.newNode('terrain', attrs={
            'model':self.preloadData['bgModel2'],
            'lighting':False,
            'background':True,
            'colorTexture':self.preloadData['bgTex2']})
        bs.newNode('terrain', attrs={
            'model':self.preloadData['vrFillModel'],
            'lighting':False,
            'vrOnly':True,
            'background':True,
            'colorTexture':self.preloadData['bgTex2']})
        self.railing = bs.newNode('terrain', attrs={
            'collideModel':self.preloadData['railingCollideModel'],
            'materials':[bs.getSharedObject('railingMaterial')],
            'bumper':True})
        bsGlobals = bs.getSharedObject('globals')
        bsGlobals.tint = (1.2, 1.1, 0.97)
        bsGlobals.ambientColor = (1.3, 1.2, 1.03)
        bsGlobals.vignetteOuter = (0.62, 0.64, 0.69)
        bsGlobals.vignetteInner = (0.97, 0.95, 0.93)

    def _isPointNearEdge(self,p,running=False):
        boxPosition = self.defs.boxes['edgeBox'][0:3]
        boxScale = self.defs.boxes['edgeBox'][6:9]
        x = (p.x() - boxPosition[0])/boxScale[0]
        z = (p.z() - boxPosition[2])/boxScale[2]
        return (x < -0.5 or x > 0.5 or z < -0.5 or z > 0.5)

registerMap(RampageMap)
