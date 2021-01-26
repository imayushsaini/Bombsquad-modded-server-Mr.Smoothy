Prevent sending chat message from lobby 

Installation===========
- unzip .rar
- put antlobychat.py and pytransform2 folder in your scripts folder or bscfg/mods/
- in your bsUI.py 
	under _filterChatMessage() 
	add 

    import antlobychat
    msg=antlobychat.filter(msg,clientID)
    
    if not msg or not msg.strip():
        return None



def _filterChatMessage(msg, clientID):
    import antlobychat
    msg=antlobychat.filter(msg,clientID)
    
    if not msg or not msg.strip():
        return None
    ...............
    ...................
    ................

join to get support
https://discord.gg/ucyaesh