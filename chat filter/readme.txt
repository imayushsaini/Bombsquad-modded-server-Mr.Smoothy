ChatFilter

This will automatically kick player that use offensive words in public chat.

=============================
Installation
=============================
1.copy chatFilter.py in scripts folder 

2.open bsUi.py , search for method
 def _handleLocalChatMessage(msg): 

     and add these 2 lines

     import chatFilter
     chatFilter.chat(msg)

it should look like this 


def _handleLocalChatMessage(msg):
    global gPartyWindow
    
    import chatFilter
    chatFilter.chat(msg)
   
    if gPartyWindow is not None and gPartyWindow() is not None:
        gPartyWindow().onChatMessage(msg)
-----------------------------------------------------------

Modify chatFilter.py and add your words list in list tuple

this will also save complete msg where bad words are used in AbusedChat.txt in same folder.

For any help discord  @mr.smoothy#5824  
or report issue to this repository 

https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy

Dont forget to give credits.

Happy Modding ;-)