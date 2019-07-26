#SharksAndMinnows

import bs
import bsUtils
import random
import weakref

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [Chess]

class PieceSet(bs.BotSet):
    def _update(self):
        try:
            botList = self._botLists[self._botUpdateList] = [b for b in self._botLists[self._botUpdateList] if b.exists()]
        except Exception:
            bs.printException("error updating bot list: "+str(self._botLists[self._botUpdateList]))
        self._botUpdateList = (self._botUpdateList+1)%self._botListCount
        playerPts = []
        for player in bs.getActivity().teams[(self.team+1)%2].players:
            try:
                if player.isAlive():
                    playerPts.append((bs.Vector(*player.actor.node.position),
                                     bs.Vector(*player.actor.node.velocity)))
            except Exception:
                bs.printException('error on bot-set _update')

        for b in botList:
            b._setPlayerPts(playerPts)
            b._updateAI()

class Piece(bs.SpazBot):
    character = 'Spaz'
    piece = 'pawn'
    throwiness = 0.0
    punchiness = 0.0
    bouncy = False
    static = True
    run = False
    chargeDistMin = 0.0 # when we can start a new charge
    chargeDistMax = 2.0 # when we can start a new charge
    runDistMin = 0.0 # how close we can be to continue running
    chargeSpeedMin = 0.4
    chargeSpeedMax = 1.0
    throwDistMin = 5.0
    throwDistMax = 9.0
    throwRate = 1.0
    defaultBombType = 'normal'
    defaultBombCount = 3
    startCursed = False
    def __init__(self,player):
        bs.Spaz.__init__(self,color=player.color,highlight=player.highlight,character=self.character,
                      sourcePlayer=player,startInvincible=False,canAcceptPowerups=False)
        self.updateCallback = None
        self._map = weakref.ref(bs.getActivity().getMap())
        self.lastPlayerAttackedBy = None
        self.lastAttackedTime = 0
        self.lastAttackedType = None
        self.targetPointDefault = None
        self.heldCount = 0
        self.lastPlayerHeldBy = None
        self.targetFlag = None
        self._chargeSpeed = 0.5*(self.chargeSpeedMin+self.chargeSpeedMax)
        self._leadAmount = 0.5
        self._mode = 'wait'
        self._chargeClosingIn = False
        self._lastChargeDist = 0.0
        self._running = False
        self._lastJumpTime = 0
        self.node.name = self.piece.capitalize()
        self.node.nameColor = player.color
    

class AIKing(Piece):
    character = 'Mel'
    piece = 'king'

class AIQueen(Piece):
    static = False
    character = 'Pixel'
    punchiness = 1.0
    throwiness = 1.0
    piece = 'queen'
    bombType = 'impact'
    run  = True
    chargeDistMax = 20.0 # when we can start a new charge
    throwDistMax = 12

class AIRook(Piece):
    static = False
    character = 'Agent Johnson'
    throwiness = 1.0
    piece = 'rook'
    bombType = 'sticky'
    chargeDistMax = 20.0 # when we can start a new charge
    throwDistMax = 12.0

class AIBishop(Piece):
    static = False
    character = 'Pascal'
    throwiness = 1.0
    piece = 'bishop'
    bombType = 'ice'
    chargeDistMax = 4.0 # when we can start a new charge
    throwDistMax = 5.0

class AIKnight(Piece):
    static = False
    character = 'Snake Shadow'
    punchiness = 1.0
    piece = 'knight'
    chargeDistMax = 4.0 # when we can start a new charge

class AIPawn(Piece):
    character = 'Spaz'
    punchiness = 0.0
    throwiness = 0.0
    piece = 'pawn'
    chargeDistMax = 3.0 # when we can start a new charge

class Chess(bs.TeamGameActivity):
    
    @classmethod
    def getName(cls):
        return "Chess"

    @classmethod
    def getDescription(cls, sessionType):
        return "Defeat the opponent's king."

    @classmethod
    def getScoreInfo(cls):
        return{'scoreType':'points'}

    @classmethod
    def getSupportedMaps(cls, sessionType):
        return ['Football Stadium']

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.TeamsSession)else False

    def __init__(self,settings):
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
        
    def getInstanceScoreBoardDescription(self):
        return ('Queen: 9 | Rook: 7 | Bishop: 3 | Knight: 3 | Pawn: 1')
        
    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self,music='FlagCatcher')

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.characters = {'king':'Mel','queen':'Pixel','rook':'Agent Johnson','knight':'Snake Shadow','bishop':'Pascal','pawn':'Spaz'}
        self.points = {'king':0,'queen':9,'rook':7,'knight':3,'bishop':3,'pawn':1}
        self._scoredis = bs.ScoreBoard()
        for team in self.teams:
            team.gameData['score'] = 0
            self._scoredis.setTeamValue(team,team.gameData['score'])
        for i in range(len(self.teams[0].players)):
            player = self.teams[0].players[i]
            if i < 1: player.gameData['piece'] = 'king'
            elif i < 2: player.gameData['piece'] = 'queen'
            elif i < 4: player.gameData['piece'] = 'rook'
            elif i < 6: player.gameData['piece'] = 'knight'
            elif i < 8: player.gameData['piece'] = 'bishop'
            else: self.teams[0].players[i].gameData['piece'] = 'pawn'
            self.spawnPlayerSpaz(player,self.getMap().getStartPosition(0))
        self.teams[0].gameData['botSet'] = PieceSet()
        self.teams[0].gameData['botSet'].team = 0
        for j in range(i+1,16):
            if j < 1: bot = AIKing(player)
            elif j < 2: bot = AIQueen(player)
            elif j < 4: bot = AIRook(player)
            elif j < 6: bot = AIKnight(player)
            elif j < 8: bot = AIBishop(player)
            else: bot = AIPawn(player)
            self.teams[0].gameData['botSet'].addBot(bot)
            bot.team = self.teams[0]
            bot.handleMessage(bs.StandMessage(self.getMap().getStartPosition(0)))
        for i in range(len(self.teams[1].players)):
            player = self.teams[1].players[i]
            if i < 1: player.gameData['piece'] = 'king'
            elif i < 2: player.gameData['piece'] = 'queen'
            elif i < 4: player.gameData['piece'] = 'rook'
            elif i < 6: player.gameData['piece'] = 'knight'
            elif i < 8: player.gameData['piece'] = 'bishop'
            else: player.gameData['piece'] = 'pawn'
            self.spawnPlayerSpaz(player,self.getMap().getStartPosition(1))
        self.teams[1].gameData['botSet'] = PieceSet()
        self.teams[1].gameData['botSet'].team = 1
        for j in range(i+1,16):
            if j < 1: bot = AIKing(player)
            elif j < 2: bot = AIQueen(player)
            elif j < 4: bot = AIRook(player)
            elif j < 6: bot = AIKnight(player)
            elif j < 8: bot = AIBishop(player)
            else: bot = AIPawn(player)
            self.teams[1].gameData['botSet'].addBot(bot)
            bot.team = self.teams[1]
            bot.handleMessage(bs.StandMessage(self.getMap().getStartPosition(1)))

        
    def spawnPlayerSpaz(self,player,position=(0,3,0),angle=None):
        name = player.getName()
        color = player.color
        highlight = player.highlight
        spaz = bs.PlayerSpaz(color=color,
                             highlight=highlight,
                             character=self.characters[player.gameData['piece']],
                             player=player)
        player.setActor(spaz)
        if player.gameData['piece'] == 'king':
            player.actor.connectControlsToPlayer(enableBomb=False, enableRun = True, enableJump = True, enablePickUp = False, enablePunch=False)
        elif player.gameData['piece'] == 'queen':
            player.actor.connectControlsToPlayer(enableBomb=True, enableRun = True, enableJump = True, enablePickUp = True, enablePunch=True)
            player.actor.equipShields(False)
            spaz.bombType = 'impact'
        if player.gameData['piece'] == 'rook':
            player.actor.connectControlsToPlayer(enableBomb=True, enableRun = True, enableJump = True, enablePickUp = False, enablePunch=False)
            spaz.bombType = 'sticky'
        if player.gameData['piece'] == 'knight':
            player.actor.connectControlsToPlayer(enableBomb=False, enableRun = True, enableJump = True, enablePickUp = False, enablePunch=True)
        if player.gameData['piece'] == 'bishop':
            player.actor.connectControlsToPlayer(enableBomb=True, enableRun = True, enableJump = True, enablePickUp = False, enablePunch=False)
            spaz.bombType = 'ice'
        if player.gameData['piece'] == 'pawn':
            player.actor.connectControlsToPlayer(enableBomb=False, enableRun = False, enableJump = True, enablePickUp = True, enablePunch=False)
        spaz.node.name = player.getName()
        spaz.node.nameColor = color
        spaz.setScoreText(player.gameData['piece'].capitalize(),player.getTeam().color)
        spaz.handleMessage(bs.StandMessage(position))


    def onPlayerJoin(self, player):
        if self.hasBegun():
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText',subs=[('${PLAYER}',player.getName(full=True))]),color=(0,1,0))
            return

    def updateScore(self):
        for team in self.teams:
            self._scoredis.setTeamValue(team,team.gameData['score'])


    def handleMessage(self,m):
        if isinstance(m, bs.PlayerSpazDeathMessage):
            loseTeam = m.spaz.getPlayer().getTeam()
            for i in range(len(self.teams)):
                if loseTeam is self.teams[i]:
                    self.teams[(i+1)%2].gameData['score'] += self.points[m.spaz.getPlayer().gameData['piece']]
                    self.updateScore()
            if m.spaz.getPlayer().gameData['piece'] == 'king': bs.gameTimer(1000,self.checkEnd)
        elif isinstance(m, bs.SpazBotDeathMessage):
            loseTeam = m.badGuy.team
            for i in range(len(self.teams)):
                if loseTeam is self.teams[i]:
                    self.teams[(i+1)%2].gameData['score'] += self.points[m.badGuy.piece]
                    self.updateScore()
            if m.badGuy.piece == 'king': self.checkEnd()
        else: bs.TeamGameActivity.handleMessage(self, m)

    def checkEnd(self):
        for team in self.teams:
            c = 0
            for player in team.players:
                if player.gameData['piece'] == 'king' and player.isAlive():
                    c += 1
            if c == 0: self.endGame()
        if bs.getGameTime() > 60000: self.endGame()

    def endGame(self):
        results = bs.TeamGameResults()
        for team in self.teams:
            c = 0
            for player in team.players:
                if player.gameData['piece'] == 'king' and player.isAlive():
                    c += 1
            if c == 0: results.setTeamScore(team,0)
            else:
                score = team.gameData['score']
                results.setTeamScore(team,score)
        self.end(results=results,announceDelay=10)
