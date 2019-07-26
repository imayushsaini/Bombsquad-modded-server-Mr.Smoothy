# Massacre
# This game will create a mass of lame kronks, 
# which the player will have to kill in  60 sec
# to earn points. They also respawn.

import bs
import random

#This tells the game which version of the API the mod uses.
def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [Massacre]

def bsGetLevels():
    return [bs.Level('Massacre 123', #<---- This name right here has to be unique to be recognized as a new game.
                     displayName='${GAME}',
                     gameType=Massacre,
                     settings={},
                     previewTexName='courtyardPreview')]

class Massacre(bs.TeamGameActivity):

# Returns the name of the game
    @classmethod
    def getName(cls):
        return 'Massacre'
        
# This returns what kind of scoring method is it.
    @classmethod
    def getScoreInfo(cls):
        return {'scoreType':'points'}

# This returns the game description
    @classmethod
    def getDescription(cls,sessionType):
        return 'Kill as many as you can.'
    
# This game is played on Doom Shroom 
    @classmethod
    def getSupportedMaps(cls,sessionType):
        return ['Doom Shroom']
        
# For now this game is just coop 
    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if issubclass(sessionType,bs.CoopSession) else False

# Play some nice dramatic music
    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self,music='ToTheDeath')
        
    def __init__(self, settings):
        bs.TeamGameActivity.__init__(self,settings)
        self.info = bs.NodeActor(bs.newNode('text',
                                                   attrs={'vAttach': 'bottom',
                                                          'hAlign': 'center',
                                                          'vrDepth': 0,
                                                          'color': (0,.2,0),
                                                          'shadow': 1.0,
                                                          'flatness': 1.0,
                                                          'position': (0,0),
                                                          'scale': 0.8,
                                                          'text': "Created by MattZ45986 on Github",
                                                          }))


    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        # End the game in a minute
        bs.gameTimer(60000,bs.WeakCall(self.endGame))
        bs.OnScreenCountdown(60).start()
        # Call the method to spawn our kronks
        bs.gameTimer(1000,bs.WeakCall(self.spawnBots))
        self._gamescore = 0
        # Set up a scoreboard
        self._scoredis = bs.ScoreBoard()
        self._scoredis.setTeamValue(self.teams[0],self._gamescore)
        # Enable powerups with TNT
        self.setupStandardPowerupDrops(enableTNT=True)
        

    def spawnBots(self):
        self._gamescore = 0
        self._bots = bs.BotSet()
        # Display a warning message
        bs.screenMessage('Here come the Bots', color = (1,0,0))
        # Generate 100 kronks in random positions
        for i in range(0,10):
            # (This is the center)
            p = [0, 2.5, -3]
            bs.gameTimer(1000,bs.Call(self._bots.spawnBot,bs.ToughGuyBotLame,pos=(p[0] + random.randint(-3,3),2.5,p[2] + random.randint(-3,3)),spawnTime=3000))
    
# Show a message when a player leaves
    def onPlayerLeave(self, player):
        message = str(player.getName(icon=False)) + " has chickened out!"
        bs.screenMessage(message, color=player.color, top=True)

    def handleMessage(self,m):
        # If a player dies respawn them in a few seconds.
        if isinstance(m,bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m)
            self.respawnPlayer(m.spaz.getPlayer())
            # It's always nice to display an encouraging message
            bs.screenMessage("You DIED!", color=(1,0,0))
        # If a kronk died, then raise the score by 5 and respawn another kronk
        elif isinstance(m,bs.SpazBotDeathMessage):
            self._gamescore = 5 + self._gamescore
            bs.TeamGameActivity.handleMessage(self,m)
            # When they reach another hundred give 'em a thumbs up
            if self._gamescore % 100 == 0:
                bs.screenMessage("Nice!", color=(0,1,0))
            # Update scoreboard and respawn the kronk
            self.scoreBoard()
            self.respawn()
        # If it's nothing special let the game handle it
        else:
            bs.TeamGameActivity.handleMessage(self,m)

    # Update the scoreboard with the new score value
    def scoreBoard(self):
        for team in self.teams:
            self._scoredis.setTeamValue(team,self._gamescore)

    # Respwan a kronk
    def respawn(self):
        p = [0,2.5,-3]
        bs.gameTimer(1000,bs.WeakCall(self._bots.spawnBot,bs.ToughGuyBotLame,pos=(p[0] + random.randint(-3,3),2.5,p[2] + random.randint(-3,3)),spawnTime=3000))
        
    # At the end of the 60 seconds give the results to the game and end
    def endGame(self):
        ourResults = bs.TeamGameResults()
        # (There should only be one anyway)
        for team in self.teams:
            ourResults.setTeamScore(team, self._gamescore)
        self.end(results=ourResults)
