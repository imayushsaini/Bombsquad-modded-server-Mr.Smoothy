import bs
import random
import bsUtils

# The volcano spews bombs and creates an impact bomb over everyone's head, though, at the cost of the user's life.
class Volcano(bs.Actor):

    def __init__(self,position = (0,1,0),color = (1,0,0), player = None):
        bs.Actor.__init__(self)

        self.radius = .6
        self.position = position
        self.player = player
        self.color = color
        self.erupted = False

        self.volcanoMaterial = bs.Material()
        self.volcanoMaterial.addActions(conditions=(('theyHaveMaterial', bs.getSharedObject('playerMaterial'))),actions=(("modifyPartCollision","collide",True),
                                                      ("modifyPartCollision","physical",False),
                                                      ("message", "theirNode","atConnect",bs.DieMessage()),
                                                      ("call","atConnect", self.erupt)))

        self.node1 = bs.newNode('region',
                       attrs={'position':(self.position[0],self.position[1],self.position[2]),
                              'scale':(self.radius,self.radius,self.radius),
                              'materials':[self.volcanoMaterial]})
        self.light = bs.newNode('locator',attrs={'shape':'circle','position':(self.position[0],self.position[1]-2,self.position[2]),
                                         'color':(1,0,0),'opacity':0.5,
                                         'drawBeauty':True,'additive':True})
        bsUtils.animateArray(self.node1,"scale",3,{0:(0,0,0),500:(self.radius,self.radius,self.radius)})
        bs.gameTimer(10000,self.die)

    def erupt(self):
        for i in range(5):
            bs.gameTimer(i*10, bs.Call(self.spurt))
        if self.erupted == True: return
        self.erupted = True
        for player in bs.getActivity().players:
            if player.isAlive() and player is not self.player:
                playerPos = player.actor.node.position
                bomb = bs.Bomb(position=(playerPos[0],playerPos[1]+6,playerPos[2]),velocity=(0,-1,0),bombType='impact',sourcePlayer=self.player).autoRetain()

    def spurt(self):
        bomb = bs.Bomb(position=(self.position[0],self.position[1]+2,self.position[2]),velocity=(6*random.random()-3,8,6*random.random()-3),sourcePlayer=self.player).autoRetain()
        bs.emitBGDynamics(position=self.position, velocity=(0,8,0), count=10)

    def die(self):
        self.node1.delete()
        self.light.delete()
        self.handleMessage(bs.DieMessage())
            
        
        
