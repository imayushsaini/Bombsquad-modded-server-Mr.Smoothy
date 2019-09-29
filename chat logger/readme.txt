ChatLogger

This will save all chat in text file in same directory.

=============================
Installation
=============================
1.We have to install pytz python lib.

so first install pip

  # apt install python-pip
  
and now install pytz

  # sudo pip install pytz

(enter these commands in linux terminal)
this lib. is used to set time by correct timezone for TimeStamp

2.copy chatLog.py in scripts folder 

3.open bsUi.py , search for method
 def _handleLocalChatMessage(msg): 

     and add these 2 lines

     import chatLog
    chatLog.chatLogg(msg)

it should look like this 


def _handleLocalChatMessage(msg):
    global gPartyWindow
    import chatLog
    chatLog.chatLogg(msg)
    
   
    if gPartyWindow is not None and gPartyWindow() is not None:
        gPartyWindow().onChatMessage(msg)
-----------------------------------------------------------



For any help discord  @mr.smoothy#5824  
or report issue to this repository 

https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy

Dont forget to give credits.

Happy Modding ;-)