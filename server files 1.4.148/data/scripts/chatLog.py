
import bs
import bsInternal
import bsPowerup
import bsUtils
import random

class chatlogger(object):

	def chatwritter(self,gname,msg):


		with open(bs.getEnvironment()['systemScriptsDirectory'] + "/ChatsLogged.txt",mode='a') as f:
			f.write('  || '+gname+' ||  '+msg+' \n')
			f.close()
			
	       
	def checkId(self,nick): # check host (settings.cmdForMe)
	    client_str = []
	    for client in bsInternal._getGameRoster():
	        if client['players'] != []:
	            if client['players'][0]['name'] == nick.encode('utf-8'):
	                client_str = client['displayString']
	                    #clientID = client['clientID']
	    return client_str  

	


d=chatlogger()
def chatLogg(msg):
    if bsInternal._getForegroundHostActivity() is not None:
	
        n = msg.split(': ')
        d.chatwritter(n[0],n[1])    