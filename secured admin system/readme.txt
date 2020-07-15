Secured admin system to prevent id spoofers to get access to the commands

Modded by Mr.Smoothy

Updated July 2020
with build 1.4.155
-to remove some  spam  (chat commands will no longer appear in chats -unless you want it)  check bsUI.py  _filterChatMessage(msg, clientID):  to enable commands msg in chat 
-admin cant kick owners :P
-/me command to check your stats (need mystats.py/MythBstats.py  and change stats.json path in /me command)
-/me <clientid>  to check stats of other players

############Installation##############

put these 5 files 

bsUI.py
BuddyBunny.py
cheatCmd.py
membersID.py
prefix-tag.py


in scripts folder 
######################################
reboot the server
##############SETUP################

initially all are admins on server (tag will not visible)

join the game immediately and add yourself as admin using command 
 /admin 113 add

now shutdown the server

edit membersID.py  change allAdmins to False

and reboot the server

OR 
goto game setting >advance >entercode > getaccountid

and add your id to membersID.py
###################################

3 membership available 
admin,vip,member

and yes OWNER for managing

use commands to add them manually
example:
/admin 113 add
/vip 113 add
/member 113 add

and same for remove
/admin 113 remove
/vip 113 remove
/member 113 remove

**ALL THESE ARE PERMANENT 

account id of player will be added in membersID.py
since its not readable or hard to identify user 

membersidlogged.txt will be automatically created inside same folder
this will contain android/google id and account id of the players you added by command 

owner can add or remove admin,vip,member 
admin has access to all commands (not all actually)
vip has lesser
member have fewer

customize access for each membership according to your need in cheatCmd.py  
customize prefix-tag.py  to change tag color and text.


hurray you have done...........

contact @mr.smoothy#5824 (discord) for help


dont forget to give credit or giving me admin :P