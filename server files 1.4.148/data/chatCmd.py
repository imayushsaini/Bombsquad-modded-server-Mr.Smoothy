# -*- coding: utf-8 -*-
import bs
import bsInternal
import bsPowerup
import bsUtils
import random
import getPermissionsHashes as gph
import BuddyBunny
import snowyPowerup
#import settings
#import portalObjects

class chatOptions(object):
    def __init__(self):
        self.all = True # just in case
       
        
        self.tint = None # needs for /nv
        
    def checkDevice(self,nick): # check host (settings.cmdForMe)
        n = "@"
        s = nick
        for i in bsInternal._getForegroundHostActivity().players:
            if i.getName().encode('utf-8') == nick:
                n = i.getInputDevice()._getAccountName(False)
        return bsInternal._getAccountDisplayString(False).encode('utf-8') == s
    
    def checkAdmin(self,nick): # check host (settings.cmdForMe)
        client_str = []
        for client in bsInternal._getGameRoster():
            if client['players'] != []:
                if client['players'][0]['name'] == nick.encode('utf-8'):
                    client_str = client['displayString']
                    #clientID = client['clientID']
        if client_str in gph.adminHashes:
            #bsInternal._chatMessage("Chat Commands Working")
            return True
        else:
            bsInternal._chatMessage("only member can use this command")
            bsInternal._chatMessage("whatsapp +91 9457179878 to become member, discord mr.smoothy#5824")
            return False
    def checkRoyal(self,nick): # check host (settings.cmdForMe)
        client_str = []
        for client in bsInternal._getGameRoster():
            if client['players'] != []:
                if client['players'][0]['name'] == nick.encode('utf-8'):
                    client_str = client['displayString']
                    #clientID = client['clientID']
        if client_str in gph.royalpass:
            #bsInternal._chatMessage("Chat Commands Working")
            return True
        else:
            bsInternal._chatMessage("only member can use this command")
            bsInternal._chatMessage("whatsapp +91 9457179878 to become member, discord mr.smoothy#5824")
            return False        
    def checkVip(self,nick): # check host (settings.cmdForMe)
        client_str = []
        for client in bsInternal._getGameRoster():
            if client['players'] != []:
                if client['players'][0]['name'] == nick.encode('utf-8'):
                    client_str = client['displayString']
                    #clientID = client['clientID']
        if client_str in gph.vipHashes:
            #bsInternal._chatMessage("Chat Commands Working")
            return True
        else:
            bsInternal._chatMessage("only owner can use this command")
            bsInternal._chatMessage("whatsapp +91 9457179878 to become owner , discord mr.smoothy#5824")
            return False

    def kickByNick(self,nick):
        roster = bsInternal._getGameRoster()
        for i in roster:
            try:
                if i['players'][0]['nameFull'].lower().find(nick.encode('utf-8').lower()) != -1:
                    bsInternal._disconnectClient(int(i['clientID']))
            except:
                pass
        
    def opt(self,nick,msg):
        if self.checkDevice(nick) or self.all:
            m = msg.split(' ')[0] # command
            a = msg.split(' ')[1:] # arguments
            
            activity = bsInternal._getForegroundHostActivity()
            with bs.Context(activity):
                if m == '/kick':
                    if self.checkAdmin(nick) or self.checkRoyal(nick):
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
                   

                elif m == '/list':
                    bsInternal._chatMessage("======== FOR /kick ONLY: ========")
                    for i in bsInternal._getGameRoster():
                        try:
                            bsInternal._chatMessage(i['players'][0]['nameFull'] + "     (/kick " + str(i['clientID'])+")")
                        except:
                            pass
                    bsInternal._chatMessage("==================================")
                    bsInternal._chatMessage("======= For other commands: =======")
                    for s in bsInternal._getForegroundHostSession().players:
                        bsInternal._chatMessage(s.getName() + "     "+ str(bsInternal._getForegroundHostSession().players.index(s)))
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


                elif m == '/owner':
                    if self.checkAdmin(nick) or self.checkRoyal(nick):
                        clID = int(a[0])
                        for client in bsInternal._getGameRoster():
                            if client['clientID']==clID:
                                if a[1] == 'add':
                                    newadmin = client['displayString']
                                    updated_admins = gph.adminHashes.append(newadmin)
                                elif a[1] == 'remove':
                                    newadmin = client['displayString']
                                    if newadmin in gph.adminHashes:
                                        updated_admins = gph.adminHashes.remove(newadmin)

                        
                        with open(bs.getEnvironment()['systemScriptsDirectory'] + "/getPermissionsHashes.py") as file:
                            s = [row for row in file]
                            s[0] = 'vipHashes = []'+'\n'
                            s[1] = 'adminHashes = '+ updated_admins + '\n'
                            f = open(bs.getEnvironment()['systemScriptsDirectory'] + "/getPermissionsHashes.py",'w')
                            for i in s:
                                f.write(i)
                            f.close()      

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
                    if self.checkAdmin(nick) or self.checkRoyal(nick):
                        bsInternal.quit()
                elif m == '/nv':
                    if self.tint is None:
                        self.tint = bs.getSharedObject('globals').tint
                    bs.getSharedObject('globals').tint = (0.5,0.7,1) if a == [] or not a[0] == u'off' else self.tint
                elif m == '/freeze':
                    if self.checkAdmin(nick) or self.checkVip(nick) or self.checkRoyal(nick):
                        if a == []:
                            bsInternal._chatMessage('Using: /freeze all or number of list')
                        else:
                            if a[0] == 'all':
                            
                                for i in bs.getSession().players:
                                    try:
                                        i.actor.node.handleMessage(bs.FreezeMessage())
                                    except:
                                        pass
                            else:
                                bs.getSession().players[int(a[0])].actor.node.handleMessage(bs.FreezeMessage())
                elif m == '/thaw':
                    if a == []:
                        bsInternal._chatMessage('Using: /thaw all or number of list')
                    else:
                        if a[0] == 'all':
                            for i in bs.getSession().players:
                                try:
                                    i.actor.node.handleMessage(bs.ThawMessage())
                                except:
                                    pass
                        else:
                            bs.getSession().players[int(a[0])].actor.node.handleMessage(bs.ThawMessage())




                elif m == '/mix':# add id to banlist=autokick list
                    if self.checkRoyal(nick):
                        if a == []:
                           bsInternal._chatMessage("MUST USE PLAYER ID OR NICK") #also FIX this every time bsInternal ChatMessage thing!! for stop loops "update-FIXED"
                        else:
                                      #firstly try nick if nick len is more then 2 else try as player id FIX ME
                            if len(a[0]) > 2:
                                for i in bs.getActivity().players:
                                    try:
                                        if (i.getName()).encode('utf-8') == (a[0]):
                                            bannedClient = i.getInputDevice().getClientID()
                                            bannedName = i.getName().encode('utf-8')
                                            bannedPlayerID = i.get_account_id()
                                            foolist = []
                                            foolist =gph.autoKickList
                                            if bannedPlayerID not in foolist:
                                              foolist.append(bannedPlayerID)
                                              bsInternal._chatMessage(str(bannedName) + " Banned")
                                              i.removeFromGame()
                                            else:
                                              bsInternal._chatMessage(str(bannedName) + " Already Banned")
                                            with open(bs.getEnvironment()['systemScriptsDirectory'] + "/getPermissionsHashes.py") as file:
                                                s = [row for row in file]
                                                s[7] = 'autoKickList = '+ str(foolist) + '\n'
                                                f = open(bs.getEnvironment()['systemScriptsDirectory'] + "/getPermissionsHashes.py",'w')
                                                for i in s:
                                                    f.write(i)
                                                f.close()
                                                reload(gph)
                                    except Exception:
                                        pass
                                bsInternal._chatMessage(bs.getSpecialChar('logoFlat'))
                            else:
                                try: 
                                    bannedClient = bsInternal._getForegroundHostSession().players[int(a[0])]
                                except Exception: 
                                      bsInternal._chatMessage("PLAYER NOT FOUND")
                                else:
                                    foolist = []
                                    foolist = gph.autoKickList
                                    bannedPlayerID = bannedClient.get_account_id()

                                    if bannedPlayerID not in foolist:

                                        foolist.append(bannedPlayerID)
                                        bsInternal._chatMessage(" mixed")
                                        
                                    else:
                                        bsInternal._chatMessage(str(bannedClient) + " Already Banned")
                                    with open(bs.getEnvironment()['systemScriptsDirectory'] + "/getPermissionsHashes.py") as file:
                                           s = [row for row in file]
                                           s[3] = 'autoKickList = '+ str(foolist) + '\n'
                                           f = open(bs.getEnvironment()['systemScriptsDirectory'] + "/getPermissionsHashes.py",'w')
                                           for i in s:
                                               f.write(i)
                                           f.close()
                                           reload(gph)

                elif m == '/unban':# remove id from banlist=autokick list
                    if a == []:
                       bsInternal._chatMessage("MUST USE PLAYER ID OR NICK")
                    else:
                      if len(a[0]) > 2:
                        for i in bs.getActivity().players:
                            try:
                                if (i.getName()).encode('utf-8') == (a[0]):
                                    bannedClient = i.getInputDevice().getClientID()
                                    bannedName = i.getName().encode('utf-8')
                                    bannedPlayerID = i.get_account_id()
                                    foolist = []
                                    foolist = gph.autoKickList
                                    if bannedPlayerID in foolist:
                                        foolist.remove(bannedPlayerID)
                                        bsInternal._chatMessage(str(bannedName) + " be free now!")
                                    else:
                                        bsInternal._chatMessage(str(bannedName) + " Already Not Banned")
                                    with open(bs.getEnvironment()['systemScriptsDirectory'] + "/getPermissionsHashes.py") as file:
                                        s = [row for row in file]
                                        s[3] = 'autoKickList = '+ str(foolist) + '\n'
                                        f = open(bs.getEnvironment()['systemScriptsDirectory'] + "/getPermissionsHashes.py",'w')
                                        for i in s:
                                            f.write(i)
                                        f.close()
                                        reload(gph)
                            except Exception:
                                pass
                        bsInternal._chatMessage(bs.getSpecialChar('logoFlat'))
                      else:
                          try: 
                              bannedClient = bsInternal._getForegroundHostSession().players[int(a[0])]
                          except Exception: 
                              bsInternal._chatMessage("PLAYER NOT FOUND")
                          else:
                              foolist = []
                              foolist = gph.autoKickList
                              bannedPlayerID = bannedClient.get_account_id()
                              if bannedPlayerID in foolist:
                                 foolist.remove(bannedPlayerID)
                                 bsInternal._chatMessage(str(bannedClient) + " be free now!")
                              else:
                                 bsInternal._chatMessage(str(bannedClient) + " Already Not Banned")
                              with open(bs.getEnvironment()['systemScriptsDirectory'] + "/getPermissionsHashes.py") as file:
                                   s = [row for row in file]
                                   s[3] = 'autoKickList = '+ str(foolist) + '\n'
                                   f = open(bs.getEnvironment()['systemScriptsDirectory'] + "/getPermissionsHashes.py",'w')
                                   for i in s:
                                       f.write(i)
                                   f.close()
                                   reload(gph)           
                elif m == '/thanos':
                    if a == []:
                        if self.checkAdmin(nick) or self.checkRoyal(nick):
                            bsInternal._chatMessage('Using: /kill all or number of list')
                    else:
                        if self.checkAdmin(nick):
                            if a[0] == 'all':
                                for i in bs.getSession().players:
                                    try:
                                        i.actor.node.handleMessage(bs.DieMessage())
                                    except:
                                        pass
                            else:
                                bs.getSession().players[int(a[0])].actor.node.handleMessage(bs.DieMessage())
                elif m == '/curse':
                    if self.checkAdmin(nick) or self.checkVip(nick) or self.checkRoyal(nick):
                        if a == []:
                            bsInternal._chatMessage('Using: /curse all or number of list')
                        else:
                            if a[0] == 'all':
                                for i in bs.getSession().players:
                                    try:
                                        i.actor.curse()
                                    except:
                                        pass
                            else:
                                bs.getSession().players[int(a[0])].actor.curse()
                elif m == '/box':
                    if a == []:
                        bsInternal._chatMessage('Using: /box all or number of list')
                    else:
                        try:
                            if a[0] == 'all':
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
                elif m == '/alien':
                    if a == []:
                        bsInternal._chatMessage('Using: /alien all or number of list')
                    else:
                        try:
                            if a[0] == 'all':
                                for i in bs.getSession().players:
                                    try:
                                        i.actor.node.torsoModel = bs.getModel("bomb")
                                    except:
                                        pass
                                for i in bs.getSession().players:
                                    try:
                                        i.actor.node.colorMaskTexture= bs.getTexture("agentHead")
                                    except:
                                        pass
                                for i in bs.getSession().players:
                                    try:
                                        i.actor.node.colorTexture= bs.getTexture("landMine")
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
                                        i.actor.node.style = "bunny"
                                    except:
                                        pass
                            else:
                                n = int(a[0])
                                bs.getSession().players[n].actor.node.torsoModel = bs.getModel("bomb"); 
                                bs.getSession().players[n].actor.node.colorMaskTexture= bs.getTexture("agentHead"); 
                                bs.getSession().players[n].actor.node.colorTexture= bs.getTexture("landMine") 
                                bs.getSession().players[n].actor.node.highlight = (1,1,1); 
                                bs.getSession().players[n].actor.node.color = (1,1,1); 
                                bs.getSession().players[n].actor.node.headModel = None; 
                                bs.getSession().players[n].actor.node.style = "bunny";
                        except:
                           pass           

                elif m == '/mine':
                    if a == []:
                        bsInternal._chatMessage('Using: /mine all or number of list')
                    else:
                        try:
                            if a[0] == 'all':
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

                elif m == '/headless': 
                    if a == []:
                        bsInternal._chatMessage('MUST USE PLAYER ID OR NICK')
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
                    if a == []:
                        bsInternal._chatMessage('MUST USE PLAYER ID OR NICK')
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
                        bsInternal._chatMessage('MUST USE PLAYER ID OR NICK')
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
                    if self.checkAdmin(nick) or self.checkRoyal(nick):
                        if a == []:
                            bsInternal._chatMessage('Using: /remove all or number of list')
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
                    if self.checkAdmin(nick) or self.checkRoyal(nick):
                        try:
                            bsInternal._getForegroundHostActivity().endGame()
                        except:
                            pass
                elif m == '/hug':
                    if a == []:
                        bsInternal._chatMessage('Using: /hug all or number of list')
                    else:
                        try:
                            if a[0] == 'all':
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
                           bs.screenMessage('Ошибка!',color = (1,0,0))
                elif m == '/gm':
                    if self.checkAdmin(nick) or self.checkRoyal(nick):
                        if a == []:
                            for i in range(len(activity.players)):
                                if activity.players[i].getName().encode('utf-8').find(nick.encode('utf-8').replace('...','').replace(':','')) != -1:
                                    activity.players[i].actor.node.hockey = activity.players[i].actor.node.hockey == False
                                    activity.players[i].actor.node.invincible = activity.players[i].actor.node.invincible == False
                                    activity.players[i].actor._punchPowerScale = 2 if activity.players[i].actor._punchPowerScale == 1.2 else 1.2
                        else:
                            activity.players[int(a[0])].actor.node.hockey = activity.players[int(a[0])].actor.node.hockey == False
                            activity.players[int(a[0])].actor.node.invincible = activity.players[int(a[0])].actor.node.invincible == False
                            activity.players[int(a[0])].actor._punchPowerScale = 2 if activity.players[int(a[0])].actor._punchPowerScale == 1.2 else 1.2
                elif m == '/tont':
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
                    bs.getSharedObject('globals').slowMotion = bs.getSharedObject('globals').slowMotion == False
                    bsInternal._chatMessage('आजा, डूब जाऊँ तेरी आँखों के ocean में, slow motion में')
                elif m == '/bouncer':
                    if self.checkRoyal(nick):
                        if a == []:

                            bsInternal._chatMessage('Using: /bouncer count owner(number of list)')
                        else:
                            if int(a[0])<=10:    
                            
                                for i in range(0,int(a[0])):
                                    p=bs.getSession().players[int(a[1])]
                                    if 'bunnies' not in p.gameData:
                                        p.gameData['bunnies'] = BuddyBunny.BunnyBotSet(p)
                                    p.gameData['bunnies'].doBunny()
                                    self._powersGiven = True
                                    
                                    bsInternal._chatMessage('/Bodyguard spawn ')


                elif m == '/spaz':
                    if a == []:
                        bsInternal._chatMessage('Using: /spaz all or number of list')
                    else:
                        try:
                            if a[0] == 'all':
                                if a[1]=='bunny' or a[1]=='ali' or a[1]=='cyborg':
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
                                if a[1]=='bunny' or a[1]=='ali' or a[1]=='cyborg':
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
                        bsInternal._chatMessage('Using: /spaz all or number of list')
                    else:
                        try:
                            if a[0] == 'all':
                                for i in bs.getSession().players:
                                    t = i.actor.node
                                    try:
                                       
                                        
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
                    try:
                        if bs.getSharedObject('globals').cameraMode == 'follow':
                            bs.getSharedObject('globals').cameraMode = 'rotate'
                        else:
                            bs.getSharedObject('globals').cameraMode = 'follow'
                    except:
                        pass
                elif m=='/sex':
                    
                    if a == []:
                        
                       bsInternal._chatMessage('please take your bra off.. i wanna suck nipples')
                    else:
                        
                        if a[0] == 'all':
                            bsInternal._chatMessage('i want group sex ...wanna join ?')

                elif m=='/kiss':
                    bsInternal._chatMessage('ummmahh.. on your vaginal lips..')  
                elif m=='/contact':
                    bsInternal._chatMessage('discord mr.smoothy#5824 whatsapp +91 9457179878 ') 
                elif m=='/fuck':
                    if a == []:
                        
                        bsInternal._chatMessage('Aaaah...Aaaah Harder...plss...fuck me hard ...omg!')
                    else:
                        
                        if a[0] == 'all':
                            bsInternal._chatMessage('i can fuck everyone.. with my large dick..oohh yeahh')
                        
                   
                elif m=='/love':
                    if a == []:
                        
                        bsInternal._chatMessage('hey ..you ..i love you .. wanna sex?')
                    else:
                        
                        if a[0] == 'all':
                            bsInternal._chatMessage('i love you all guyzz...')
                        
                elif m=='/sexy':
                    if a == []:
                        
                        bsInternal._chatMessage('hey sexy girl ...i like your figure')
                    else:
                        
                        if a[0] == 'all':
                            bsInternal._chatMessage('i like big breast..and wanna suck ')
                                             
                elif m == '/lm':
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
                    if self.checkRoyal(nick):
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
                    bsInternal._getForegroundHostActivity().players[int(a[0])].actor.node = bsInternal._getForegroundHostActivity().players[int(a[1])].actor.node
                elif m == '/fly':
                    if a == []:
                        bsInternal._chatMessage('Using: /fly all or number of list')
                    else:
                        if a[0] == 'all':
                            for i in bsInternal._getForegroundHostActivity().players:
                                i.actor.node.fly = True
                        else:
                            bsInternal._getForegroundHostActivity().players[int(a[0])].actor.node.fly = bsInternal._getForegroundHostActivity().players[int(a[0])].actor.node.fly == False
                elif m == '/flooorReflection':
                    bs.getSharedObject('globals').floorReflection = bs.getSharedObject('globals').floorReflection == False
                elif m == '/aco':
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
                        bsInternal._chatMessage('MUST USE PLAYER ID OR NICK')
                    else:
                        if a[0]=='all':
                            for i in bs.getActivity().players:
                                try:
                                    if i.actor.exists():
                                       i.actor.node.handleMessage(bs.PowerupMessage(powerupType = 'health'))
                                       bsInternal._chatMessage('shield will give you Protection')
                                except Exception:
                                    pass
                        if len(a[0]) > 2:
                           for i in bs.getActivity().players:
                               try:
                                   if (i.getName()).encode('utf-8') == (a[0]):
                                      if i.actor.exists():
                                         i.actor.node.handleMessage(bs.PowerupMessage(powerupType = 'health'))
                                         bsInternal._chatMessage('shield will give you Protection')
                               except Exception:
                                   pass
                           bsInternal._chatMessage(bs.getSpecialChar('logoFlat'))
                        else:
                             try:
                                 bs.getActivity().players[int(a[0])].actor.node.handleMessage(bs.PowerupMessage(powerupType = 'health'))
                                 bsInternal._chatMessage('shield will give you Protection')
                                 bsInternal._chatMessage(bs.getSpecialChar('logoFlat'))
                             except Exception:
                                 bsInternal._chatMessage('PLAYER NOT FOUND')       

                elif m == '/punch': #shield
                    if self.checkAdmin(nick)  or self.checkRoyal(nick):
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
                                                       
                elif m == '/reflectionso':
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
                    if a == []:
                        bsInternal._chatMessage('Using: /shatter all or number of list')
                    else:
                        if a[0] == 'all':
                            for i in bsInternal._getForegroundHostActivity().players:
                                i.actor.node.shattered = int(a[1])
                        else:
                            bsInternal._getForegroundHostActivity().players[int(a[0])].actor.node.shattered = int(a[1])
                

                elif m == '/sleep':
                    if a == []:
                        bsInternal._chatMessage('Using: number of list')
                    else:
                        if a[0] == 'all':
                            for i in bs.getSession().players:
                                try:
                                    i.actor.node.handleMessage("knockout",5000)
                                except:
                                    pass
                        else:
                            bs.getSession().players[int(a[0])].actor.node.handleMessage("knockout",5000)

                elif m == '/cm':
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
                        
                elif m == '/help':
                    bsInternal._chatMessage('Try commands ')
                    bsInternal._chatMessage('/inv /spaz /box /headless')
                    bsInternal._chatMessage('/shatter /sleep /iceoff /heal')
                    bsInternal._chatMessage('/fly /gm /hug /remove /alien all')
                    bsInternal._chatMessage('/freeze all /nv /ooh /mine all  /sm /end /curse')
                 
                    bsInternal._chatMessage('/sex /kiss /fuck /sexy all /love')
                    bsInternal._chatMessage('/kick /remove /bouncer /mix /thanos and many more')
                    bsInternal._chatMessage('/contact to get discord id')
                   
            
c = chatOptions()

def cmd(msg):
    if bsInternal._getForegroundHostActivity() is not None:
	
        n = msg.split(': ')
        c.opt(n[0],n[1])
bs.realTimer(5000,bs.Call(bsInternal._setPartyIconAlwaysVisible,True))

import bsUI
bs.realTimer(10000,bs.Call(bsUI.onPartyIconActivate,(0,0)))## THATS THE TRICKY PART check ==> 23858 bsUI / _handleLocalChatMessage

