# -*- coding: utf-8 -*-
#https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy
import bs
import bsInternal
import bsPowerup
import bsUtils
import random
import membersID as MID
import BuddyBunny
import os
import threading
import json




class cheatOptions(object):
    def __init__(self):
        self.all = True # just in case
       
        
        self.tint = None # needs for /nv
    
    def checkOwner(self,clientID): 
       
        client='kuchbhi'
        
        for i in bsInternal._getForegroundHostActivity().players:
            
            if i.getInputDevice().getClientID()==clientID:
                client=i.get_account_id()
        
        if client in MID.owners or MID.allAdmins: 
            bs.screenMessage('cheat activated',color=(0,1,0), clients=[clientID], transient=True)
            return True
            
        else:
            bs.screenMessage('access denied',color=(1,0,0), clients=[clientID], transient=True)

    def checkAdmin(self,clientID): 
       
        client='kuchbhi'
        
        for i in bsInternal._getForegroundHostActivity().players:
            
            if i.getInputDevice().getClientID()==clientID:
                client=i.get_account_id()
        
        if client in MID.admins or MID.allAdmins: 
            bs.screenMessage('cheat activated',color=(0,1,0), clients=[clientID], transient=True)
            return True
            
        else:
            bs.screenMessage('access denied',color=(1,0,0), clients=[clientID], transient=True)
        

    def checkMember(self,clientID): 
       client='kuchbhi'
        
       for i in bsInternal._getForegroundHostActivity().players:
            
            if i.getInputDevice().getClientID()==clientID:
                client=i.get_account_id()
        
       if client in MID.admins or client in MID.members  or  client in MID.owners or MID.allAdmins:   #member,vip,admin will have access
            bs.screenMessage('cheat activated',color=(0,1,0), clients=[clientID], transient=True)
            return True
           
       else:
            bs.screenMessage('access denied',color=(1,0,0), clients=[clientID], transient=True)

      
    def checkVip(self,clientID):
        client='kuchbhi'
        
        for i in bsInternal._getForegroundHostActivity().players:
            
            if i.getInputDevice().getClientID()==clientID:
                client=i.get_account_id()
        
        if client in MID.admins or client in MID.vips or  client in MID.owners or MID.allAdmins:         #only admin and vip can access
            bs.screenMessage('cheat activated',color=(0,1,0), clients=[clientID], transient=True)
            return True
            
        else:
            bs.screenMessage('access denied',color=(1,0,0), clients=[clientID], transient=True)

    def kickByNick(self,nick):
        roster = bsInternal._getGameRoster()
        for i in roster:
            try:
                if i['players'][0]['nameFull'].lower().find(nick.encode('utf-8').lower()) != -1:
                    bsInternal._disconnectClient(int(i['clientID']))
            except:
                pass
      #  https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy
    def opt(self,clientID,msg):
        nick=clientID
        if True:
            m = msg.split(' ')[0] # command
            a = msg.split(' ')[1:] # arguments
            
            activity = bsInternal._getForegroundHostActivity()
            with bs.Context(activity):
                if m == '/kick':
                    if self.checkAdmin(clientID):
                        if a == []:
                            bs.screenMessage('kick using name of clientID',color=(0,1,0), clients=[clientID], transient=True)
                        else:
                            if len(a[0]) > 3:
                                if(self.checkOwner(nick)!=True):
                                    
                                    self.kickByNick(a[0])
                                else:
                                    bs.screenMessage('cant kick owner',color=(1,0,0), clients=[clientID], transient=True)   
                            else:
                                try:
                                    

                                    s = int(a[0])
                                    for cl in bsInternal._getForegroundHostSession().players:
                                        if(cl.getInputDevice().getClientID()==s):
                                            accountid=cl.get_account_id()
  #defend your self from dhokebaaz admins......  
                                    if accountid in MID.owners:
                                        bs.screenMessage('cant kick owner',color=(1,0,0), clients=[clientID], transient=True)
                                    else:    
                                        
                                        bsInternal._disconnectClient(int(a[0]))
                                except:
                                    self.kickByNick(a[0])
                   
                elif m == '/getlost':
                    if self.checkAdmin(nick):
                        if a == []:
                            bsInternal._chatMessage('Using: /kick name or number of list')
                        else:
                            if len(a[0]) > 3:
                                self.kickByNick(a[0])
                            else:
                                try:
                                    s = int(a[0])
                                    bsInternal._disconnectClient(int(a[0]))
                                except:
                                    self.kickByNick(a[0])
                elif m == '/list':     #need to add some delay , else you will only last players id ...   do it yourself , as i dont use much list command
                    if self.checkMember(nick):
                        bs.screenMessage('========For kick=======',color=(1,0,0), clients=[clientID], transient=True)
                        for i in bsInternal._getGameRoster():
                            try:
                                bs.screenMessage(i['players'][0]['nameFull'].encode('utf-8') + "     (/kick " + str(i['clientID'])+")",color=(1,0.4,0), clients=[clientID], transient=True)
                                
                            except:
                                pass
                        bs.screenMessage('=================',color=(1,0,0), clients=[clientID], transient=True)
                        bs.screenMessage('========For Other Commands=======',color=(1,0.6,0.4), clients=[clientID], transient=True)
                        for s in bsInternal._getForegroundHostSession().players:
                            bs.screenMessage(s.getName() + "     "+ str(bsInternal._getForegroundHostSession().players.index(s)),color=(0.5,0.7,0.3), clients=[clientID], transient=True)
                elif m == '/ooh':
                    if a is not None and len(a) > 0:
                        s = int(a[0])
                        def oohRecurce(c):
                            bs.playSound(bs.getSound('ooh'),volume = 2)
                            c -= 1
                            if c > 0:
                                bs.gameTimer(int(a[1]) if len(a) > 1 and a[1] is not None else 1000,bs.Call(oohRecurce,c=c))
                        oohRecurce(c=s)
                    else:
                        bs.playSound(bs.getSound('ooh'),volume = 2)

                elif m=='/me':
                    if a==[]
                        playeraccountid=''   #  https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy
                        playername=''
                        for i in bsInternal._getForegroundHostActivity().players:
                
                            if i.getInputDevice().getClientID()==clientID:
                                
                                playeraccountid=i.get_account_id()
                                playername=i.getName()
                    else:
                        playeraccountid=''   #  https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy
                        playername=''
                        for i in bsInternal._getForegroundHostActivity().players:
                
                            if i.getInputDevice().getClientID()==int(a[0]):
                                
                                playeraccountid=i.get_account_id()
                                playername=i.getName()
                    if os.path.exists('stats.json'):
                        while True:
                            try:
                                with open('stats.json') as f:
                                    stats = json.loads(f.read())
                                    break
                            except Exception as (e):
                                print e
                                time.sleep(0.05)
                    else:
                        stats = {}
                    if playeraccountid not in stats:
                        bs.screenMessage('Not played any match yet',color=(0,1,1),transient=True)
                    else:    
                        killed=stats[playeraccountid]['killed']
                        kills=stats[playeraccountid]['kills']
                        
                        bs.screenMessage(playername+':'+' Kills:'+str(kills)+', Killed:'+str(killed)+', Matches:'+str(stats[playeraccountid]['played']),color=(0,1,1),transient=True)
                

                elif m == '/admin':
                    if self.checkOwner(nick):
                        clID = int(a[0])
                        updated_admins=[]
                        updated_admins=MID.admins
                        for client in bsInternal._getGameRoster():
                            if client['clientID']==clID:
                                cl_str = client['displayString']

                        for i in bsInternal._getForegroundHostActivity().players:
            
                            if i.getInputDevice().getClientID()==clID:
                                newadmin=i.get_account_id()       
                                if a[1] == 'add':
                                    
                                    updated_admins.append(newadmin)
                                    with open(bs.getEnvironment()['systemScriptsDirectory'] + "/membersidlogged.txt",mode='a') as fi:
                                        fi.write(cl_str +' || '+newadmin +'\n')
                                        fi.close()
                                elif a[1] == 'remove':
                                   
                                    if newadmin in MID.admins:
                                        updated_admins.remove(newadmin)

                        if True:

                            with open(bs.getEnvironment()['systemScriptsDirectory'] + "/membersID.py") as file:
                                s = [row for row in file]
                               
                                s[1] = 'admins = '+ str(updated_admins)+ '\n'
                                f = open(bs.getEnvironment()['systemScriptsDirectory'] + "/membersID.py",'w')
                                for i in s:
                                    f.write(i)
                                f.close()
                                reload(MID)
                        else:
                            pass  #  https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy

                elif m == '/vip':
                    if self.checkAdmin(nick):
                        clID = int(a[0])
                        updated_admins=[]
                        updated_admins=MID.vips
                        for client in bsInternal._getGameRoster():
                            if client['clientID']==clID:
                                cl_str = client['displayString']

                        for i in bsInternal._getForegroundHostActivity().players:
            
                            if i.getInputDevice().getClientID()==clID:
                                newadmin=i.get_account_id()       
                                if a[1] == 'add':
                                    
                                    updated_admins.append(newadmin)
                                    with open(bs.getEnvironment()['systemScriptsDirectory'] + "/membersidlogged.txt",mode='a') as fi:
                                        fi.write(cl_str +' || '+newadmin+'\n')
                                        fi.close()
                                elif a[1] == 'remove':
                                   
                                    if newadmin in MID.vips:
                                        updated_admins.remove(newadmin)

                        if True:

                            with open(bs.getEnvironment()['systemScriptsDirectory'] + "/membersID.py") as file:
                                s = [row for row in file]
                               
                                s[2] = 'vips = '+ str(updated_admins)+ '\n'
                                f = open(bs.getEnvironment()['systemScriptsDirectory'] + "/membersID.py",'w')
                                for i in s:
                                    f.write(i)
                                f.close()
                                reload(MID)
                        else:
                            pass

                elif m == '/member':
                    if self.checkOwner(nick):
                        clID = int(a[0])
                        updated_admins=[]
                        updated_admins=MID.members
                        for client in bsInternal._getGameRoster():
                            if client['clientID']==clID:
                                cl_str = client['displayString']

                        for i in bsInternal._getForegroundHostActivity().players:
            
                            if i.getInputDevice().getClientID()==clID:
                                newadmin=i.get_account_id()       
                                if a[1] == 'add':
                                    
                                    updated_admins.append(newadmin)
                                    with open(bs.getEnvironment()['systemScriptsDirectory'] + "/membersidlogged.txt",mode='a') as fi:
                                        fi.write(cl_str +' || '+newadmin+'\n')
                                        fi.close()
                                elif a[1] == 'remove':
                                   
                                    if newadmin in MID.members:
                                        updated_admins.remove(newadmin)

                        if True:

                            with open(bs.getEnvironment()['systemScriptsDirectory'] + "/membersID.py") as file:
                                s = [row for row in file]
                               
                                s[3] = 'members = '+ str(updated_admins)+ '\n'
                                f = open(bs.getEnvironment()['systemScriptsDirectory'] + "/membersID.py",'w')
                                for i in s:
                                    f.write(i)
                                f.close()
                                reload(MID)
                        else:
                            pass 
                elif m == '/playSound':
                    if a is not None and len(a) > 1:
                        s = int(a[1])
                        def oohRecurce(c):
                            bs.playSound(bs.getSound(str(a[0])),volume = 2)
                            c -= 1
                            if c > 0:
                                bs.gameTimer(int(a[2]) if len(a) > 2 and a[2] is not None else 1000,bs.Call(oohRecurce,c=c))
                        oohRecurce(c=s)
                    else:
                        bs.playSound(bs.getSound(str(a[0])),volume = 2)
                elif m == '/quit':
                    if self.checkOwner(nick):
                        bsInternal.quit()
                elif m == '/nv':
                    if self.tint is None:
                        self.tint = bs.getSharedObject('globals').tint
                    bs.getSharedObject('globals').tint = (0.5,0.7,1) if a == [] or not a[0] == u'off' else self.tint
                elif m == '/freeze':
                    if self.checkMember(nick):
                        if a == []:
                            
                            bs.screenMessage('Using: /freeze all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                        else:
                            if a[0] == 'all':
                                if self.checkVip(nick):
                            
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.handleMessage(bs.FreezeMessage())
                                        except:
                                            pass
                            else:
                                bs.getSession().players[int(a[0])].actor.node.handleMessage(bs.FreezeMessage())
                elif m == '/thaw':
                    if a == []:
                        
                        bs.screenMessage('Using: /thaw all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                    else:
                        if a[0] == 'all':
                            for i in bs.getSession().players:
                                try:
                                    i.actor.node.handleMessage(bs.ThawMessage())
                                except:
                                    pass
                        else:
                            bs.getSession().players[int(a[0])].actor.node.handleMessage(bs.ThawMessage())




               
                
                elif m == '/kill':
                    if self.checkVip(nick):
                        if a == []:
                            
                               
                                bs.screenMessage('Using: /kill all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                        else:
                            
                            if a[0] == 'all':
                                if self.checkAdmin(nick):
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.handleMessage(bs.DieMessage())
                                        except:
                                            pass
                            else:
                                bs.getSession().players[int(a[0])].actor.node.handleMessage(bs.DieMessage())                
                elif m == '/curse':
                    if self.checkMember(nick):
                        if a == []:
                            
                            bs.screenMessage('Using: /curse all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                        else:
                            if a[0] == 'all':
                                if self.checkAdmin(nick):
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.curse()
                                        except:
                                            pass
                                else:
                                    bs.getSession().players[int(a[0])].actor.curse()
                elif m == '/box':
                    if a == []:
                        
                        bs.screenMessage('Using: /box all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                    else:
                        try:
                            if a[0] == 'all':
                                if self.checkAdmin(nick):
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.torsoModel = bs.getModel("tnt")
                                        except:
                                            pass
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.colorMaskTexture= bs.getTexture("tnt")
                                        except:
                                            pass
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.colorTexture= bs.getTexture("tnt")
                                        except:
                                            pass
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.highlight = (1,1,1)
                                        except:
                                            pass
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.color = (1,1,1)
                                        except:
                                            pass
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.headModel = None
                                        except:
                                            pass
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.style = "cyborg"
                                        except:
                                            pass
                            else:
                                n = int(a[0])
                                bs.getSession().players[n].actor.node.torsoModel = bs.getModel("tnt"); 
                                bs.getSession().players[n].actor.node.colorMaskTexture= bs.getTexture("tnt"); 
                                bs.getSession().players[n].actor.node.colorTexture= bs.getTexture("tnt") 
                                bs.getSession().players[n].actor.node.highlight = (1,1,1); 
                                bs.getSession().players[n].actor.node.color = (1,1,1); 
                                bs.getSession().players[n].actor.node.headModel = None; 
                                bs.getSession().players[n].actor.node.style = "cyborg";
                        except:
                           pass
                          
                
                elif m == '/mine':
                    if a == []:
                        
                        bs.screenMessage('Using: /mine all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                    else:
                        try:
                            if a[0] == 'all':
                                if self.checkAdmin(nick):
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.torsoModel = bs.getModel("landMine")
                                        except Exception:
                                            pass
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.colorMaskTexture= bs.getTexture("landMine")
                                        except Exception:
                                            pass
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.colorTexture= bs.getTexture("landMine")
                                        except Exception:
                                            pass
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.highlight = (1,1,1)
                                        except Exception:
                                            pass
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.color = (1,1,1)
                                        except Exception:
                                            pass
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.headModel = None
                                        except Exception:
                                            pass 
                                    for i in bs.getSession().players:
                                        try:
                                            i.actor.node.style = "cyborg"
                                        except Exception:
                                            pass 
                            else:
                                n = int(a[0])
                                bs.getSession().players[n].actor.node.torsoModel = bs.getModel("landMine"); 
                                bs.getSession().players[n].actor.node.colorMaskTexture= bs.getTexture("landMine"); 
                                bs.getSession().players[n].actor.node.colorTexture= bs.getTexture("landMine") 
                                bs.getSession().players[n].actor.node.highlight = (1,1,1); 
                                bs.getSession().players[n].actor.node.color = (1,1,1); 
                                bs.getSession().players[n].actor.node.headModel = None; 
                                bs.getSession().players[n].actor.node.style = "cyborg";
                        except:
                           pass           

                elif m == '/headless':   #  https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy
                    if a == []:
                        
                        bs.screenMessage('Using: /headless all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                    else:
                        if a[0]=='all':
                            for i in bs.getActivity().players:
                                try:
                                    if i.actor.exists():
                                       i.actor.node.headModel = None
                                       i.actor.node.style = "cyborg"
                                except Exception:
                                    pass
                                

                        elif len(a[0]) > 2:
                           for i in bs.getActivity().players:
                               try:
                                   if (i.getName()).encode('utf-8') == (a[0]):
                                      if i.actor.exists():
                                         i.actor.node.headModel = None
                                         i.actor.node.style = "cyborg"
                               except Exception:
                                   pass
                           bsInternal._chatMessage(bs.getSpecialChar('logoFlat'))

                        else:
                             try:
                                 bs.getActivity().players[int(a[0])].actor.node.headModel = None
                                 bs.getActivity().players[int(a[0])].actor.node.style = "cyborg"
                                 bsInternal._chatMessage(bs.getSpecialChar('logoFlat'))
                             except Exception:
                                bsInternal._chatMessage('PLAYER NOT FOUND')     
                elif m == '/shield': #shield
                    if self.checkAdmin(nick):
                        if a == []:
                            
                            bs.screenMessage('Using: /shield all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                        else:
                            if a[0]=='all':
                                for i in bs.getActivity().players:
                                    try:
                                        if i.actor.exists():
                                           i.actor.node.handleMessage(bs.PowerupMessage(powerupType = 'shield'))
                                           bsInternal._chatMessage('shield will give you Protection')
                                    except Exception:
                                        pass
                            if len(a[0]) > 2:
                               for i in bs.getActivity().players:
                                   try:
                                       if (i.getName()).encode('utf-8') == (a[0]):
                                          if i.actor.exists():
                                             i.actor.node.handleMessage(bs.PowerupMessage(powerupType = 'shield'))
                                             bsInternal._chatMessage('shield will give you Protection')
                                   except Exception:
                                       pass
                               bsInternal._chatMessage(bs.getSpecialChar('logoFlat'))
                            else:
                                 try:
                                     bs.getActivity().players[int(a[0])].actor.node.handleMessage(bs.PowerupMessage(powerupType = 'shield'))
                                     bsInternal._chatMessage('shield will give you Protection')
                                     bsInternal._chatMessage(bs.getSpecialChar('logoFlat'))
                                 except Exception:
                                     bsInternal._chatMessage('PLAYER NOT FOUND')
                                 
                elif m == '/celebrate': #celebrate him
                    if a == []:
                       
                        bs.screenMessage('Using: /celebrate all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                    else:
                        if a[0]=='all':
                            for i in bs.getActivity().players:
                                try:
                                    if i.actor.exists():
                                       i.actor.node.handleMessage('celebrate', 30000)
                                except Exception:
                                    pass

                        elif len(a[0]) > 2:
                           for i in bs.getActivity().players:
                               try:
                                   if (i.getName()).encode('utf-8') == (a[0]):
                                      if i.actor.exists():
                                         i.actor.node.handleMessage('celebrate', 30000)
                               except Exception:
                                   pass
                                   
                        else:
                             try:
                                 bs.getActivity().players[int(a[0])].actor.node.handleMessage('celebrate', 30000)
                                 bsInternal._chatMessage(bs.getSpecialChar('logoFlat'))
                             except Exception:
                                bsInternal._chatMessage('PLAYER NOT FOUND')                      
                elif m == '/remove':
                    if self.checkAdmin(nick):
                        if a == []:
                            
                            bs.screenMessage('Using: /remove all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                        else:
                            if a[0] == 'all':
                                for i in bs.getSession().players:
                                    try:
                                        i.removeFromGame()
                                    except:
                                        pass
                            else:
                                bs.getSession().players[int(a[0])].removeFromGame()
                    else:
                        bsInternal._chatMessage('You cant remove any one')   
                elif m == '/end':
                    if self.checkAdmin(nick):
                        try:
                            bsInternal._getForegroundHostActivity().endGame()
                        except:
                            pass  #  https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy
                elif m == '/hug':
                    if a == []:
                        
                        bs.screenMessage('Using: /hug all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                    else:
                        try:
                            if a[0] == 'all':
                                if self.checkAdmin(nick):
                                    try:
                                        bsInternal._getForegroundHostActivity().players[0].actor.node.holdNode = bsInternal._getForegroundHostActivity().players[1].actor.node
                                    except:
                                        pass
                                    try:
                                        bsInternal._getForegroundHostActivity().players[1].actor.node.holdNode = bsInternal._getForegroundHostActivity().players[0].actor.node
                                    except:
                                        pass
                                    try:
                                        bsInternal._getForegroundHostActivity().players[3].actor.node.holdNode = bsInternal._getForegroundHostActivity().players[2].actor.node
                                    except:
                                        pass
                                    try:
                                        bsInternal._getForegroundHostActivity().players[4].actor.node.holdNode = bsInternal._getForegroundHostActivity().players[3].actor.node
                                    except:
                                        pass
                                    try:
                                        bsInternal._getForegroundHostActivity().players[5].actor.node.holdNode = bsInternal._getForegroundHostActivity().players[6].actor.node
                                    except:
                                        pass
                                    try:
                                        bsInternal._getForegroundHostActivity().players[6].actor.node.holdNode = bsInternal._getForegroundHostActivity().players[7].actor.node
                                    except:
                                        pass
                            else:
                                bsInternal._getForegroundHostActivity().players[int(a[0])].actor.node.holdNode = bsInternal._getForegroundHostActivity().players[int(a[1])].actor.node
                        except:
                            pass
                elif m == '/gm':
                    if self.checkAdmin(nick):
                        if a == []:
                            for i in range(len(activity.players)):   #removed punch and shield ...no need as you are already invicible
                                if activity.players[i].getName().encode('utf-8').find(nick.encode('utf-8').replace('...','').replace(':','')) != -1:
                                    activity.players[i].actor.node.hockey = activity.players[i].actor.node.hockey == False
                                    activity.players[i].actor.node.invincible = activity.players[i].actor.node.invincible == False
                                    activity.players[i].actor._punchPowerScale = 5 if activity.players[i].actor._punchPowerScale == 1.2 else 1.2
                        else:
                            activity.players[int(a[0])].actor.node.hockey = activity.players[int(a[0])].actor.node.hockey == False
                            activity.players[int(a[0])].actor.node.invincible = activity.players[int(a[0])].actor.node.invincible == False
                            activity.players[int(a[0])].actor._punchPowerScale = 5 if activity.players[int(a[0])].actor._punchPowerScale == 1.2 else 1.2

                elif m == '/tint':
                    if self.checkAdmin(nick):
                        if a == []:
                            bsInternal._chatMessage('Using: /tint R G B')
                            bsInternal._chatMessage('OR')
                            bsInternal._chatMessage('Using: /tint r bright speed')
                        else:
                            if a[0] == 'r':
                                m = 1.3 if a[1] is None else float(a[1])
                                s = 1000 if a[2] is None else float(a[2])
                                bsUtils.animateArray(bs.getSharedObject('globals'), 'tint',3, {0: (1*m,0,0), s: (0,1*m,0),s*2:(0,0,1*m),s*3:(1*m,0,0)},True)
                            else:
                                try:
                                    if a[1] is not None:
                                        bs.getSharedObject('globals').tint = (float(a[0]),float(a[1]),float(a[2]))
                                    else:
                                        bs.screenMessage('Error!',color = (1,0,0))
                                except:
                                    bs.screenMessage('Error!',color = (1,0,0))
                    
                elif m == '/sm':
                    if self.checkAdmin(nick):
                        bs.getSharedObject('globals').slowMotion = bs.getSharedObject('globals').slowMotion == False
                       
                


                elif m == '/spaz':
                    if a == []:
                        
                        bs.screenMessage('Using: /spaz all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                    else:
                        try:
                            if a[0] == 'all': #mr.smoothy
                                if self.checkAdmin(nick):
                                    if a[1] in ['ali','agent','bunny','cyborg','pixie','robot','alien','witch','wizard','bones','zoe']:
                                        for i in bs.getSession().players:
                                            t = i.actor.node
                                            try:
                                               
                                                t.colorTexture = bs.getTexture(a[1]+"Color")
                                                t.colorMaskTexture = bs.getTexture(a[1]+"ColorMask")
                                                
                                                t.headModel =     bs.getModel(a[1]+"Head")
                                                t.torsoModel =    bs.getModel(a[1]+"Torso")
                                                t.pelvisModel =   bs.getModel(a[1]+"Pelvis")
                                                t.upperArmModel = bs.getModel(a[1]+"UpperArm")
                                                t.foreArmModel =  bs.getModel(a[1]+"ForeArm")
                                                t.handModel =     bs.getModel(a[1]+"Hand")
                                                t.upperLegModel = bs.getModel(a[1]+"UpperLeg")
                                                t.lowerLegModel = bs.getModel(a[1]+"LowerLeg")
                                                t.toesModel =     bs.getModel(a[1]+"Toes")
                                                t.style = a[1]
                                            except:
                                                pass

                                    else:
                                        bsInternal._chatMessage('use ali,agent,bunny,cyborg,pixie,robot')
                                        bsInternal._chatMessage('alien,witch,wizard,bones,zoe')
                            else:
                                if a[1] in ['ali','agent','bunny','cyborg','pixie','robot','alien','witch','wizard','bones','santa','zoe']:
                                    n = int(a[0])
                                    t = bs.getSession().players[n].actor.node
                                    t.colorTexture = bs.getTexture(a[1]+"Color")
                                    t.colorMaskTexture = bs.getTexture(a[1]+"ColorMask")
                                            
                                    t.headModel =     bs.getModel(a[1]+"Head")
                                    t.torsoModel =    bs.getModel(a[1]+"Torso")
                                    t.pelvisModel =   bs.getModel(a[1]+"Pelvis")
                                    t.upperArmModel = bs.getModel(a[1]+"UpperArm")
                                    t.foreArmModel =  bs.getModel(a[1]+"ForeArm")
                                    t.handModel =     bs.getModel(a[1]+"Hand")
                                    t.upperLegModel = bs.getModel(a[1]+"UpperLeg")
                                    t.lowerLegModel = bs.getModel(a[1]+"LowerLeg")
                                    t.toesModel =     bs.getModel(a[1]+"Toes")
                                    t.style = a[1]
                        except:
                           pass

                elif m == '/inv':
                    if a == []:
                        
                        bs.screenMessage('Using: /inv all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                    else:
                        try:
                            if a[0] == 'all':
                                if self.checkAdmin(nick):
                                    for i in bs.getSession().players:
                                        t = i.actor.node
                                        try:
                                           
                                              #  https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy
                                            t.headModel =     None
                                            t.torsoModel =    None
                                            t.pelvisModel =   None
                                            t.upperArmModel = None
                                            t.foreArmModel =  None
                                            t.handModel =     None
                                            t.upperLegModel = None
                                            t.lowerLegModel = None
                                            t.toesModel =     None
                                            t.style = "cyborg"
                                        except:
                                            pass
                            else:
                                n = int(a[0])
                                t = bs.getSession().players[n].actor.node
                                                                        
                                t.headModel =     None
                                t.torsoModel =    None
                                t.pelvisModel =   None
                                t.upperArmModel = None
                                t.foreArmModel =  None
                                t.handModel =     None
                                t.upperLegModel = None
                                t.lowerLegModel = None
                                t.toesModel =     None
                                t.style = "cyborg"
                        except:
                           pass
                elif m == '/cameraMode':
                    if self.checkAdmin(nick):
                        try:
                            if bs.getSharedObject('globals').cameraMode == 'follow':
                                bs.getSharedObject('globals').cameraMode = 'rotate'
                            else:
                                bs.getSharedObject('globals').cameraMode = 'follow'
                        except:
                            pass
              
                elif m == '/lm444':   
                    arr = []
                    for i in range(100):
                        try:
                            arr.append(bsInternal._getChatMessages()[-1-i])
                        except:
                            pass
                    arr.reverse()
                    for i in arr:
                        bsInternal._chatMessage(i)
                elif m == '/id':
                    if self.checkAdmin(nick):
                        if a == []:
                            bsInternal._chatMessage('Using: /gp number of list')
                        else:
                            s = bsInternal._getForegroundHostSession()
                            for i in s.players[int(a[0])].getInputDevice()._getPlayerProfiles():
                                try:
                                    bsInternal._chatMessage(i)
                                except:
                                    pass
                elif m == '/icy':
                    if self.checkAdmin(nick):
                        bsInternal._getForegroundHostActivity().players[int(a[0])].actor.node = bsInternal._getForegroundHostActivity().players[int(a[1])].actor.node
                elif m == '/fly':
                    if True:
                        if a == []:
                            bsInternal._chatMessage('Using: /fly all or number of list')
                            
                        else:
                            if self.checkAdmin(nick):
                                if a[0] == 'all':
                                    for i in bsInternal._getForegroundHostActivity().players:
                                        i.actor.node.fly = True
                                else:
                                    bsInternal._getForegroundHostActivity().players[int(a[0])].actor.node.fly = bsInternal._getForegroundHostActivity().players[int(a[0])].actor.node.fly == False
                elif m == '/floorReflection':
                    if self.checkAdmin(nick):
                        bs.getSharedObject('globals').floorReflection = bs.getSharedObject('globals').floorReflection == False
                elif m == '/ac':
                    if self.checkAdmin(nick):
                        if a == []:
                            bsInternal._chatMessage('Using: /ac R G B')
                            bsInternal._chatMessage('OR')
                            bsInternal._chatMessage('Using: /ac r bright speed')
                        else:
                            if a[0] == 'r':
                                m = 1.3 if a[1] is None else float(a[1])
                                s = 1000 if a[2] is None else float(a[2])
                                bsUtils.animateArray(bs.getSharedObject('globals'), 'ambientColor',3, {0: (1*m,0,0), s: (0,1*m,0),s*2:(0,0,1*m),s*3:(1*m,0,0)},True)
                            else:
                                try:
                                    if a[1] is not None:
                                        bs.getSharedObject('globals').ambientColor = (float(a[0]),float(a[1]),float(a[2]))
                                    else:
                                        bs.screenMessage('Error!',color = (1,0,0))
                                except:
                                    bs.screenMessage('Error!',color = (1,0,0))
                elif m == '/iceOff':
                    try:
                        activity.getMap().node.materials = [bs.getSharedObject('footingMaterial')]
                        activity.getMap().isHockey = False
                    except:
                        pass
                    try:
                        activity.getMap().floor.materials = [bs.getSharedObject('footingMaterial')]
                        activity.getMap().isHockey = False
                    except:
                        pass
                    for i in activity.players:
                        i.actor.node.hockey = False
                elif m == '/maxPlayers':
                    if self.checkAdmin(nick):
                        if a == []:
                            bsInternal._chatMessage('Using: /maxPlayers count of players')
                        else:
                            try:
                                bsInternal._getForegroundHostSession()._maxPlayers = int(a[0])
                                bsInternal._setPublicPartyMaxSize(int(a[0]))
                                bsInternal._chatMessage('Players limit set to '+str(int(a[0])))
                            except:
                                bs.screenMessage('Error!',color = (1,0,0))
                            '''
                elif m == '/heal':
                    if a == []:
                        bsInternal._chatMessage('Using: /heal all or number of list')
                    else:
                        try:
                            bsInternal._getForegroundHostActivity().players[int(a[0])].actor.node.handleMessage(bs.PowerupMessage(powerupType = 'health'))
                        except:
                            pass      original heal command new one modified by mr.smoothy

                        '''
                elif m == '/heal': #shield
                    if a == []:
                        
                        bs.screenMessage('Using: /heal all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                    else:
                        if a[0]=='all':
                            if self.checkAdmin(nick):
                                for i in bs.getActivity().players:
                                    try:
                                        if i.actor.exists():
                                           i.actor.node.handleMessage(bs.PowerupMessage(powerupType = 'health'))
                                          
                                    except Exception:
                                        pass
                        if len(a[0]) > 2:
                           for i in bs.getActivity().players:
                               try:
                                   if (i.getName()).encode('utf-8') == (a[0]):
                                      if i.actor.exists():
                                         i.actor.node.handleMessage(bs.PowerupMessage(powerupType = 'health'))
                                         
                               except Exception:
                                   pass
                           bsInternal._chatMessage(bs.getSpecialChar('logoFlat'))
                        else:
                             try:
                                 bs.getActivity().players[int(a[0])].actor.node.handleMessage(bs.PowerupMessage(powerupType = 'health'))
                                 
                                 bsInternal._chatMessage(bs.getSpecialChar('logoFlat'))
                             except Exception:
                                 bsInternal._chatMessage('PLAYER NOT FOUND')       

                elif m == '/punch': #shield
                    if self.checkAdmin(nick):
                        if a == []:
                            for i in range(len(activity.players)):
                                bs.getActivity().players[i].actor.node.handleMessage(bs.PowerupMessage(powerupType = 'punch'))
                               
                            bsInternal._chatMessage('MUST USE PLAYER ID OR NICK')
                        else:
                            if a[0]=='all':
                                for i in bs.getActivity().players:
                                    try:
                                        if i.actor.exists():
                                           i.actor.node.handleMessage(bs.PowerupMessage(powerupType = 'punch'))
                                          
                                    except Exception:
                                        pass
                            if len(a[0]) > 2:
                               for i in bs.getActivity().players:
                                   try:
                                       if (i.getName()).encode('utf-8') == (a[0]):
                                          if i.actor.exists():
                                             i.actor.node.handleMessage(bs.PowerupMessage(powerupType = 'punch'))
                                             
                                   except Exception:
                                       pass
                               bsInternal._chatMessage(bs.getSpecialChar('logoFlat'))
                            else:
                                 try:
                                     bs.getActivity().players[int(a[0])].actor.node.handleMessage(bs.PowerupMessage(powerupType = 'punch'))
                                    
                                     bsInternal._chatMessage(bs.getSpecialChar('logoFlat'))
                                 except Exception:
                                     bsInternal._chatMessage('PLAYER NOT FOUND')
                
                elif m == '/gift': #random powerup
                    if self.checkAdmin(nick):
                        powerss=['shield','punch','curse','health']
                        if True:
                            if True:
                                for i in bs.getActivity().players:
                                    try:
                                        if i.actor.exists():
                                           i.actor.node.handleMessage(bs.PowerupMessage(powerupType = powerss[random.randrange(0,4)]))
                                           
                                    except Exception:
                                        pass
                                     
                elif m == '/reset':
                    type='soft'
                    rs=0
                    try:
                        bsInternal._getForegroundHostActivity().getMap().node.reflection = type
                        bsInternal._getForegroundHostActivity().getMap().node.reflectionScale = rs
                    except:
                        pass
                    try:
                        bsInternal._getForegroundHostActivity().getMap().bg.reflection = type
                        bsInternal._getForegroundHostActivity().getMap().bg.reflectionScale = rs
                    except:
                        pass
                    try:
                        bsInternal._getForegroundHostActivity().getMap().floor.reflection = type
                        bsInternal._getForegroundHostActivity().getMap().floor.reflectionScale = rs
                    except:
                        pass
                    try:
                        bsInternal._getForegroundHostActivity().getMap().center.reflection = type
                        bsInternal._getForegroundHostActivity().getMap().center.reflectionScale = rs
                    except:
                        pass
                    bs.getSharedObject('globals').ambientColor = (0,0,0)
                    bs.getSharedObject('globals').tint = (1,1,1)

                elif m== '/disco':  #naacho benchod
                    times=[0]
                    def discoRed():
                        bs.getSharedObject('globals').tint = (1,.6,.6)
                        bs.gameTimer(230,bs.Call(discoBlue))
                    def discoBlue():
                        bs.getSharedObject('globals').tint = (.6,1,.6)
                        bs.gameTimer(230,bs.Call(discoGreen))
                    def discoGreen():
                        
                        bs.getSharedObject('globals').tint = (.6,.6,1)
                        if times[0]<10:
                            times[0]+=1

                            bs.gameTimer(230,bs.Call(discoRed))
                        else:
                            bs.getSharedObject('globals').tint = (1,1,1)
                    bs.gameTimer(300,bs.Call(discoRed))   

        
                elif m == '/reflections':
                    if self.checkAdmin(nick):
                        if a == [] or len(a) < 2:
                            bsInternal._chatMessage('Using: /reflections type(1/0) scale')
                        rs = [int(a[1])]
                        type = 'soft' if int(a[0]) == 0 else 'powerup'
                        try:
                            bsInternal._getForegroundHostActivity().getMap().node.reflection = type
                            bsInternal._getForegroundHostActivity().getMap().node.reflectionScale = rs
                        except:
                            pass
                        try:
                            bsInternal._getForegroundHostActivity().getMap().bg.reflection = type
                            bsInternal._getForegroundHostActivity().getMap().bg.reflectionScale = rs
                        except:
                            pass
                        try:
                            bsInternal._getForegroundHostActivity().getMap().floor.reflection = type
                            bsInternal._getForegroundHostActivity().getMap().floor.reflectionScale = rs
                        except:
                            pass
                        try:
                            bsInternal._getForegroundHostActivity().getMap().center.reflection = type
                            bsInternal._getForegroundHostActivity().getMap().center.reflectionScale = rs
                        except:
                            pass
                elif m == '/shatter':
                    if self.checkAdmin(nick):
                        if a == []:
                            
                            bs.screenMessage('Using: /shatter all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                        else:
                            if a[0] == 'all':
                                if self.checkAdmin(nick):
                                    for i in bsInternal._getForegroundHostActivity().players:
                                        i.actor.node.shattered = int(a[1])
                            else:
                                bsInternal._getForegroundHostActivity().players[int(a[0])].actor.node.shattered = int(a[1])
                

                elif m == '/sleep':
                    if self.checkAdmin(nick):
                        if a == []:
                            
                            bs.screenMessage('Using: /sleep all or number of list',color=(0,0,1), clients=[clientID], transient=True)
                        else:
                            if a[0] == 'all':
                                for i in bs.getSession().players:
                                    try:
                                        i.actor.node.handleMessage("knockout",5000)
                                    except:
                                        pass
                            else:
                                bs.getSession().players[int(a[0])].actor.node.handleMessage("knockout",5000)

                elif m == '/cmr':
                    if self.checkAdmin(nick):
                        if a == []:
                            time = 8000
                        else:
                            time = int(a[0])
                            
                            op = 0.08
                            std = bs.getSharedObject('globals').vignetteOuter
                            bsUtils.animateArray(bs.getSharedObject('globals'),'vignetteOuter',3,{0:bs.getSharedObject('globals').vignetteOuter,17000:(0,1,0)})
                            
                        try:
                            bsInternal._getForegroundHostActivity().getMap().node.opacity = op
                        except:
                            pass
                        try:
                            bsInternal._getForegroundHostActivity().getMap().bg.opacity = op
                        except:
                            pass
                        try:
                            bsInternal._getForegroundHostActivity().getMap().bg.node.opacity = op
                        except:
                            pass
                        try:
                            bsInternal._getForegroundHostActivity().getMap().node1.opacity = op
                        except:
                            pass
                        try:
                            bsInternal._getForegroundHostActivity().getMap().node2.opacity = op
                        except:
                            pass
                        try:
                            bsInternal._getForegroundHostActivity().getMap().node3.opacity = op
                        except:
                            pass
                        try:
                            bsInternal._getForegroundHostActivity().getMap().steps.opacity = op
                        except:
                            pass
                        try:
                            bsInternal._getForegroundHostActivity().getMap().floor.opacity = op
                        except:
                            pass
                        try:
                            bsInternal._getForegroundHostActivity().getMap().center.opacity = op
                        except:
                            pass
                            
                        def off():
                            op = 1
                            try:
                                bsInternal._getForegroundHostActivity().getMap().node.opacity = op
                            except:
                                pass
                            try:
                                bsInternal._getForegroundHostActivity().getMap().bg.opacity = op
                            except:
                                pass
                            try:
                                bsInternal._getForegroundHostActivity().getMap().bg.node.opacity = op
                            except:
                                pass
                            try:
                                bsInternal._getForegroundHostActivity().getMap().node1.opacity = op
                            except:
                                pass
                            try:
                                bsInternal._getForegroundHostActivity().getMap().node2.opacity = op
                            except:
                                pass
                            try:
                                bsInternal._getForegroundHostActivity().getMap().node3.opacity = op
                            except:
                                pass
                            try:
                                bsInternal._getForegroundHostActivity().getMap().steps.opacity = op
                            except:
                                pass
                            try:
                                bsInternal._getForegroundHostActivity().getMap().floor.opacity = op
                            except:
                                pass
                            try:
                                bsInternal._getForegroundHostActivity().getMap().center.opacity = op
                            except:
                                pass
                            bsUtils.animateArray(bs.getSharedObject('globals'),'vignetteOuter',3,{0:bs.getSharedObject('globals').vignetteOuter,100:std})
                        bs.gameTimer(time,bs.Call(off))
                elif m=='/contact':
                    
                    bs.screenMessage('discord mr.smoothy#5824',color=(0,0,1), clients=[clientID], transient=True)

                          
                elif m == '/help':
                    bs.screenMessage('Try commands ',color=(0,0,1), clients=[clientID], transient=True)
                    bs.screenMessage('/inv /spaz /box /headless',color=(0,0,1), clients=[clientID], transient=True)
                    bs.screenMessage('/shatter /sleep /iceoff /heal',color=(0,0,1), clients=[clientID], transient=True)
                    bs.screenMessage('/fly /gm /hug /remove /alien all',color=(0,0,1), clients=[clientID], transient=True)
                    bs.screenMessage('/freeze all /nv /ooh /mine all  /sm /end /curse',color=(0,0,1), clients=[clientID], transient=True)
                    bs.screenMessage('/kick /remove /bouncer /mix /thanos and many more',color=(0,0,1), clients=[clientID], transient=True)
                    bs.screenMessage('/contact to get discord id',color=(0,0,1), clients=[clientID], transient=True)
                    
                   
            
c = cheatOptions()

def cmnd(msg,clientID):
    if bsInternal._getForegroundHostActivity() is not None:
    
        c.opt(clientID,msg)
bs.realTimer(5000,bs.Call(bsInternal._setPartyIconAlwaysVisible,True))

import bsUI
bs.realTimer(10000,bs.Call(bsUI.onPartyIconActivate,(0,0)))## THATS THE TRICKY PART check ==> 23858 bsUI / _handleLocalChatMessage

#for help contact mr.smoothy#5824 on discord