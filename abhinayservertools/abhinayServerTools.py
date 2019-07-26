#-------------------------------------------------
#----------------Start of Code--------------------
#-------------------------------------------------
ver = 2.1
import os
def scriptsReplacer(filename,textToFind,textToAdd):
    x = open(os.path.join("data","scripts",filename),'r+').read()
    before = (x[:x.find(textToFind)])
    middle = textToAdd
    last = x[x.find(textToFind)+len(textToFind):]
    y = open(os.path.join("data","scripts",filename),'w').write(before+textToFind+middle+last)
if open(os.path.join('data','scripts','bsLobby.py'),'r+').read().find('abhinayServerTools().databaseReady') == -1:
    scriptsReplacer('bsLobby.py','            self.ready = True\n            self._updateText()','\n            from abhinayServerTools import abhinayServerTools\n            abhinayServerTools().databaseReady(self._player.getName(True),self._player)')
if open(os.path.join('data','scripts','bsLobby.py'),'r+').read().find('abhinayServerTools().databaseWaiting') == -1:
    scriptsReplacer('bsLobby.py','                name = bs.uniFromInts(nameChars[:10])+\'...\'','\n        from abhinayServerTools import abhinayServerTools\n        abhinayServerTools().databaseWaiting(name,self._player)')
if open(os.path.join('data','scripts','bsGame.py'),'r+').read().find('abhinayServerTools().banexecute') == -1:
    scriptsReplacer('bsGame.py','# limit player counts based on pro purchase/etc *unless* we\'re in a stress test','\n        from abhinayServerTools import abhinayServerTools\n        abhinayServerTools().banexecute(player)')
if open(os.path.join('data','scripts','bsGame.py'),'r+').read().find('abhinayServerTools().databaseLeave') == -1:
    scriptsReplacer('bsGame.py','# remove them from the game rosters','\n        from abhinayServerTools import abhinayServerTools\n        abhinayServerTools().databaseLeave(player.getName(full=True),player)')
if open(os.path.join('data','scripts','bsGame.py'),'r+').read().find('abhinayServerTools().rankName') == -1:
    scriptsReplacer('bsGame.py','        Create and wire up a bs.PlayerSpaz for the provide bs.Player.\n        """\n        name = player.getName()','\n        from abhinayServerTools import abhinayServerTools\n        name = abhinayServerTools().rankName(player)+player.getName()\n')
try :
    from astConfig import *
except Exception:
    f1=open(os.path.join("data","scripts","astConfig.py"),"w+")
    f1.write("#Supported Devices - Game Center,Game Circle,Google Play,Alibaba,Local,OUYA,Test,PC,Android,Linux,Mac\n\nids = [\'ID1\']\ndevices = [\'DEVICES1\',\'DEVICES2\']\n\nfakeNameChecker = False\nrealIdsToBeCheckedFromBeingFaked = \'PC152870\'\n\nwhitelist = False #If False Only the ids and devices specified in the ban.txt will get entry to your server\n\nprintServerWelcomeMessage=False #Whether to print a welcome message or not\nserverWelcomeMessage=\"Welcome To AbhinaY Server\" # The message\nserverWelcomeMessageColor=(1,1,1) #Its RGB color\n\nbanReason=\"Sorry you are Banned from this Server. Contact AbhinaY for help! Kicking in 5 seconds\" #The reason to give for banning\nbanReasonColor = (1,0,0) #Color of reason\ntimeWithBanPeopleToReadTheBanReason = 5000 # time to wait before kicking, keep it 0 to instant kick (5000 = 5sec)\n\nannounceOwnerNameOnEnteringYourServer = False #Whether to announce that the server owner has joined\nownerWrittenAboveOwnerName = False #Whether Owner should be written above Owner Name\naddIconAroundOwnerName = True\niconCodeOwner= u\"\ue043\"#Crown\nserverOwnerID = [] #Replace it with owners\' id.\nshowOwnerProfileNameWhileAnnouncing = False # This will also display the owner name while displaying the below message\nownerAnnounceMessage=\" is the Server Owner and is Online!\" #the message\nownerAnnounceMessageColor = (0,1,1) #its color\nkeepAnnouncingOwnerNameAfterGivenTime = False #keep announcing owner name after the below specified time\nsecondsToAnnounceOwnerEntry=5000#5000 = 5seconds (KEEP A LONGER VALUE TO STAY AWAY FROM LAGS) after how many seconds it shud be repeated\n\nannounceAdminNameOnEnteringYourServer = False\nadminWrittenAboveAdminName = False\naddIconAroundAdminName = True\niconCodeAdmin= u\"\ue044\"#Zen\nserverAdminID = [\'PC152870\'] #Replace it with your id.\nshowAdminProfileNameWhileAnnouncing = False\nadminAnnounceMessage=\" is Server Admin and is Online!\"\nadminAnnounceMessageColor = (0,1,1)\nkeepAnnouncingAdminNameAfterGivenTime = False\nsecondsToAnnounceAdminEntry=60000 #5000 = 5seconds\n\nannounceElderNameOnEnteringYourServer = False\nelderWrittenAboveElderName = False\naddIconAroundElderName = True\niconCodeElder= u\"\ue00c\"#2d bs logo\nserverElderID = [\'PC152870\'] #Replace it with your id.\nshowElderProfileNameWhileAnnouncing = False\nelderAnnounceMessage=\" is Server Elder and is Online!\"\nelderAnnounceMessageColor = (0,1,1)\nkeepAnnouncingElderNameAfterGivenTime = False\nsecondsToAnnounceElderEntry=60000 #5000 = 5seconds\n\nkeepCheckingBanlistAfterASpecifiedTime=False #FALSE RECOMMENDED May Cause Serious Lags if a Lesser Time is provided(Lags the server for 0.5sec to check the banlist every given second)\nsecondsToCheckBanlistAgain=5000 #5000 = 5seconds\n\ngiveCreditToAbhinaY = True #Kindly keep it true if you want to appreciate my work!")
    f1.close()
    from astConfig import *
import bs
import bsInternal
import imp
from bsUI import *
import bsUI
temp = [0,0,0,0]
import sqlite3
import time
import datetime
connection = sqlite3.connect("serverData.db")
connection1 = sqlite3.connect("noneOfYourBusiness.db")
connection.text_factory = str
connection1.text_factory = str
c1 = connection1.cursor()
c = connection.cursor()
connection.cursor().execute("CREATE TABLE IF NOT EXISTS allPlayers (Account TEXT,ID TEXT,Time TEXT,Status TEXT,TimePlayed TEXT,tempPlayerID TEXT,Faker TEXT, UNIQUE(Account, ID, Time)) ")
c1.execute("CREATE TABLE IF NOT EXISTS timeCalc (Account TEXT KEY UNIQUE,Time INTEGER)")
class abhinayServerTools():
    def rankName(self,player):
        supername = player.getName(icon=False)
        supername_ = player.getName(True)
        def elderNameAnnounce():
            name = supername
            if not elderWrittenAboveElderName: return False
            if addIconAroundElderName:
                b=u"\ue072"+iconCodeElder+name+iconCodeElder
            else:
                b=supername_
            roster = bsInternal._getGameRoster()
            for xx in roster:
                if xx['displayString'].endswith(tuple(serverElderID)):
                    ID = xx['clientID']
                    if player.getInputDevice().getClientID()==ID:
                       player.setName(player.getName(),b,real=True)
                       return True
            return False
        def adminNameAnnounce():
            name = supername
            if not adminWrittenAboveAdminName : return False
            if addIconAroundAdminName:
                b=u"\ue072"+iconCodeAdmin+name+iconCodeAdmin
            else:
                b=supername_
            roster = bsInternal._getGameRoster()
            for xx in roster:
                if xx['displayString'].endswith(tuple(serverAdminID)):
                    ID = xx['clientID']
                    if player.getInputDevice().getClientID()==ID:
                        player.setName(player.getName(),b,real=True)
                        return True
            return False
        adminNameAnnounce()
        def ownerNameAnnounce():
            name = supername
            if not ownerWrittenAboveOwnerName: return False
            if addIconAroundOwnerName:
                b=u"\ue072"+iconCodeOwner+name+iconCodeOwner
            else:
                b=supername_
            roster = bsInternal._getGameRoster()
            for xx in roster:
                if xx['displayString'].endswith(tuple(serverOwnerID)):
                    ID = xx['clientID']
                    if player.getInputDevice().getClientID()==ID:
                        player.setName(player.getName(),b,real=True)
                        return True
            return False
        if ownerNameAnnounce():return "OWNER\n"
        if adminNameAnnounce():return "ADMIN\n"
        if elderNameAnnounce():return "ELDER\n"
        return ""
    def databaseWaiting(self, name, player):
        time = datetime.datetime.now().strftime('%Y-%m-%d | %H:%M:%S')
        faker = False
        if fakeNameChecker and name.endswith(tuple(realIdsToBeCheckedFromBeingFaked)): faker = True
        connection.cursor().execute(("REPLACE INTO allPlayers (Account, ID, Time, Status, tempPlayerID, Faker) VALUES ((?),(?),(?),('Waiting'),(?),(?))"), (player.getInputDevice()._getAccountName(True), name, time,player.getID(),faker))
        connection.commit()
    def databaseReady(self, name, player):
        faker = False
        if fakeNameChecker and name.endswith(tuple(realIdsToBeCheckedFromBeingFaked)): faker = True
        c1.execute("CREATE TABLE IF NOT EXISTS timeCalc (Account TEXT PRIMARY KEY UNIQUE,Time INTEGER)")
        c1.execute(("REPLACE INTO timeCalc(Account, Time) VALUES ((?),(?))"), (player.getID(),time.time()))
        time1 = datetime.datetime.now().strftime('%Y-%m-%d | %H:%M:%S')
        c.execute(("REPLACE INTO allPlayers (Account, ID, Time, Status, tempPlayerID, Faker) VALUES ((?),(?),(?),('Ready'),(?),(?))"), (player.getInputDevice()._getAccountName(True), name, time1, player.getID(),faker))
        connection1.commit()
        connection.commit()
    def databaseLeave(self, name, player):
        faker = False
        if fakeNameChecker and name.endswith(tuple(realIdsToBeCheckedFromBeingFaked)): faker = True
        yax = time.time()
        xxax = c1.execute(("SELECT Time FROM timeCalc WHERE Account = (?)"), (player.getID(), ))
        for rowax in xxax:
            yax = rowax[0]
        zax = time.time()-yax
        xxax1 = c.execute(("SELECT Account FROM allPlayers WHERE tempPlayerID = (?)"), (player.getID(), ))
        for rowax1 in xxax1:
            yax1 = rowax1[0]
        time1 = datetime.datetime.now().strftime('%Y-%m-%d | %H:%M:%S')
        c.execute(("REPLACE INTO allPlayers (Account, ID, Time,Status, TimePlayed, Faker) VALUES ((?),(?),(?),('Leave'),(?),(?))"), (yax1, name, time1, zax,faker))
        connection.commit()
    def banexecute(self,player):
        try:
            if printServerWelcomeMessage:bs.screenMessage(serverWelcomeMessage,color=serverWelcomeMessageColor,clients=[player.getInputDevice().getClientID()],transient=True)
            if giveCreditToAbhinaY:bs.screenMessage("Ban System by AbhinaY (Website - technicraze.ml)",color=(1,1,0),clients=[player.getInputDevice().getClientID()],transient=True)
        except Exception:pass
        def intervalKick():
            kickcheck()
            bs.gameTimer(secondsToCheckBanlistAgain,bs.Call(intervalKick))
        def ownerEntryAnnounce(loop):
            roster = bsInternal._getGameRoster()
            for xx in roster:
                if xx['displayString'].endswith(tuple(serverOwnerID)):
                    rtr1 = xx['specString']
                    ID = xx['clientID']
                    namename=xx['displayString']
                    try: cidd = player.getInputDevice().getClientID()
                    except Exception: cidd = -5
                    if cidd==ID:
                        try:
                            if player.getName(full=True) != '' and player.getName(full=True) != "<choosing player>":namename = player.getName(full=True)
                        except Exception: 
                            pass
                        if showOwnerProfileNameWhileAnnouncing:
                            asd = namename+ownerAnnounceMessage
                            bs.screenMessage(asd,color=ownerAnnounceMessageColor)
                        else:
                            bs.screenMessage(ownerAnnounceMessage,color=ownerAnnounceMessageColor)
                    else:
                        bs.screenMessage(namename+ownerAnnounceMessage,color=ownerAnnounceMessageColor)
            if loop: bs.gameTimer(secondsToAnnounceOwnerEntry,bs.Call(ownerEntryAnnounce,True))
        def adminEntryAnnounce(loop):
            roster = bsInternal._getGameRoster()
            for xx in roster:
                if xx['displayString'].endswith(tuple(serverAdminID)):
                    rtr1 = xx['specString']
                    ID = xx['clientID']
                    namename=xx['displayString']
                    try: cidd = player.getInputDevice().getClientID()
                    except Exception: cidd = -5
                    if cidd==ID:
                        try:
                            if player.getName(full=True) != '' and player.getName(full=True) != "<choosing player>":
                                namename = player.getName(full=True)                                
                        except Exception: 
                            pass
                        if showAdminProfileNameWhileAnnouncing:
                            asd = namename+adminAnnounceMessage
                            bs.screenMessage(asd,color=adminAnnounceMessageColor)
                        else:
                            bs.screenMessage(adminAnnounceMessage,color=ownerAnnounceMessageColor)
                    else:
                        bs.screenMessage(namename+adminAnnounceMessage,color=ownerAnnounceMessageColor)
            if loop: bs.gameTimer(secondsToAnnounceAdminEntry,bs.Call(adminEntryAnnounce,True))
        def elderEntryAnnounce(loop):
            roster = bsInternal._getGameRoster()
            for xx in roster:
                if xx['displayString'].endswith(tuple(serverElderID)):
                    rtr1 = xx['specString']
                    ID = xx['clientID']
                    namename=xx['displayString']
                    try: cidd = player.getInputDevice().getClientID()
                    except Exception: cidd = -5
                    if cidd==ID:
                        try:
                            if player.getName(full=True) != '' and player.getName(full=True) != "<choosing player>":namename = player.getName(full=True)
                        except Exception: 
                            pass
                        if showElderProfileNameWhileAnnouncing:
                            asd = namename+elderAnnounceMessage
                            bs.screenMessage(asd,color=elderAnnounceMessageColor)
                        else:
                            bs.screenMessage(elderAnnounceMessage,color=ownerAnnounceMessageColor)
                    else:
                        bs.screenMessage(namename+elderAnnounceMessage,color=ownerAnnounceMessageColor)
            if loop: bs.gameTimer(secondsToAnnounceElderEntry,bs.Call(elderEntryAnnounce,True))
            
        def kick(id):
            def _kick(id):
                bsInternal._disconnectClient(id)
            bs.screenMessage(banReason,color=banReasonColor,clients=[id],transient=True)
            bs.gameTimer(timeWithBanPeopleToReadTheBanReason,bs.Call(_kick,id))

        def kickcheck():
            
            if announceOwnerNameOnEnteringYourServer and not keepAnnouncingOwnerNameAfterGivenTime: ownerEntryAnnounce(False)
            if announceAdminNameOnEnteringYourServer and not keepAnnouncingAdminNameAfterGivenTime: adminEntryAnnounce(False)
            if announceElderNameOnEnteringYourServer and not keepAnnouncingElderNameAfterGivenTime: elderEntryAnnounce(False)
            configfile = imp.load_source('banfile', '', open(os.path.join("data","scripts","astConfig.py")))
            ids = []
            devices = []
            try: 
                ids = configfile.ids
            except Exception: pass
            try: 
                devices = configfile.devices      
            except Exception: pass            
            for rtr in bsInternal._getGameRoster():
                rtr1 = rtr['specString']
                ID = rtr['clientID']
                name = rtr1[6:(rtr1.find("\",\"a\":"))] 
                account = rtr1[(rtr1.find("\",\"a\":")+7):(rtr1.find("\",\"sn\":"))]
                if account=='Local':
                    s=str(name)
                else:
                    s=str(account+name)
                if whitelist:
                    if not s.endswith(tuple(ids)):
                        if not s.startswith(tuple(devices)):
                            kick(ID)
                else:
                    if s.endswith(tuple(ids)) or s.startswith(tuple(devices)):
                        kick(ID)
                  
                    ''' 
                    if(client=='pb-IF4uV0VZKw=='):
                        bsInternal._chatMessage("/kick "+str(i.getInputDevice().getClientID()))
                        kick(i.getInputDevice().getClientID())
                    '''    




        kickcheck()
        if temp[0]==0 and keepAnnouncingOwnerNameAfterGivenTime:
            temp[0]=1
            ownerEntryAnnounce(True)
        if temp[1]==0 and keepAnnouncingAdminNameAfterGivenTime:
            temp[1]=1
            adminEntryAnnounce(True)
        if temp[2]==0 and keepAnnouncingElderNameAfterGivenTime:
            temp[2]=1
            elderEntryAnnounce(True)
        if temp[3]==0 and keepCheckingBanlistAfterASpecifiedTime:
            temp[3]=1
            bs.gameTimer(secondsToCheckBanlistAgain,bs.Call(intervalKick))
            
class DamnPartyWindow(PartyWindow):
    def _onPartyMemberPress(self, clientID, isHost, widget):
        # THANKS TO DEVA
        if bsInternal._getForegroundHostSession() is not None:
            kickStr = bs.Lstr(resource='kickText')
        else:
            # kick-votes appeared in build 14248
            if bsInternal._getConnectionToHostInfo().get('buildNumber', 0) < 14248:
                return
            kickStr = bs.Lstr(resource='kickVoteText')
            for rst in self._roster:
                cid = rst['clientID']
                if cid == clientID:
                    bs.screenMessage(rst['displayString'])
                    x=rst['clientID']
                    bs.screenMessage(str(x))
                    break
        p = PopupMenuWindow(position=widget.getScreenSpaceCenter(),
                            scale=2.3 if gSmallUI else 1.65 if gMedUI else 1.23,
                            choices=['kick'],
                            choicesDisplay=[kickStr],
                            currentChoice='kick',
                            delegate=self).getRootWidget()
        self._popupType='partyMemberPress'
        self._popupPartyMemberClientID = clientID
        self._popupPartyMemberIsHost = isHost


bsUI.PartyWindow = DamnPartyWindow