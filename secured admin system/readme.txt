Secured admin system to prevent id spoofers to get access to the commands

Modded by Mr.Smoothy

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
###################################

3 membership available 
admin,vip,member

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


admin has access to all commands
vip has lesser
member have fewer

customize access for each membership according to your need in cheatCmd.py  
customize prefix-tag.py  to change tag color and text.


hurray you have done...........

contact @mr.smoothy#5824 (discord) for help


dont forget to give credit or giving me admin :P