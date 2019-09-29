
import bs
import bsInternal
import bsPowerup
import bsUtils
import random
import datetime
import pytz

class chatlogger(object):

	def chatwritter(self,gname,msg):
		currentdt=datetime.datetime.now(pytz.timezone('Asia/Calcutta'))


		with open(bs.getEnvironment()['systemScriptsDirectory'] + "/ChatsLogged.txt",mode='a') as f:
			f.write(str(currentdt)+str(self.checkId(gname))+'  || '+gname+' ||  '+msg+' \n') #https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy    
#discord @mr.smoothy#5824   
			f.close()
#https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy    
#discord @mr.smoothy#5824   			
	       
	def checkId(self,nick): # check host (settings.cmdForMe)
	    client_str = []
	    for client in bsInternal._getGameRoster():
	        if client['players'] != []:
	            if client['players'][0]['nameFull'].find(nick)!=-1:
	                client_str = client['displayString']
	                    #clientID = client['clientID']
	    return client_str  

	

#https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy    
#discord @mr.smoothy#5824   
d=chatlogger()
def chatLogg(msg):
    if bsInternal._getForegroundHostActivity() is not None:
	
        n = msg.split(': ')
        if n[0].endswith('...'):
        		
        		d.chatwritter(n[0][:-3],n[1])
        		
        else:

        	d.chatwritter(n[0],n[1])


#https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy    
#discord @mr.smoothy#5824    		  