ChatLogger

This will save all chat in text file in same directory.

=============================
Installation
=============================

1.copy chatLog.py in scripts folder 

2.open bsUi.py , search for method
 def _filterChatMessage(msg, clientID): 

     and add these 2 lines

     import chatLog
    chatLog.chatLogg(msg,clientID)

it should look like this 


def _filterChatMessage(msg, clientID):
    
    if not msg or not msg.strip():
        return None
    else:    
        import chatLog
        chatLog.chatLogg(msg,clientID)

        

        else:
            if '/' in msg:
               import cheatCmd
               cheatCmd.cmnd(msg,clientID)
               return None
            else:

                return msg


-----------------------------------------------------------



For any help discord  @mr.smoothy#5824  
or report issue to this repository 

https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy

Dont forget to give credits.

Happy Modding ;-)