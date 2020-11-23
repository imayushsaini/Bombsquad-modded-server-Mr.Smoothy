# -*- coding: utf-8 -*-
# coding: utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import bs
import bsInternal
import bsPowerup
import bsUtils
import random
import datetime


class chatlogger(object):

	def chatwritter(self,msg):
		


		with open(bs.getEnvironment()['systemScriptsDirectory'] + "/ChatsLogged.txt",mode='a') as f:
			f.write(str(msg+' \n'))
			f.close()
			
	       
	def checkId(self,nick): # check host (settings.cmdForMe)
	    client_str = []
	    for client in bsInternal._getGameRoster():
	        if client['players'] != []:
	            if client['players'][0]['nameFull'].find(nick)!=-1:
	                client_str = client['displayString']
	                    #clientID = client['clientID']
	    return client_str  

	


d=chatlogger()
def chatLogg(msg,clientID):
    if bsInternal._getForegroundHostActivity() is not None:
	
        n = msg.split(': ')
        client='kuchbhi'
        name="dsf"
        for i in bsInternal._getForegroundHostActivity().players:
            
            if i.getInputDevice().getClientID()==clientID:
                client=i.get_account_id()
                name=i.getName() 
        msg=client+'||'+name.encode('utf-8')+"||"+msg.encode('utf-8')
        d.chatwritter(msg)
        		  