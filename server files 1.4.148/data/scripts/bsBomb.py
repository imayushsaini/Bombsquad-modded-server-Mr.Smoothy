import bs
import bsUtils
from bsVector import Vector
import random
import weakref


class BombFactory(object):
    """
    category: Game Flow Classes

    Wraps up media and other resources used by bs.Bombs
    A single instance of this is shared between all bombs
    and can be retrieved via bs.Bomb.getFactory().

    Attributes:

       bombModel
          The bs.Model of a standard or ice bomb.

       stickyBombModel
          The bs.Model of a sticky-bomb.

       impactBombModel
          The bs.Model of an impact-bomb.

       landMinModel
          The bs.Model of a land-mine.

       tntModel
          The bs.Model of a tnt box.

       regularTex
          The bs.Texture for regular bombs.

       iceTex
          The bs.Texture for ice bombs.

       stickyTex
          The bs.Texture for sticky bombs.

       impactTex
          The bs.Texture for impact bombs.

       impactLitTex
          The bs.Texture for impact bombs with lights lit.

       landMineTex
          The bs.Texture for land-mines.

       landMineLitTex
          The bs.Texture for land-mines with the light lit.

       tntTex
          The bs.Texture for tnt boxes.

       hissSound
          The bs.Sound for the hiss sound an ice bomb makes.

       debrisFallSound
          The bs.Sound for random falling debris after an explosion.

       woodDebrisFallSound
          A bs.Sound for random wood debris falling after an explosion.

       explodeSounds
          A tuple of bs.Sounds for explosions.

       freezeSound
          A bs.Sound of an ice bomb freezing something.

       fuseSound
          A bs.Sound of a burning fuse.

       activateSound
          A bs.Sound for an activating impact bomb.

       warnSound
          A bs.Sound for an impact bomb about to explode due to time-out.

       bombMaterial
          A bs.Material applied to all bombs.

       normalSoundMaterial
          A bs.Material that generates standard bomb noises on impacts, etc.

       stickyMaterial
          A bs.Material that makes 'splat' sounds and makes collisions softer.

       landMineNoExplodeMaterial
          A bs.Material that keeps land-mines from blowing up.
          Applied to land-mines when they are created to allow land-mines to
          touch without exploding.

       landMineBlastMaterial
          A bs.Material applied to activated land-mines that causes them to
          explode on impact.

       impactBlastMaterial
          A bs.Material applied to activated impact-bombs that causes them to
          explode on impact.

       blastMaterial
          A bs.Material applied to bomb blast geometry which triggers impact
          events with what it touches.

       dinkSounds
          A tuple of bs.Sounds for when bombs hit the ground.

       stickyImpactSound
          The bs.Sound for a squish made by a sticky bomb hitting something.

       rollSound
          bs.Sound for a rolling bomb.
    """

    def getRandomExplodeSound(self):
        'Return a random explosion bs.Sound from the factory.'
        return self.explodeSounds[random.randrange(len(self.explodeSounds))]

    def __init__(self):
        """
        Instantiate a BombFactory.
        You shouldn't need to do this; call bs.Bomb.getFactory() to get a
        shared instance.
        """

        self.bombModel = bs.getModel('bomb')
        self.stickyBombModel = bs.getModel('bombSticky')
        self.impactBombModel = bs.getModel('impactBomb')
        self.landMineModel = bs.getModel('landMine')
        self.tntModel = bs.getModel('tnt')

        self.regularTex = bs.getTexture('bombColor')
        self.iceTex = bs.getTexture('bombColorIce')
        self.stickyTex = bs.getTexture('bombStickyColor')
        self.impactTex = bs.getTexture('impactBombColor')
        self.impactLitTex = bs.getTexture('impactBombColorLit')
        self.landMineTex = bs.getTexture('landMine')
        self.landMineLitTex = bs.getTexture('landMineLit')
        self.tntTex = bs.getTexture('tnt')

        self.hissSound = bs.getSound('hiss')
        self.debrisFallSound = bs.getSound('debrisFall')
        self.woodDebrisFallSound = bs.getSound('woodDebrisFall')

        self.explodeSounds = (bs.getSound('explosion01'),
                              bs.getSound('explosion02'),
                              bs.getSound('explosion03'),
                              bs.getSound('explosion04'),
                              bs.getSound('explosion05'))

        self.freezeSound = bs.getSound('freeze')
        self.fuseSound = bs.getSound('fuse01')
        self.activateSound = bs.getSound('activateBeep')
        self.warnSound = bs.getSound('warnBeep')

        # set up our material so new bombs dont collide with objects
        # that they are initially overlapping
        self.bombMaterial = bs.Material()
        self.normalSoundMaterial = bs.Material()
        self.stickyMaterial = bs.Material()

        self.bombMaterial.addActions(
            conditions=((('weAreYoungerThan',100),
                         'or',('theyAreYoungerThan',100)),
                        'and',('theyHaveMaterial',
                               bs.getSharedObject('objectMaterial'))),
            actions=(('modifyNodeCollision','collide',False)))

        # we want pickup materials to always hit us even if we're currently not
        # colliding with their node (generally due to the above rule)
        self.bombMaterial.addActions(
            conditions=('theyHaveMaterial',
                        bs.getSharedObject('pickupMaterial')),
            actions=(('modifyPartCollision','useNodeCollide', False)))
        
        self.bombMaterial.addActions(actions=('modifyPartCollision',
                                              'friction', 0.3))

        self.landMineNoExplodeMaterial = bs.Material()
        self.landMineBlastMaterial = bs.Material()
        self.landMineBlastMaterial.addActions(
            conditions=(
                ('weAreOlderThan',200),
                 'and', ('theyAreOlderThan',200),
                 'and', ('evalColliding',),
                 'and', (('theyDontHaveMaterial',
                          self.landMineNoExplodeMaterial),
                         'and', (('theyHaveMaterial',
                                  bs.getSharedObject('objectMaterial')),
                                 'or',('theyHaveMaterial',
                                       bs.getSharedObject('playerMaterial'))))),
            actions=(('message', 'ourNode', 'atConnect', ImpactMessage())))
        
        self.impactBlastMaterial = bs.Material()
        self.impactBlastMaterial.addActions(
            conditions=(('weAreOlderThan', 200),
                        'and', ('theyAreOlderThan',200),
                        'and', ('evalColliding',),
                        'and', (('theyHaveMaterial',
                                 bs.getSharedObject('footingMaterial')),
                               'or',('theyHaveMaterial',
                                     bs.getSharedObject('objectMaterial')))),
            actions=(('message','ourNode','atConnect',ImpactMessage())))

        self.blastMaterial = bs.Material()
        self.blastMaterial.addActions(
            conditions=(('theyHaveMaterial',
                         bs.getSharedObject('objectMaterial'))),
            actions=(('modifyPartCollision','collide',True),
                     ('modifyPartCollision','physical',False),
                     ('message','ourNode','atConnect',ExplodeHitMessage())))

        self.dinkSounds = (bs.getSound('bombDrop01'),
                           bs.getSound('bombDrop02'))
        self.stickyImpactSound = bs.getSound('stickyImpact')
        self.rollSound = bs.getSound('bombRoll01')

        # collision sounds
        self.normalSoundMaterial.addActions(
            conditions=('theyHaveMaterial',
                        bs.getSharedObject('footingMaterial')),
            actions=(('impactSound',self.dinkSounds,2,0.8),
                     ('rollSound',self.rollSound,3,6)))

        self.stickyMaterial.addActions(
            actions=(('modifyPartCollision','stiffness',0.1),
                     ('modifyPartCollision','damping',1.0)))

        self.stickyMaterial.addActions(
            conditions=(('theyHaveMaterial',
                         bs.getSharedObject('playerMaterial')),
                        'or', ('theyHaveMaterial',
                               bs.getSharedObject('footingMaterial'))),
            actions=(('message','ourNode','atConnect',SplatMessage())))

class SplatMessage(object):
    pass

class ExplodeMessage(object):
    pass

class ImpactMessage(object):
    """ impact bomb touched something """
    pass

class ArmMessage(object):
    pass

class WarnMessage(object):
    pass

class ExplodeHitMessage(object):
    "Message saying an object was hit"
    def __init__(self):
        pass

class Blast(bs.Actor):
    """
    category: Game Flow Classes

    An explosion, as generated by a bs.Bomb.
    """
    def __init__(self, position=(0,1,0), velocity=(0,0,0), blastRadius=2.0,
                 blastType="normal", sourcePlayer=None, hitType='explosion',
                 hitSubType='normal'):
        """
        Instantiate with given values.
        """
        bs.Actor.__init__(self)
        
        factory = Bomb.getFactory()

        self.blastType = blastType
        self.sourcePlayer = sourcePlayer

        self.hitType = hitType;
        self.hitSubType = hitSubType;

        # blast radius
        self.radius = blastRadius

        # set our position a bit lower so we throw more things upward
        self.node = bs.newNode('region', delegate=self, attrs={
            'position':(position[0], position[1]-0.1, position[2]),
            'scale':(self.radius,self.radius,self.radius),
            'type':'sphere',
            'materials':(factory.blastMaterial,
                         bs.getSharedObject('attackMaterial'))})

        bs.gameTimer(50, self.node.delete)

        # throw in an explosion and flash
        explosion = bs.newNode("explosion", attrs={
            'position':position,
            'velocity':(velocity[0],max(-1.0,velocity[1]),velocity[2]),
            'radius':self.radius,
            'big':(self.blastType == 'tnt')})
        if self.blastType == "ice":
            explosion.color = (0, 0.05, 0.4)

        bs.gameTimer(1000,explosion.delete)

        if self.blastType != 'ice':
            bs.emitBGDynamics(position=position, velocity=velocity,
                              count=int(1.0+random.random()*4),
                              emitType='tendrils',tendrilType='thinSmoke')
        bs.emitBGDynamics(
            position=position, velocity=velocity,
            count=int(4.0+random.random()*4), emitType='tendrils',
            tendrilType='ice' if self.blastType == 'ice' else 'smoke')
        bs.emitBGDynamics(
            position=position, emitType='distortion',
            spread=1.0 if self.blastType == 'tnt' else 2.0)
        
        # and emit some shrapnel..
        if self.blastType == 'ice':
            def _doEmit():
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=30, spread=2.0, scale=0.4,
                                  chunkType='ice', emitType='stickers');
            bs.gameTimer(50, _doEmit) # looks better if we delay a bit

        elif self.blastType == 'sticky':
            def _doEmit():
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(4.0+random.random()*8),
                                  spread=0.7,chunkType='slime');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(4.0+random.random()*8), scale=0.5,
                                  spread=0.7,chunkType='slime');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=15, scale=0.6, chunkType='slime',
                                  emitType='stickers');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=20, scale=0.7, chunkType='spark',
                                  emitType='stickers');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(6.0+random.random()*12),
                                  scale=0.8, spread=1.5,chunkType='spark');
            bs.gameTimer(50,_doEmit) # looks better if we delay a bit

        elif self.blastType == 'impact': # regular bomb shrapnel
            def _doEmit():
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(4.0+random.random()*8), scale=0.8,
                                  chunkType='metal');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(4.0+random.random()*8), scale=0.4,
                                  chunkType='metal');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=20, scale=0.7, chunkType='spark',
                                  emitType='stickers');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(8.0+random.random()*15), scale=0.8,
                                  spread=1.5, chunkType='spark');
            bs.gameTimer(50,_doEmit) # looks better if we delay a bit

        else: # regular or land mine bomb shrapnel
            def _doEmit():
                if self.blastType != 'tnt':
                    bs.emitBGDynamics(position=position, velocity=velocity,
                                      count=int(4.0+random.random()*8),
                                      chunkType='rock');
                    bs.emitBGDynamics(position=position, velocity=velocity,
                                      count=int(4.0+random.random()*8),
                                      scale=0.5,chunkType='rock');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=30,
                                  scale=1.0 if self.blastType=='tnt' else 0.7,
                                  chunkType='spark', emitType='stickers');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(18.0+random.random()*20),
                                  scale=1.0 if self.blastType == 'tnt' else 0.8,
                                  spread=1.5, chunkType='spark');

                # tnt throws splintery chunks
                if self.blastType == 'tnt':
                    def _emitSplinters():
                        bs.emitBGDynamics(position=position, velocity=velocity,
                                          count=int(20.0+random.random()*25),
                                          scale=0.8, spread=1.0,
                                          chunkType='splinter');
                    bs.gameTimer(10,_emitSplinters)
                
                # every now and then do a sparky one
                if self.blastType == 'tnt' or random.random() < 0.1:
                    def _emitExtraSparks():
                        bs.emitBGDynamics(position=position, velocity=velocity,
                                          count=int(10.0+random.random()*20),
                                          scale=0.8, spread=1.5,
                                          chunkType='spark');
                    bs.gameTimer(20,_emitExtraSparks)
                        
            bs.gameTimer(50,_doEmit) # looks better if we delay a bit

        light = bs.newNode('light', attrs={
            'position':position,
            'volumeIntensityScale': 10.0,
            'color': ((0.6, 0.6, 1.0) if self.blastType == 'ice'
                      else (1, 0.3, 0.1))})

        s = random.uniform(0.6,0.9)
        scorchRadius = lightRadius = self.radius
        if self.blastType == 'tnt':
            lightRadius *= 1.4
            scorchRadius *= 1.15
            s *= 3.0

        iScale = 1.6
        bsUtils.animate(light,"intensity", {
            0:2.0*iScale, int(s*20):0.1*iScale,
            int(s*25):0.2*iScale, int(s*50):17.0*iScale, int(s*60):5.0*iScale,
            int(s*80):4.0*iScale, int(s*200):0.6*iScale,
            int(s*2000):0.00*iScale, int(s*3000):0.0})
        bsUtils.animate(light,"radius", {
            0:lightRadius*0.2, int(s*50):lightRadius*0.55,
            int(s*100):lightRadius*0.3, int(s*300):lightRadius*0.15,
            int(s*1000):lightRadius*0.05})
        bs.gameTimer(int(s*3000),light.delete)

        # make a scorch that fades over time
        scorch = bs.newNode('scorch', attrs={
            'position':position,
            'size':scorchRadius*0.5,
            'big':(self.blastType == 'tnt')})
        if self.blastType == 'ice':
            scorch.color = (1,1,1.5)

        bsUtils.animate(scorch,"presence",{3000:1, 13000:0})
        bs.gameTimer(13000,scorch.delete)

        if self.blastType == 'ice':
            bs.playSound(factory.hissSound,position=light.position)
            
        p = light.position
        bs.playSound(factory.getRandomExplodeSound(),position=p)
        bs.playSound(factory.debrisFallSound,position=p)

        bs.shakeCamera(intensity=5.0 if self.blastType == 'tnt' else 1.0)

        # tnt is more epic..
        if self.blastType == 'tnt':
            bs.playSound(factory.getRandomExplodeSound(),position=p)
            def _extraBoom():
                bs.playSound(factory.getRandomExplodeSound(),position=p)
            bs.gameTimer(250,_extraBoom)
            def _extraDebrisSound():
                bs.playSound(factory.debrisFallSound,position=p)
                bs.playSound(factory.woodDebrisFallSound,position=p)
            bs.gameTimer(400,_extraDebrisSound)

    def handleMessage(self, msg):
        self._handleMessageSanityCheck()
        
        if isinstance(msg, bs.DieMessage):
            self.node.delete()

        elif isinstance(msg, ExplodeHitMessage):
            node = bs.getCollisionInfo("opposingNode")
            if node is not None and node.exists():
                t = self.node.position

                # new
                mag = 2000.0
                if self.blastType == 'ice': mag *= 0.5
                elif self.blastType == 'landMine': mag *= 2.5
                elif self.blastType == 'tnt': mag *= 2.0

                node.handleMessage(bs.HitMessage(
                    pos=t,
                    velocity=(0,0,0),
                    magnitude=mag,
                    hitType=self.hitType,
                    hitSubType=self.hitSubType,
                    radius=self.radius,
                    sourcePlayer=self.sourcePlayer))
                if self.blastType == "ice":
                    bs.playSound(Bomb.getFactory().freezeSound, 10, position=t)
                    node.handleMessage(bs.FreezeMessage())

        else:
            bs.Actor.handleMessage(self, msg)

class Bomb(bs.Actor):
    """
    category: Game Flow Classes
    
    A bomb and its variants such as land-mines and tnt-boxes.
    """

    def __init__(self, position=(0,1,0), velocity=(0,0,0), bombType='normal',
                 blastRadius=2.0, sourcePlayer=None, owner=None):
        """
        Create a new Bomb.
        
        bombType can be 'ice','impact','landMine','normal','sticky', or 'tnt'.
        Note that for impact or landMine bombs you have to call arm()
        before they will go off.
        """
        bs.Actor.__init__(self)

        factory = self.getFactory()

        if not bombType in ('ice','impact','landMine','normal','sticky','tnt'):
            raise Exception("invalid bomb type: " + bombType)
        self.bombType = bombType

        self._exploded = False

        if self.bombType == 'sticky': self._lastStickySoundTime = 0

        self.blastRadius = blastRadius
        if self.bombType == 'ice': self.blastRadius *= 1.2
        elif self.bombType == 'impact': self.blastRadius *= 0.7
        elif self.bombType == 'landMine': self.blastRadius *= 0.7
        elif self.bombType == 'tnt': self.blastRadius *= 1.45

        self._explodeCallbacks = []
        
        # the player this came from
        self.sourcePlayer = sourcePlayer

        # by default our hit type/subtype is our own, but we pick up types of
        # whoever sets us off so we know what caused a chain reaction
        self.hitType = 'explosion'
        self.hitSubType = self.bombType

        # if no owner was provided, use an unconnected node ref
        if owner is None: owner = bs.Node(None)

        # the node this came from
        self.owner = owner

        # adding footing-materials to things can screw up jumping and flying
        # since players carrying those things
        # and thus touching footing objects will think they're on solid ground..
        # perhaps we don't wanna add this even in the tnt case?..
        if self.bombType == 'tnt':
            materials = (factory.bombMaterial,
                         bs.getSharedObject('footingMaterial'),
                         bs.getSharedObject('objectMaterial'))
        else:
            materials = (factory.bombMaterial,
                         bs.getSharedObject('objectMaterial'))
            
        if self.bombType == 'impact':
            materials = materials + (factory.impactBlastMaterial,)
        elif self.bombType == 'landMine':
            materials = materials + (factory.landMineNoExplodeMaterial,)

        if self.bombType == 'sticky':
            materials = materials + (factory.stickyMaterial,)
        else:
            materials = materials + (factory.normalSoundMaterial,)

        if self.bombType == 'landMine':
            self.node = bs.newNode('prop', delegate=self, attrs={
                'position':position,
                'velocity':velocity,
                'model':factory.landMineModel,
                'lightModel':factory.landMineModel,
                'body':'landMine',
                'shadowSize':0.44,
                'colorTexture':factory.landMineTex,
                'reflection':'powerup',
                'reflectionScale':[1.0],
                'materials':materials})

        elif self.bombType == 'tnt':
            self.node = bs.newNode('prop', delegate=self, attrs={
                'position':position,
                'velocity':velocity,
                'model':factory.tntModel,
                'lightModel':factory.tntModel,
                'body':'crate',
                'shadowSize':0.5,
                'colorTexture':factory.tntTex,
                'reflection':'soft',
                'reflectionScale':[0.23],
                'materials':materials})
            
        elif self.bombType == 'impact':
            fuseTime = 20000
            self.node = bs.newNode('prop', delegate=self, attrs={
                'position':position,
                'velocity':velocity,
                'body':'sphere',
                'model':factory.impactBombModel,
                'shadowSize':0.3,
                'colorTexture':factory.impactTex,
                'reflection':'powerup',
                'reflectionScale':[1.5],
                'materials':materials})
            self.armTimer = bs.Timer(200, bs.WeakCall(self.handleMessage,
                                                      ArmMessage()))
            self.warnTimer = bs.Timer(fuseTime-1700,
                                      bs.WeakCall(self.handleMessage,
                                                  WarnMessage()))

        else:
            fuseTime = 3000
            if self.bombType == 'sticky':
                sticky = True
                model = factory.stickyBombModel
                rType = 'sharper'
                rScale = 1.8
            else:
                sticky = False
                model = factory.bombModel
                rType = 'sharper'
                rScale = 1.8
            if self.bombType == 'ice': tex = factory.iceTex
            elif self.bombType == 'sticky': tex = factory.stickyTex
            else: tex = factory.regularTex
            self.node = bs.newNode('bomb', delegate=self, attrs={
                'position':position,
                'velocity':velocity,
                'model':model,
                'shadowSize':0.3,
                'colorTexture':tex,
                'sticky':sticky,
                'owner':owner,
                'reflection':rType,
                'reflectionScale':[rScale],
                'materials':materials})

            sound = bs.newNode('sound', owner=self.node, attrs={
                'sound':factory.fuseSound,
                'volume':0.25})
            self.node.connectAttr('position', sound, 'position')
            bsUtils.animate(self.node, 'fuseLength', {0:1.0, fuseTime:0.0})

        # light the fuse!!!
        if self.bombType not in ('landMine','tnt'):
            bs.gameTimer(fuseTime,
                         bs.WeakCall(self.handleMessage, ExplodeMessage()))

        bsUtils.animate(self.node,"modelScale",{0:0, 200:1.3, 260:1})

    def getSourcePlayer(self):
        """
        Returns a bs.Player representing the source of this bomb.
        """
        if self.sourcePlayer is None: return bs.Player(None) # empty player ref
        return self.sourcePlayer
        
    @classmethod
    def getFactory(cls):
        """
        Returns a shared bs.BombFactory object, creating it if necessary.
        """
        activity = bs.getActivity()
        try: return activity._sharedBombFactory
        except Exception:
            f = activity._sharedBombFactory = BombFactory()
            return f

    def onFinalize(self):
        bs.Actor.onFinalize(self)
        # release callbacks/refs so we don't wind up with dependency loops..
        self._explodeCallbacks = []
        
    def _handleDie(self,m):
        self.node.delete()
        
    def _handleOOB(self, msg):
        self.handleMessage(bs.DieMessage())

    def _handleImpact(self,m):
        node,body = bs.getCollisionInfo("opposingNode","opposingBody")
        # if we're an impact bomb and we came from this node, don't explode...
        # alternately if we're hitting another impact-bomb from the same source,
        # don't explode...
        try: nodeDelegate = node.getDelegate()
        except Exception: nodeDelegate = None
        if node is not None and node.exists():
            if (self.bombType == 'impact' and
                (node is self.owner
                 or (isinstance(nodeDelegate, Bomb)
                     and nodeDelegate.bombType == 'impact'
                     and nodeDelegate.owner is self.owner))): return
            else:
                self.handleMessage(ExplodeMessage())

    def _handleDropped(self,m):
        if self.bombType == 'landMine':
            self.armTimer = \
                bs.Timer(1250, bs.WeakCall(self.handleMessage, ArmMessage()))

        # once we've thrown a sticky bomb we can stick to it..
        elif self.bombType == 'sticky':
            def _safeSetAttr(node,attr,value):
                if node.exists(): setattr(node,attr,value)
            bs.gameTimer(
                250, lambda: _safeSetAttr(self.node, 'stickToOwner', True))

    def _handleSplat(self,m):
        node = bs.getCollisionInfo("opposingNode")
        if (node is not self.owner
                and bs.getGameTime() - self._lastStickySoundTime > 1000):
            self._lastStickySoundTime = bs.getGameTime()
            bs.playSound(self.getFactory().stickyImpactSound, 2.0,
                         position=self.node.position)

    def addExplodeCallback(self,call):
        """
        Add a call to be run when the bomb has exploded.
        The bomb and the new blast object are passed as arguments.
        """
        self._explodeCallbacks.append(call)
        
    def explode(self):
        """
        Blows up the bomb if it has not yet done so.
        """
        if self._exploded: return
        self._exploded = True
        activity = self.getActivity()
        if activity is not None and self.node.exists():
            blast = Blast(
                position=self.node.position,
                velocity=self.node.velocity,
                blastRadius=self.blastRadius,
                blastType=self.bombType,
                sourcePlayer=self.sourcePlayer,
                hitType=self.hitType,
                hitSubType=self.hitSubType).autoRetain()
            for c in self._explodeCallbacks: c(self,blast)
            
        # we blew up so we need to go away
        bs.gameTimer(1, bs.WeakCall(self.handleMessage, bs.DieMessage()))

    def _handleWarn(self, m):
        if self.textureSequence.exists():
            self.textureSequence.rate = 30
            bs.playSound(self.getFactory().warnSound, 0.5,
                         position=self.node.position)

    def _addMaterial(self, material):
        if not self.node.exists(): return
        materials = self.node.materials
        if not material in materials:
            self.node.materials = materials + (material,)
        
    def arm(self):
        """
        Arms land-mines and impact-bombs so
        that they will explode on impact.
        """
        if not self.node.exists(): return
        factory = self.getFactory()
        if self.bombType == 'landMine':
            self.textureSequence = \
                bs.newNode('textureSequence', owner=self.node, attrs={
                    'rate':30,
                    'inputTextures':(factory.landMineLitTex,
                                     factory.landMineTex)})
            bs.gameTimer(500,self.textureSequence.delete)
            # we now make it explodable.
            bs.gameTimer(250,bs.WeakCall(self._addMaterial,
                                         factory.landMineBlastMaterial))
        elif self.bombType == 'impact':
            self.textureSequence = \
                bs.newNode('textureSequence', owner=self.node, attrs={
                    'rate':100,
                    'inputTextures':(factory.impactLitTex,
                                     factory.impactTex,
                                     factory.impactTex)})
            bs.gameTimer(250, bs.WeakCall(self._addMaterial,
                                          factory.landMineBlastMaterial))
        else:
            raise Exception('arm() should only be called '
                            'on land-mines or impact bombs')
        self.textureSequence.connectAttr('outputTexture',
                                         self.node, 'colorTexture')
        bs.playSound(factory.activateSound, 0.5, position=self.node.position)
        
    def _handleHit(self, msg):
        isPunch = (msg.srcNode.exists() and msg.srcNode.getNodeType() == 'spaz')

        # normal bombs are triggered by non-punch impacts..
        # impact-bombs by all impacts
        if (not self._exploded and not isPunch
            or self.bombType in ['impact', 'landMine']):
            # also lets change the owner of the bomb to whoever is setting
            # us off.. (this way points for big chain reactions go to the
            # person causing them)
            if msg.sourcePlayer not in [None]:
                self.sourcePlayer = msg.sourcePlayer

                # also inherit the hit type (if a landmine sets off by a bomb,
                # the credit should go to the mine)
                # the exception is TNT.  TNT always gets credit.
                if self.bombType != 'tnt':
                    self.hitType = msg.hitType
                    self.hitSubType = msg.hitSubType

            bs.gameTimer(100+int(random.random()*100),
                         bs.WeakCall(self.handleMessage, ExplodeMessage()))
        self.node.handleMessage(
            "impulse", msg.pos[0], msg.pos[1], msg.pos[2],
            msg.velocity[0], msg.velocity[1], msg.velocity[2],
            msg.magnitude, msg.velocityMagnitude, msg.radius, 0,
            msg.velocity[0], msg.velocity[1], msg.velocity[2])

        if msg.srcNode.exists():
            pass
        
    def handleMessage(self, msg):
        if isinstance(msg, ExplodeMessage): self.explode()
        elif isinstance(msg, ImpactMessage): self._handleImpact(msg)
        elif isinstance(msg, bs.PickedUpMessage):
            # change our source to whoever just picked us up *only* if its None
            # this way we can get points for killing bots with their own bombs
            # hmm would there be a downside to this?...
            if self.sourcePlayer is not None:
                self.sourcePlayer = msg.node.sourcePlayer
        elif isinstance(msg, SplatMessage): self._handleSplat(msg)
        elif isinstance(msg, bs.DroppedMessage): self._handleDropped(msg)
        elif isinstance(msg, bs.HitMessage): self._handleHit(msg)
        elif isinstance(msg, bs.DieMessage): self._handleDie(msg)
        elif isinstance(msg, bs.OutOfBoundsMessage): self._handleOOB(msg)
        elif isinstance(msg, ArmMessage): self.arm()
        elif isinstance(msg, WarnMessage): self._handleWarn(msg)
        else: bs.Actor.handleMessage(self, msg)

class TNTSpawner(object):
    """
    category: Game Flow Classes

    Regenerates TNT at a given point in space every now and then.
    """
    def __init__(self,position,respawnTime=30000):
        """
        Instantiate with a given position and respawnTime (in milliseconds).
        """
        self._position = position
        self._tnt = None
        self._update()
        self._updateTimer = bs.Timer(1000,bs.WeakCall(self._update),repeat=True)
        self._respawnTime = int(random.uniform(0.8,1.2)*respawnTime)
        self._waitTime = 0
        
    def _update(self):
        tntAlive = self._tnt is not None and self._tnt.node.exists()
        if not tntAlive:
            # respawn if its been long enough.. otherwise just increment our
            # how-long-since-we-died value
            if self._tnt is None or self._waitTime >= self._respawnTime:
                self._tnt = Bomb(position=self._position,bombType='tnt')
                self._waitTime = 0
            else: self._waitTime += 1000
