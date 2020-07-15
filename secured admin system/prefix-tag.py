import bs
from bsSpaz import *
import bsSpaz
import bsUtils
import random
import bsInternal
import membersID as MID

class PermissionEffect(object):
    def __init__(self,position = (0,1,0),owner = None,prefix = 'ADMIN',prefixColor = (1,1,1),prefixAnim = {0:(1,1,1),500:(0.5,0.5,0.5)},prefixAnimate = True,particles = True):
        self.position = position
        self.owner = owner
        
         #  https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy

        
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
        #https://github.com/imayushsaini/Bombsquad-Mr.Smoothy-Admin-Powerup-Server
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
        cName=player.getName()
        

        clID = self._player.getInputDevice().getClientID()
        

          #  https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy
       
        #bsInternal._chatMessage(str(clID)+'clid')
        #bsInternal._chatMessage(str(self._player.get_account_id()))
        #bsInternal._chatMessage(str(self._player.getID()))
        cl_str = []
        

        if cName[0]==' ' or cName=='':
            bsInternal._disconnectClient(int(player.getInputDevice().getClientID()))
            bsInternal._chatMessage("No white Space Name Allowed")
            bsInternal._chatMessage("kicking"+cl_str)   

        playeraccountid=self._player.get_account_id()
     
        
        ##
        if profiles == [] or profiles == {}:
            profiles = bs.getConfig()['Player Profiles']

        for p in profiles:
            try:
                if playeraccountid in MID.admins:
                    PermissionEffect(owner = self.node,prefix = u'\ue048 A.D.M.I.N \ue048',prefixAnim = {0: (0.5,0.011,0.605), 250: (1,0.411,0.3411),250*2:(1,0.591,0.811),250*3:(0.829,0.331,0.403)})
                    break
                if playeraccountid in MID.vips:
                    PermissionEffect(owner = self.node,prefix = u'\ue043 VIP \ue043',prefixAnim = {0: (0.9,0.611,0.705), 250: (1,0.311,0.5411),250*2:(0.7,0.591,0.811),250*3:(0.729,0.431,0.703)})
                    break
                
                if playeraccountid in MID.members:
                    PermissionEffect(owner = self.node,prefix = u" MEMBER ",prefixAnim = {0: (0.85,0.852,0.85), 250: (0.59,0.598,0),250*2:(0.75,1,0),250*3:(0.9,0.17,0.028)})
                    break      
                
                 
            except:
                pass

        # grab the node for this player and wire it to follow our spaz (so players' controllers know where to draw their guides, etc)
        if player.exists():
            playerNode = bs.getActivity()._getPlayerNode(player)
            self.node.connectAttr('torsoPosition',playerNode,'position')

    

bsSpaz.PlayerSpaz.__init__ = __init__




