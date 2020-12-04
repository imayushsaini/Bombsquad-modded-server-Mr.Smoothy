Credits :
MythB - for stats 
sobydamn - for rank system

Modification :
-added KD (kill/death ratio) with rank 

-and PRO OR NOOB tag according to that KD



Installation
>put all files in scripts folder 

>open bsGame.py search for def onBegin(self, customContinueMessage=None):
      will found this at line no. 1949(approx)
      add
	    import MythBStats
            MythBStats.update(self.scoreSet)
      will  look like this

 def onBegin(self, customContinueMessage=None):
        Activity.onBegin(self)
        
        import MythBStats
        MythBStats.update(self.scoreSet)

        # pop up a 'press any button to continue' statement after our
        # min-view-time show a 'press any button to continue..'f
        # thing after a bit..
        if bs.getEnvironment()['interfaceType'] == 'large':
            # FIXME - need a better way to determine whether we've probably
            # got a keyboard
            s = bs.Lstr(resource='pressAnyKeyButtonText')
        else:
            s = bs.Lstr(resource='pressAnyButtonText')

        bsUtils.Text(customContinueMessage if customContinueMessage else s,
                     vAttach='bottom',
                     hAlign='center',
                     flash=True,
                     vrDepth=50,
                     position=(0, 10),
                     scale=0.8,
                     color=(0.5, 0.7, 0.5, 0.5),
                     transition='inBottomSlow',
                     transitionDelay=self._minViewTime).autoRetain()


Migrating from other rank to kd system===================
just use prefix-tag.py ....
you might already have stats and rank scripts installed
just check the path of stats.json and rank/toprank.py  and modify path in  prefix-tag.py 

if not works ..replace everything


and yes need to remove old tag scripts .. or copy paste code to your old scripts (for modders).


for any help discord @mr.smoothy@5824 or raise issue on github

https://github.com/imayushsaini/Bombsquad-modded-server-Mr.Smoothy
