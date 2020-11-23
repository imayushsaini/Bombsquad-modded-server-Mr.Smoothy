ChatFilter

This will automatically kick player that use offensive words in public chat.

=============================
Installation
=============================
1.copy chatFilter.py in scripts folder 

2.open bsUi.py , search for method

 def _filterChatMessage(msg, clientID): 

     and add these 4 lines

     import chatFilter
     if(chatFilter.chat(msg,clientID)):
            bs.screenMessage('Please dont spoil environment',color=(1,0,0), clients=[clientID], transient=True)
            bs.screenMessage('Dont Abuse',color=(1,0,0), clients=[clientID], transient=True)

it should look like this 


def _filterChatMessage(msg, clientID):
    
    if not msg or not msg.strip():
        return None
    else:    
        import chatLog
        chatLog.chatLogg(msg,clientID)

        import chatFilter
        if(chatFilter.chat(msg,clientID)):
            bs.screenMessage('Please dont spoil environment',color=(1,0,0), clients=[clientID], transient=True)
            bs.screenMessage('Dont Abuse',color=(1,0,0), clients=[clientID], transient=True)

        else:
            if '/' in msg:
               import cheatCmd
               cheatCmd.cmnd(msg,clientID)
               return None
            else:

                return msg


-----------------------------------------------------------

Modify chatFilter.py and add your words list in list tuple

this will also save complete msg where bad words are used in AbusedChat.txt in same folder.

For any help discord  @mr.smoothy#5824  
or report issue to this repository 

https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy

Dont forget to give credits.

Happy Modding ;-)