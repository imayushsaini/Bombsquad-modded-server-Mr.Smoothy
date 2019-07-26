import bs
from bsSpaz import *
import bsSpaz
import bsUtils
import random
import bsInternal
import getPermissionsHashes as gph

class PermissionEffect(object):
    def __init__(self,position = (0,1,0),owner = None,prefix = 'ADMIN',prefixColor = (1,1,1),prefixAnim = {0:(1,1,1),500:(0.5,0.5,0.5)},prefixAnimate = True,particles = True):
        self.position = position
        self.owner = owner
        
        #nick
        #text
        #color
        #anim
        #animCurve
        #particles
        

        
        def a():
            self.emit()
            
        #particles    
        if particles:
            self.timer = bs.Timer(10,bs.Call(a),repeat = True)
            
        #prefix
        m = bs.newNode('math', owner=self.owner, attrs={'input1': (0, 1.55, 0), 'operation': 'add'})
        self.owner.connectAttr('position', m, 'input2')
        
        self._Text = bs.newNode('text',
                                      owner=self.owner,
                                      attrs={'text':prefix, #prefix text
                                             'inWorld':True,
                                             'shadow':1.2,
                                             'flatness':1.0,
                                             'color':prefixColor,
                                             'scale':0.0,
                                             'hAlign':'center'})
                                             
        m.connectAttr('output', self._Text, 'position')
        
        bs.animate(self._Text, 'scale', {0: 0.0, 1000: 0.01}) #smooth prefix spawn
        
        #animate prefix
        if prefixAnimate:
            bsUtils.animateArray(self._Text, 'color',3, prefixAnim,True) #animate prefix color
        
    def emit(self):
        if self.owner.exists():
            vel = 4
            bs.emitBGDynamics(position=(self.owner.torsoPosition[0]-0.25+random.random()*0.5,self.owner.torsoPosition[1]-0.25+random.random()*0.5,self.owner.torsoPosition[2]-0.25+random.random()*0.5),
                              velocity=((-vel+(random.random()*(vel*2)))+self.owner.velocity[0]*2,(-vel+(random.random()*(vel*2)))+self.owner.velocity[1]*4,(-vel+(random.random()*(vel*2)))+self.owner.velocity[2]*2),
                              count=10,
                              scale=0.3+random.random()*1.1,
                              spread=0.1,
                              chunkType='sweat')
                              #emitType = 'stickers')
def __init__(self,color=(1,1,1),highlight=(0.5,0.5,0.5),character="Spaz",player=None,powerupsExpire=True):
        """
        Create a spaz for the provided bs.Player.
        Note: this does not wire up any controls;
        you must call connectControlsToPlayer() to do so.
        """
        # convert None to an empty player-ref
        if player is None: player = bs.Player(None)
        
        Spaz.__init__(self,color=color,highlight=highlight,character=character,sourcePlayer=player,startInvincible=True,powerupsExpire=powerupsExpire)
        self.lastPlayerAttackedBy = None # FIXME - should use empty player ref
        self.lastAttackedTime = 0
        self.lastAttackedType = None
        self.heldCount = 0
        self.lastPlayerHeldBy = None # FIXME - should use empty player ref here
        self._player = player
		
		
        
        
        profiles = []
        profiles = self._player.getInputDevice()._getPlayerProfiles()
        ###
        clID = self._player.getInputDevice().getClientID()
        cl_str = []
        for client in bsInternal._getGameRoster():
            if client['clientID'] == clID:
                cl_str = client['displayString']
                
            
        for spclient in bsInternal._getForegroundHostSession().players:
            spPlayerID = spclient.get_account_id()

        
        ##
        if profiles == [] or profiles == {}:
            profiles = bs.getConfig()['Player Profiles']

        for p in profiles:
            try:
                if cl_str in gph.vipHashes:
                    PermissionEffect(owner = self.node,prefix = '[PAID MEMBER]',prefixAnim = {0: (1,0,0), 250: (0,1,0),250*2:(0,0,1),250*3:(1,0,0)})
                    break
                if cl_str in gph.sneha:
                    PermissionEffect(owner = self.node,prefix = '[QUEEN]',prefixAnim = {0: (1,0,0), 250: (0,1,0),250*2:(0,0,1),250*3:(1,0,0)})
                    break 
                if cl_str in gph.ayush:
                    PermissionEffect(owner = self.node,prefix = '[KING]',prefixAnim = {0: (1,0,0), 250: (0,1,1),250*2:(1,0,1),250*3:(1,0,0)})
                    break     
                if cl_str in gph.adminHashes :
                    PermissionEffect(owner = self.node,prefix = '[OWNER]',prefixAnim = {0: (1,0,0), 250: (0,1,0),250*2:(0,0,1),250*3:(1,0,0)})
                    break
                if cl_str in gph.frndHashes :
                    PermissionEffect(owner = self.node,prefix = '[TEAM MEMBER]',prefixAnim = {0: (1,0,0), 250: (0,1,0),250*2:(0,0,1),250*3:(1,0,0)})
                    break    
                if spPlayerID in gph.autoKickList:
                    PermissionEffect(owner = self.node,prefix = '[LOOSER]',prefixAnim = {0: (1,0,0), 250: (0,1,0),250*2:(0,0,1),250*3:(1,0,0)})
                    break
                if cl_str in gph.royalpass:
                    PermissionEffect(owner = self.node,prefix = '[ROYAL PASS]',prefixAnim = {0: (1,0,0), 250: (0,1,0),250*2:(0,0,1),250*3:(1,0,0)})
                    break   
                    '''   
                else:
                    PermissionEffect(owner = self.node,prefix = '[ADMIN]',prefixAnim = {0: (1,0,0), 250: (0,1,0),250*2:(0,0,1),250*3:(1,0,0)})
                    break
                       '''
            except:
                pass

        # grab the node for this player and wire it to follow our spaz (so players' controllers know where to draw their guides, etc)
        if player.exists():
            playerNode = bs.getActivity()._getPlayerNode(player)
            self.node.connectAttr('torsoPosition',playerNode,'position')

    

bsSpaz.PlayerSpaz.__init__ = __init__




