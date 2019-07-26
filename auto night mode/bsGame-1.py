import bs
import bsInternal
from bsVector import Vector
import weakref
import random
import bsUtils
import time
import pytz
import datetime

#auto nightmode by mr.smoothy   https://github.com/imayushsaini/Bombsquad-Mr.Smoothy-Admin-Powerup-Server




class Team(object):
    """
    category: Game Flow Classes

    A team of one or more bs.Players.
    Note that a player *always* has a team;
    in some cases, such as free-for-all bs.Sessions,
    the teams consists of just one bs.Player each.

    Attributes:

       name
          The team's name.

       color
          The team's color.

       players
          The list of bs.Players on the team.

       gameData
          A dict for use by the current bs.Activity
          for storing data associated with this team.
          This gets cleared for each new bs.Activity.

       sessionData
          A dict for use by the current bs.Session for
          storing data associated with this team.
          Unlike gameData, this perists for the duration
          of the session.
    """

    def __init__(self, teamID=0, name='', color=(1, 1, 1)):
        """
        Instantiate a team. In most cases teams are provided to you
        automatically by the bs.Session, so calling this shouldn't be necessary.
        """
        # we override __setattr__ to lock ourself down
        # so we have to set attrs all funky-like
        object.__setattr__(self, '_teamID', teamID)
        object.__setattr__(self, 'name', name)
        object.__setattr__(self, 'color', tuple(color))
        object.__setattr__(self, 'players', [])
        object.__setattr__(self, 'gameData', {})  # per-game user-data
        object.__setattr__(self, 'sessionData', {})  # per-session user-data

    def getID(self):
        'Returns the numeric team ID.'
        return object.__getattribute__(self, '_teamID')

    def celebrate(self, duration=10000):
        'Tells all players on the team to celebrate'
        for player in self.players:
            try:
                player.actor.node.handleMessage('celebrate', 10000)
            except Exception:
                pass

    def _reset(self):
        self._resetGameData()
        object.__setattr__(self, 'players', [])

    def _resetGameData(self):
        object.__setattr__(self, 'gameData', {})

    def _resetSessionData(self):
        object.__setattr__(self, 'sessionData', {})

    def __setattr__(self, name, value):
        raise Exception("can't set attrs on bs.Team objects")


class OutOfBoundsMessage(object):
    """
    category: Message Classes

    Tells an object that it is out of bounds.
    """
    pass


class DieMessage(object):
    """
    category: Message Classes

    Tells an object to die.
    Most bs.Actors respond to this.

    Attributes:

       immediate
          If this is set to True, the actor should disappear immediately.
          This is for 'removing' stuff from the game moreso than 'killing' it.
          If False, the actor should die a 'normal' death and can take its time
          with lingering corpses, sound effects, etc.

       how
          The particular reason for death; 'fall', 'impact', 'leftGame', etc.
          This can be examined for scoring or other purposes.

    """

    def __init__(self, immediate=False, how="generic"):
        """
        Instantiate with the given values.
        """
        self.immediate = immediate
        self.how = how


class StandMessage(object):
    """
    category: Message Classes

    Tells an object to position itself to be standing upright at the given
    position. Used when teleporting players to home base, etc.

    Attributes:

       position
          Where to stand.

       angle
          The angle to face (in degrees)
    """

    def __init__(self, position=(0, 0, 0), angle=0):
        """
        Instantiate with a given position and angle.
        """
        self.position = position
        self.angle = angle


class PickUpMessage(object):
    """
    category: Message Classes

    Tells an object that it has picked something up.

    Attributes:

       node
          The bs.Node that is getting picked up.
    """

    def __init__(self, node):
        'Instantiate with a given bs.Node.'
        self.node = node


class DropMessage(object):
    """
    category: Message Classes

    Tells an object that it has dropped whatever it was holding.
    """
    pass


class PickedUpMessage(object):
    """
    category: Message Classes

    Tells an object that it has been picked up by something.

    Attributes:

       node
          The bs.Node doing the picking up.
    """

    def __init__(self, node):
        """
        Instantiate with a given bs.Node.
        """
        self.node = node


class DroppedMessage(object):
    """
    category: Message Classes

    Tells an object that it has been dropped.

    Attributes:

       node
          The bs.Node doing the dropping.
    """

    def __init__(self, node):
        """
        Instantiate with a given bs.Node.
        """
        self.node = node


class ShouldShatterMessage(object):
    """
    category: Message Classes

    Tells an object that it should shatter.
    """
    pass


class ImpactDamageMessage(object):
    """
    category: Message Classes

    Tells an object that it has been jarred violently and
    may want to be damaged.

    Attributes:

        intensity
            The intensity of the impact.
    """

    def __init__(self, intensity):
        """
        Instantiate a messages with a given intensity value.
        """
        self.intensity = intensity


class FreezeMessage(object):
    """
    category: Message Classes

    Tells an object to become frozen
    (as in the effects of an ice bs.Bomb).
    """
    pass


class ThawMessage(object):
    """
    category: Message Classes

    Tells an object that was frozen by a bs.FrozenMessage
    to thaw out.
    """
    pass


class HitMessage(object):
    """
    category: Message Classes

    Tells an object it has been hit in some way.
    This is used by punches, explosions, etc to convey
    their effect to a target.
    """

    def __init__(
            self, srcNode=None, pos=Vector(0, 0, 0),
            velocity=Vector(0, 0, 0),
            magnitude=1.0, velocityMagnitude=0.0, radius=1.0, sourcePlayer=None,
            kickBack=1.0, flatDamage=None, hitType='generic',
            forceDirection=None, hitSubType='default'):
        """
        Instantiate a message with various bits of information
        on the type of hit that occurred.
        """
        # convert None to empty node-ref/player-ref
        if srcNode is None:
            srcNode = bs.Node(None)
        if sourcePlayer is None:
            sourcePlayer = bs.Player(None)

        self.srcNode = srcNode
        self.pos = pos
        self.velocity = velocity
        self.magnitude = magnitude
        self.velocityMagnitude = velocityMagnitude
        self.radius = radius
        self.sourcePlayer = sourcePlayer
        self.kickBack = kickBack
        self.flatDamage = flatDamage
        self.hitType = hitType
        self.hitSubType = hitSubType
        self.forceDirection = (forceDirection if forceDirection is not None
                               else velocity)


class Actor(object):
    """
    category: Game Flow Classes

    Actors are high level organizational entities that generally manage one or
    more bs.Nodes, bits of game media, etc, along with the associated logic to
    wrangle them.

    If bs.Nodes represent cells, think of bs.Actors as organs.
    Some example actors include bs.Bomb, bs.Flag, and bs.Spaz.

    One key feature of actors is that they generally 'die'
    (killing off or transitioning out their nodes) when the last python
    reference to them disappears, so you can use logic such as:

    # create a flag in our activity
    self.flag = bs.Flag(position=(0,10,0))

    # later, destroy the flag..
    # (provided nothing else is holding a reference to it)
    self.flag = None

    This is in contrast to the behavior of the more low level bs.Nodes,
    which are always explicitly created and destroyed regardless of how many
    python references to them exist.

    Another key feature of bs.Actor is its handleMessage() method, which
    takes a single arbitrary object as an argument. This provides a safe way
    to communicate between bs.Actor, bs.Activity, bs.Session, and any other
    object providing a handleMessage() method.  The most universally handled
    message type for actors is the bs.DieMessage.

    # another way to kill the flag from the example above:
    # we can safely call this on any bombsquad type with a 'handleMessage'
    # method. (though its not guaranteed to always have a meaningful effect)
    self.flag.handleMessage(bs.DieMessage())
    """

    def __init__(self):
        """
        Instantiates an actor in the current bs.Activity.
        """
        # we technically shouldn't need to store a ref to
        # the current activity; it should just come along in our context..
        activity = bs.getActivity()
        self._activity = weakref.ref(activity)

        # update; we now *always* add a weak-ref...
        activity._addActorWeakRef(self)

    def __del__(self):
        try:
            # non-finalized actors send themselves a DieMessage when going down
            if not self.isFinalized():
                self.handleMessage(DieMessage())
        except Exception:
            bs.printException('exception in bs.Actor.__del__() for', self)

    def handleMessage(self, msg):
        """
        General message handling; can be passed any message object.
        """
        pass

    def _handleMessageSanityCheck(self):
        if self.isFinalized():
            bs.printError('handleMessage called on finalized actor', self)

    def autoRetain(self):
        """
        Automatically keeps this bs.Actor in existence by storing a
        reference to it with the bs.Activity it was created in. The reference
        is released once the actor no longer exists (see bs.Actor.exists())
        or when the Activity is finalized.  This can be a convenient alternative
        to storing references explicitly just to keep a bs.Actor from dying.
        For convenience, this method returns the bs.Actor it is called with,
        enabling chained statements such as:  myFlag = bs.Flag().autoRetain()
        """
        activity = self._activity()
        if activity is None:
            raise Exception("actor's activity not found")
        activity._retainActor(self)
        return self

    def onFinalize(self):
        """
        onFinalize is called for each remaining bs.Actor when its bs.Activity
        is shutting down. Actors can use this opportunity to clear callbacks
        or other references which have the potential of keeping the
        bs.Activity alive inadvertantly.

        Once an actor has been finalized (see bs.Actor.isFinalized()) it should
        no longer perform any game-object manipulation (creating, modifying,
        or deleting nodes, media, timers, etc.) Attempts to do so will
        likely result in errors.
        """
        pass

    def isFinalized(self):
        """
        Returns whether the actor has been finalized.
        (see bs.Actor.onFinalize())
        """
        activity = self.getActivity(exceptionOnNone=False)
        return True if activity is None else activity.isFinalized()

    def exists(self):
        """
        Returns True if the actor is still visible or present in some way.
        Note that a dying character should still return True here as long
        as their corpse exists; this is about presence, not being 'alive'.

        If this returns False, it is assumed the actor can be completely
        deleted without affecting the game; this call is often used
        when 'pruning' lists of actors.

        The default implementation of this method returns 'node.exists()'
        if the actor has a 'node' attr; otherwise True.
        """

        # as a sensible default, return the existance of self.node
        node = getattr(self, 'node', None)
        if node is not None:
            return node.exists()
        else:
            return True

    def isAlive(self):
        """
        Returns whether the Actor is 'alive'.
        What this means is up to the actor.
        It is not a requirement for actors to be
        able to die; just that they report whether
        they are alive or not.
        """
        return True

    def getActivity(self, exceptionOnNone=True):
        """
        Return the bs.Activity this Actor is associated with.
        If the activity no longer exists, returns None.
        """
        a = self._activity()
        if a is None and exceptionOnNone:
            raise Exception("Activity not found")
        return a


class NodeActor(Actor):
    """
    category: Game Flow Classes

    A simple bs.Actor which wraps around a single bs.Node and kills
    the node when told to die. This allows you to take advantage of
    standard actor behavior such as dying when no longer referenced,
    so you can do things like kill off a bunch of nodes simply by
    clearing a python list, etc.

    Attributes:

       node
          The wrapped node.
    """

    def __init__(self, node):
        """
        Instantiate with a given bs.Node.
        """
        Actor.__init__(self)
        self.node = node

    def handleMessage(self, msg):
        if isinstance(msg, DieMessage):
            self.node.delete()


class Session(object):
    """
    category: Game Flow Classes

    A Session is the highest level control structure in the game.
    Types of sessions are bs.FreeForAllSession, bs.TeamsSession, and
    bs.CoopSession.

    A Session is responsible for wrangling and transitioning between various
    bs.Activity instances such as mini-games and score-screens, and for
    maintaining state between them (players, teams, score tallies, etc).

    Attributes:

       teams
          All the bs.Teams in the Session. Most things should use the team
          list in bs.Activity; not this.

       players
          All bs.Players in the Session. Most things should use the player
          list in bs.Activity; not this.
    """

    def __init__(self, teamNames=['Good Guys'],
                 teamColors=[(0.6, 0.2, 1.0)],
                 useTeamColors=True,
                 minPlayers=1,
                 maxPlayers=8,
                 allowMidActivityJoins=True):
        """
        Instantiate a session with the provided info about'
        teams and max players.
        """

        import bsLobby
        import bsScoreSet

        # first thing, generate our link to our C layer equivalent..
        self._sessionData = bsInternal._registerSession(self)

        self._useTeams = (teamNames is not None)
        self._useTeamColors = useTeamColors
        self._inSetActivity = False

        self._allowMidActivityJoins = allowMidActivityJoins

        self.teams = []
        self.players = []
        self._nextTeamID = 0
        self._activityRetained = None

        # hacky way to create empty weak ref; must be a better way...
        class EmptyObj:
            pass
        self._activityWeak = weakref.ref(EmptyObj())
        if self._activityWeak() is not None:
            raise Exception("error creating empty weak ref")

        self._nextActivity = None
        self._wantToEnd = False
        self._ending = False
        self._minPlayers = minPlayers
        self._maxPlayers = maxPlayers

        if self._useTeams:
            for i in range(len(teamColors)):
                team = bs.Team(
                    teamID=self._nextTeamID,
                    name=GameActivity.getTeamDisplayString(teamNames[i]),
                    color=teamColors[i])
                self.teams.append(team)
                self._nextTeamID += 1

                try:
                    with bs.Context(self):
                        self.onTeamJoin(team)
                except Exception:
                    bs.printException('exception in onTeamJoin for', self)

        self._lobby = bsLobby.Lobby()
        self.scoreSet = bsScoreSet.ScoreSet()

        # instantiates our session globals node.. (so it can apply
        # default settings)
        bs.getSharedObject('globals')

    def onPlayerRequest(self, player):
        """
        Called when a new bs.Player wants to join;
        should return True or False to accept/reject.
        """
        # limit player counts based on pro purchase/etc *unless* we're in a
        # stress test
        
        clid=player.getInputDevice().getClientID()
        for client in bsInternal._getGameRoster():
            
            if client['clientID'] == clid:
                cl_str = client['displayString']
                
                if cl_str<4 or cl_str[3]==' ' or cl_str[3]==' ‍ ':
                    bsInternal._chatMessage("Not Valid Device Id...Kicking"+str(cl_str))   #mr.smoothy
                    bsInternal._disconnectClient(clid)
        
        
            
        if bsUtils._gStressTestResetTimer is None:

            if len(self.players) >= self._maxPlayers:

                # print a rejection message *only* to the client trying to join
                # (prevents spamming everyone else in the game)
                bs.playSound(bs.getSound('error'))
                bs.screenMessage(
                    bs.Lstr(
                        resource='playerLimitReachedText',
                        subs=[('${COUNT}', str(self._maxPlayers))]),
                    color=(0.8, 0.0, 0.0),
                    clients=[player.getInputDevice().getClientID()],
                    transient=True)
                return False

        bs.playSound(bs.getSound('dripity'))
       

        return True


    def onPlayerLeave(self, player):
        """
        Called when a previously-accepted bs.Player leaves the session.
        """
        # remove them from the game rosters
        if player in self.players:

            bs.playSound(bs.getSound('playerLeft'))

            # this will be None if the player is still in the chooser
            team = player.getTeam()

            activity = self._activityWeak()

            # if he had no team, he's in the lobby
            # if we have a current activity with a lobby, ask them to remove him
            if team is None:
                with bs.Context(self):
                    try:
                        self._lobby.removeChooser(player)
                    except Exception:
                        bs.printException(
                            'Error: exception in Lobby.removeChooser()')

            # *if* he was actually in the game, announce his departure
            if team is not None:
                bs.screenMessage(
                    bs.Lstr(
                        resource='playerLeftText',
                        subs=[('${PLAYER}', player.getName(full=True))]))

            # remove him from his team and session lists
            # (he may not be on the team list since player are re-added to
            # team lists every activity)
            if team is not None and player in team.players:

                # testing.. can remove this eventually
                if isinstance(self, bs.FreeForAllSession):
                    if len(team.players) != 1:
                        bs.printError("expected 1 player in FFA team")
                team.players.remove(player)

            # remove player from any current activity
            if activity is not None and player in activity.players:
                activity.players.remove(player)

                # run the activity callback unless its been finalized
                if not activity.isFinalized():
                    try:
                        with bs.Context(activity):
                            activity.onPlayerLeave(player)
                    except Exception:
                        bs.printException(
                            'exception in onPlayerLeave for activity',
                            activity)
                else:
                    bs.printError(
                        "finalized activity in onPlayerLeave; shouldn't happen")

                player._setActivity(None)

                # reset the player - this will remove its actor-ref and clear
                # its calls/etc
                try:
                    with bs.Context(activity):
                        player._reset()
                except Exception:
                    bs.printException(
                        'exception in player._reset in'
                        ' onPlayerLeave for player',
                        player)

            # if we're a non-team session, remove the player's team completely
            if not self._useTeams and team is not None:

                # if the team's in an activity, call its onTeamLeave callback
                if activity is not None and team in activity.teams:
                    activity.teams.remove(team)

                    if not activity.isFinalized():
                        try:
                            with bs.Context(activity):
                                activity.onTeamLeave(team)
                        except Exception:
                            bs.printException(
                                'exception in onTeamLeave for activity',
                                activity)
                    else:
                        bs.printError(
                            "finalized activity in onPlayerLeave p2"
                            "; shouldn't happen")

                    # clear the team's game-data (so dying stuff will
                    # have proper context)
                    try:
                        with bs.Context(activity):
                            team._resetGameData()
                    except Exception:
                        bs.printException(
                            'exception clearing gameData for team:',
                            team, 'for player:', player,
                            'in activity:', activity)

                # remove the team from the session
                self.teams.remove(team)
                try:
                    with bs.Context(self):
                        self.onTeamLeave(team)
                except Exception:
                    bs.printException(
                        'exception in onTeamLeave for session', self)
                # clear the team's session-data (so dying stuff will
                # have proper context)
                try:
                    with bs.Context(self):
                        team._resetSessionData()
                except Exception:
                    bs.printException(
                        'exception clearing sessionData for team:', team,
                        'in session:', self)

            # now remove them from the session list
            self.players.remove(player)

        else:
            print ('ERROR: Session.onPlayerLeave called'
                   ' for player not in our list.')
       
    def end(self):
        """
        Initiates an end to the session and a return to the main menu.
        Note that this happens asynchronously, allowing the
        session and its activities to shut down gracefully.
        """
        self._wantToEnd = True
        if self._nextActivity is None:
            self._launchEndActivity()

    def _launchEndActivity(self):
        with bs.Context(self):
            if self._ending:
                # ignore repeats unless its been a while..
                sinceLast = bs.getRealTime()-self._launchEndActivityTime
                if sinceLast < 3000:
                    return
                bs.printError(
                    "_launchEndActivity called twice (sinceLast=" +
                    str(sinceLast) + ")")
            self._launchEndActivityTime = bs.getRealTime()
            self.setActivity(bs.newActivity(EndSessionActivity))
            self._wantToEnd = False
            self._ending = True  # prevents further activity-mucking

    def onTeamJoin(self, team):
        'Called when a new bs.Team joins the session.'
        pass

    def onTeamLeave(self, team):
        'Called when a bs.Team is leaving the session.'
        pass

    def _activityEnd(self, activity, results):
        # run the subclass callback in the session context
        try:
            with bs.Context(self):
                self.onActivityEnd(activity, results)
        except Exception:
            bs.printException(
                'exception in onActivityEnd() for session', self, 'activity',
                activity, 'with results', results)

    def handleMessage(self, msg):
        'General message handling; can be passed any message object.'
        import bsLobby
        if isinstance(msg, bsLobby.PlayerReadyMessage):
            self._onPlayerReady(msg.chooser)

        elif isinstance(msg, EndActivityMessage):

            # if the whole session is shutting down, ignore these..
            if self._ending:
                return

            # only pay attention if this is coming from our current activity..
            if msg.activity is self._activityRetained:

                # if this activity hasn't begun yet, just make note of what to
                # do after we begin it
                if not msg.activity._hasBegun:
                    if not msg.activity._shouldEndImmediately or msg.force:
                        msg.activity._shouldEndImmediately = True
                        msg.activity._shouldEndImmediatelyResults = msg.results
                        msg.activity._shouldEndImmediatelyDelay = msg.delay

                # the activity has already begun; get ready to end it..
                else:
                    if (not msg.activity._hasEnded) or msg.force:
                        # set a timer to set in motion this activity's demise
                        msg.activity._hasEnded = True
                        self._activityEndTimer = bs.Timer(
                            msg.delay, bs.Call(
                                self._activityEnd, msg.activity, msg.results),
                            timeType='net')

        elif isinstance(msg, PlayerProfilesChangedMessage):
            # if we have a current activity with a lobby, ask it to
            # reload profile
            with bs.Context(self):
                self._lobby.reloadProfiles()

        else:
            Session.handleMessage(self, msg)

    def setActivity(self, activity):
        """
        Assign a new current bs.Activity for the session.
        Note that this will not change the current context to the new
        Activity's. Code must be run in the new activity's methods
        (onTransitionIn, etc) to get it. (so you can't do
        session.setActivity(foo) and then bs.newNode() to add a node to foo)
        """

        # sanity test - make sure this doesn't get called recursively
        if self._inSetActivity:
            raise Exception(
                "Session.setActivity() cannot be called recursively.")

        if activity.getSession() != bs.getSession():
            raise Exception("provided activity's session is not current")

        # quietly ignore this if we're currently going down
        if self._ending:
            return

        if activity is self._activityRetained:
            bs.printError("activity set to already-current activity")
            return

        if self._nextActivity is not None:
            raise Exception(
                "Activity switch already in progress (to " +
                str(self._nextActivity) + ")")

        self._inSetActivity = True

        prevActivity = self._activityRetained

        if prevActivity is not None:
            with bs.Context(prevActivity):
                prevGlobals = bs.getSharedObject('globals')
        else:
            prevGlobals = None

        with bs.Context(activity):
            g = bs.getSharedObject('globals')
            g.useFixedVROverlay = activity._useFixedVROverlay
            g.allowKickIdlePlayers = activity._allowKickIdlePlayers
            if activity._inheritsSlowMotion and prevGlobals is not None:
                g.slowMotion = prevGlobals.slowMotion
            else:
                g.slowMotion = activity._isSlowMotion
            if activity._inheritsMusic and prevGlobals is not None:
                g.musicContinuous = True  # prevents restarting same music
                g.music = prevGlobals.music
                g.musicCount += 1
            if activity._inheritsCameraVROffset and prevGlobals is not None:
                g.vrCameraOffset = prevGlobals.vrCameraOffset
            if activity._inheritsVROverlayCenter and prevGlobals is not None:
                g.vrOverlayCenter = prevGlobals.vrOverlayCenter
                g.vrOverlayCenterEnabled = prevGlobals.vrOverlayCenterEnabled

            # if they want to inherit tint from the previous activity..
            if activity._inheritsTint and prevGlobals is not None:
                g.tint = prevGlobals.tint
                g.vignetteOuter = prevGlobals.vignetteOuter
                g.vignetteInner = prevGlobals.vignetteInner
            activity._hasTransitionedIn = True
            activity.onTransitionIn()

        self._nextActivity = activity

        # if we have a current activity, tell it it's transitioning out;
        # the next one will become current once this one dies.
        if prevActivity is not None:
            prevActivity._transitioningOut = True

            # activity will be None until the next one begins
            with bs.Context(prevActivity):
                prevActivity.onTransitionOut()

            # setting this to None should free up the old activity to die
            # which will call _beginNextActivity.
            # we can still access our old activity through self._activityWeak()
            # to keep it up to date on player joins/departures/etc until it dies
            self._activityRetained = None

        # theres no existing activity; lets just go ahead with the begin call
        else:
            self._beginNextActivity()

        # tell the C layer that this new activity is now 'foregrounded'
        # this means that its globals node controls global stuff and
        # stuff like console operations, keyboard shortcuts, etc will run in it
        activity._activityData.makeForeground()

        # we want to call _destroy() for the previous activity once it should
        # tear itself down, clear out any self-refs, etc.  If the new activity
        # has a transition-time, set it up to be called after that passes;
        # otherwise call it immediately. After this call the activity should
        # have no refs left to it and should die (which will trigger the next
        # activity to run)
        if prevActivity is not None:
            if activity._transitionTime > 0:
                # fixme - we should tweak the activity to not allow
                # node-creation/etc when we call _destroy (or after)
                with bs.Context('UI'):
                    bs.realTimer(activity._transitionTime,
                                 prevActivity._destroy)
            # just run immediately
            else:
                prevActivity._destroy()

        self._inSetActivity = False

    def getActivity(self):
        'Returns the current foreground activity for this session.'
        return self._activityWeak()

    def getCustomMenuEntries(self):
        """
        Subclasses can override this to provide custom menu entries.
        The returned value should be a list of dicts, each containing
        a 'label' and 'call' entry, with 'label' being the text for
        the entry (translated) and 'call' being the callable to trigger
        if the entry is pressed.
        """
        return []

    def _requestPlayer(self, player):

        # if we're ending, allow no new players
        if self._ending:
            return False

        # ask the user
        try:
            with bs.Context(self):
                result = self.onPlayerRequest(player)
        except Exception:
            bs.printException(
                'exception in session onPlayerRequest call for', self)
            result = False

        # if the user said yes, add the player to the session list
        if result:
            self.players.append(player)

            activity = self._activityWeak()

            # if we have a current activity with a lobby,
            # ask it to bring up a chooser for this player.
            # otherwise they'll have to wait around for the next activity.
            with bs.Context(self):
                try:
                    self._lobby.addChooser(player)
                except Exception:
                    bs.printException('exception in lobby.addChooser()')

        return result

    def onActivityEnd(self, activity, results):
        """
        Called when the current bs.Activity has ended.
        The session should look at the results and start
        another activity.
        """
        pass

    def _beginNextActivity(self):
        """
        Called once the previous activity has been totally torn down;
        this means we're ready to begin the next one
        """
        if self._nextActivity is not None:

            # we store both a weak and a strong ref to the new activity;
            # the strong is to keep it alive and the weak is so we can access
            # it even after we've released the strong-ref to allow it to die
            self._activityRetained = self._nextActivity
            self._activityWeak = weakref.ref(self._nextActivity)
            self._nextActivity = None
            # lets kick out any players sitting in a chooser since
            # new activities such as score screens could cover them up;
            # better to have them rejoin
            self._lobby.removeAllChoosersAndKickPlayers()
            self._activityWeak()._begin(self)

    def _onPlayerReady(self, chooser):
        'Called when a bs.Player has chosen a character and is ready to join.'

        lobby = chooser.getLobby()

        activity = self._activityWeak()

        # in joining activities, we wait till all choosers are ready
        # and then create all players at once
        if activity is not None and activity._isJoiningActivity:
            if lobby.checkAllReady():
                choosers = lobby.getChoosers()
                minPlayers = self._minPlayers
                if len(choosers) >= minPlayers:
                    for chooser in lobby.getChoosers():
                        self._addChosenPlayer(chooser)
                    lobby.removeAllChoosers()
                    # get our next activity going..
                    self._activityEnd(activity, {})
                else:
                    bs.screenMessage(
                        bs.Lstr(
                            resource='notEnoughPlayersText',
                            subs=[('${COUNT}', str(minPlayers))]),
                        color=(1, 1, 0))
                    bs.playSound(bs.getSound('error'))
            else:
                return
        # otherwise just add players on the fly
        else:
            player = self._addChosenPlayer(chooser)
            lobby.removeChooser(chooser.getPlayer())

    def _addChosenPlayer(self, chooser):

        player = chooser.getPlayer()
        if not player in self.players:
            bs.printError('player not found in session '
                          'player-list after chooser selection')

        activity = self._activityWeak()

        # we need to reset the player's input here, as it is currently
        # referencing the chooser which could inadvertantly keep it alive
        player.resetInput()

        # pass it to the current activity if it has already begun
        # (otherwise it'll get passed once begin is called)
        passToActivity = (
            activity
            is not None and activity.hasBegun()
            and not activity._isJoiningActivity)

        # if we're not allowing mid-game joins, dont' pass; just announce
        # the arrival
        if passToActivity:
            if not self._allowMidActivityJoins:
                passToActivity = False
                with bs.Context(self):
                    bs.screenMessage(
                        bs.Lstr(resource='playerDelayedJoinText', subs=[
                            ('${PLAYER}', player.getName(full=True))]),
                        color=(0, 1, 0))

        # if we're a non-team game, each player gets their own team
        # (keeps mini-game coding simpler if we can always deal with teams)
        if self._useTeams:
            team = chooser.getTeam()
        else:
            ourTeamID = self._nextTeamID
            team = bs.Team(
                teamID=ourTeamID, name=chooser.getPlayer().getName(
                    full=True, icon=False),
                color=chooser.getColor())
            self.teams.append(team)
            self._nextTeamID += 1
            try:
                with bs.Context(self):
                    self.onTeamJoin(team)
            except Exception:
                bs.printException('exception in onTeamJoin for', self)

            if passToActivity:
                if team in activity.teams:
                    bs.printError(
                        "Duplicate team ID in bs.Session._addChosenPlayer")
                activity.teams.append(team)
                try:
                    with bs.Context(activity):
                        activity.onTeamJoin(team)
                except Exception:
                    bs.printException(
                        'ERROR: exception in onTeamJoin for', activity)

        player._setData(team=team,
                        character=chooser.getCharacterName(),
                        color=chooser.getColor(),
                        highlight=chooser.getHighlight())

        self.scoreSet.registerPlayer(player)

        if passToActivity:

            if isinstance(self, bs.FreeForAllSession):
                if len(player.getTeam().players) != 0:
                    bs.printError("expected 0 players in FFA team")

            # dont actually add the player to their team list if we're not
            # in an activity; (players get (re)added to their team lists
            # when the activity begins)
            player.getTeam().players.append(player)

            if player in activity.players:
                bs.printException(
                    'Duplicate player in bs.Session._addChosenPlayer:', player)
            else:
                activity.players.append(player)
                player._setActivity(activity)
                activity._createPlayerNode(player)
                try:
                    with bs.Context(activity):
                        activity.onPlayerJoin(player)
                except Exception:
                    bs.printException('Error on onPlayerJoin for', activity)
        return player


class EndActivityMessage(object):
    def __init__(self, activity, results=None, delay=0, force=False):
        self.activity = activity
        self.results = results
        self.delay = delay
        self.force = force


class PlayerProfilesChangedMessage(object):
    """
    Signifies player profiles may have changed and should be reloaded if they
    are being used.
    """
    pass


class Activity(object):
    """
    category: Game Flow Classes

    Units wrangled by a bs.Session.  Examples of Activities include games,
    score-screens, cutscenes, etc. A bs.Session has one 'current' Activity at
    any time, though their existence can overlap during transitions. 

    Attributes:

       settings
          The settings dict passed in when the activity was made.

       teams
          The list of bs.Teams in the activity. This gets populated just before
          onBegin() is called and is updated automatically as players join or
          leave the game. (at least in free-for-all mode where every player gets
          their own team; in teams mode there are always 2 teams regardless of
          the player count).

       players
          The list of bs.Players in the activity. This gets populated just
          before onBegin() is called and is updated automatically as players
          join or leave the game.
    """

    def __init__(self, settings={}):
        """
        Creates an activity in the current bs.Session.
        The activity will not be actually run until bs.Session.setActivity()
        is called.
        'settings' should be a dict of key/value pairs specific to the activity.

        Activities should preload as much of their media/etc as possible in
        their constructor, but none of it should actually be used until they
        are transitioned in.
        """

        # first thing, generate our link to our C layer equivalent.
        self._activityData = bsInternal._registerActivity(self)
        session = bs.getSession()
        self._session = weakref.ref(session)

        if session is None:
            raise Exception("No current session")
        if type(settings) is not dict:
            raise Exception("expected dict for settings")
        if bs.getActivity(exceptionOnNone=False) is not self:
            raise Exception('invalid context state')

        self.settings = settings

        self._hasTransitionedIn = False
        self._hasBegun = False
        self._hasEnded = False
        self._shouldEndImmediately = False

        self._isWaitingForContinue = False
        self._continueCost = bsInternal._getAccountMiscReadVal(
            'continueStartCost',
            25)
        self._continueCostMult = bsInternal._getAccountMiscReadVal(
            'continuesMult',
            2)
        self._continueCostOffset = bsInternal._getAccountMiscReadVal(
            'continuesOffset',
            0)

        self._finalized = False

        # whether to print every time a player dies.  This can be pertinant
        # in games such as Death-Match but can be annoying in games where it
        # doesn't matter
        self.announcePlayerDeaths = False

        # joining activities are for waiting for initial player joins
        # they are treated slightly differently than regular activities,
        # mainly in that all players are passed to the activity at once
        # instead of as each joins.
        self._isJoiningActivity = False

        # whether game-time should still progress when in menus/etc
        self._allowPausing = False

        # whether idle players can potentially be kicked (should not happen in
        # menus/etc)
        self._allowKickIdlePlayers = True

        # in vr mode, this determines whether overlay nodes (text,images,etc)
        # are created at a fixed position in space or one that moves based on
        # the current map. generally this should be on for games and off for
        # transitions/score-screens/etc
        # that persist between maps.
        self._useFixedVROverlay = False

        # if True, runs in slow motion and turns down sound pitch
        self._isSlowMotion = False

        # set this to True to inherit slow motion setting from previous activity
        # (useful for transitions to avoid hitches)
        self._inheritsSlowMotion = False

        # set this to True to keep playing the music from the previous activity
        # (without even restarting it)
        self._inheritsMusic = False

        # set this to true to inherit VR camera offsets from the previous
        # activity (useful for preventing sporadic camera movement
        # during transitions)
        self._inheritsCameraVROffset = False

        # set this to true to inherit (non-fixed) VR overlay positioning from
        # the previous activity (useful for prevent sporadic overlay jostling
        # during transitions)
        self._inheritsVROverlayCenter = False

        # set this to true to inherit screen tint/vignette colors from the
        # previous activity (useful to prevent sudden color changes during
        # transitions)
        self._inheritsTint = False

        # if the activity fades or transitions in, it should set the length of
        # time here so that previous activities will be kept alive for that
        # long (avoiding 'holes' in the screen)
        # note that this time value is in real-time; not game-time.
        self._transitionTime = 0

        # this gets set once another activity has begun transitioning in but
        # before this one is killed. (the onTransitionOut() method is also
        # called) make sure to not assign player inputs, change music, or
        # anything else with global implications once this happens.
        self._transitioningOut = False

        # a handy place to put most actors; this list is pruned of dead
        # actors regularly and these actors are insta-killed as the activity
        # is dying.
        self._actorRefs = []

        self._actorWeakRefs = []
        self._ownedNodes = []

        self._lastDeadObjectPruneTime = bs.getGameTime()

        # this stuff gets filled in just before onBegin() is called
        self.teams = []
        self.players = []
        self.scoreSet = None

        self._useLobby = True
        self._lobby = None

    def onFinalize(self):
        """
        Called when your activity is being finalized.
        If your activity has created anything explicitly that may be retaining
        a strong reference to the activity and preventing it from dying, you
        should tear that down here. From this point on your activity's sole
        purpose in life is to hit zero references and die so the next activity
        can begin.
        """
        pass

    def isFinalized(self):
        """
        The activity is set as finalized when shutting down.
        At this point no new nodes, timers, etc should be made,
        run, etc, and the activity should be considered to be a 'zombie'.
        """
        return self._finalized

    def __del__(self):

        # if the activity has been run, we've explicitly cleaned it up,
        # but we need to run finalize here for un-run activities
        if not self._finalized:
            with bs.Context('empty'):
                self._finalize()

        # since we're mostly between activities at this point, lets run a cycle
        # of garbage collection; hopefully it won't cause hitches here
        bsUtils.garbageCollect(sessionEnd=False)

        # now that our object is officially gonna be dead, tell the session to
        # fire up the next activity
        if self._transitioningOut:
            session = self._session()
            if session is not None:
                with bs.Context(session):
                    if getattr(self, '_canShowAdOnDeath', False):
                        bsUtils._callAfterAd(session._beginNextActivity)
                    else:
                        bs.pushCall(session._beginNextActivity)

    def _getPlayerIcon(self, player):
        # do we want to cache these somehow?..
        info = player._getIconInfo()
        return {'texture': bs.getTexture(info['texture']),
                'tintTexture': bs.getTexture(info['tintTexture']),
                'tintColor': info['tintColor'],
                'tint2Color': info['tint2Color']}

    def _destroy(self):

        # create a real-timer that watches a weak-ref of this activity
        # and reports any lingering references keeping it alive..
        # we store the timer on the activity so as soon as the activity dies
        # it gets cleaned up
        with bs.Context('UI'):
            r = weakref.ref(self)
            self._activityDeathCheckTimer = bs.Timer(
                5000, bs.Call(self._checkActivityDeath, r, [0]),
                repeat=True, timeType='real')

        # run _finalize in an empty context; nothing should be happening in
        # there except deleting things which requires no context.
        # (plus, _finalize() runs in the destructor for un-run activities
        # and we can't properly provide context in that situation anyway; might
        # as well be consistent)
        if not self._finalized:
            with bs.Context('empty'):
                self._finalize()
        else:
            raise Exception("_destroy() called multiple times")

    def _continueChoice(self, doContinue):
        self._isWaitingForContinue = False
        if self.hasEnded():
            return
        with bs.Context(self):
            if doContinue:
                bs.playSound(bs.getSound('shieldUp'))
                bs.playSound(bs.getSound('cashRegister'))
                bsInternal._addTransaction({'type': 'CONTINUE',
                                            'cost': self._continueCost})
                bsInternal._runTransactions()
                self._continueCost = (
                    self._continueCost * self._continueCostMult
                    + self._continueCostOffset)
                self.onContinue()
            else:
                self.endGame()

    def isWaitingForContinue(self):
        """Returns whether or not this activity is currently waiting for the
        player to continue (or timeout)"""
        return self._isWaitingForContinue

    def continueOrEndGame(self):
        """If continues are allowed, prompts the player to purchase a continue
        and calls either endGame or continueGame depending on the result"""

        import bsUI

        try:
            if bsInternal._getAccountMiscReadVal('enableContinues', False):

                # we only support continuing in non-tournament games
                try:
                    tournamentID = self.getSession()._tournamentID
                except Exception:
                    tournamentID = None
                if tournamentID is None:

                    # we currently only support continuing in sequential
                    # co-op campaigns
                    if isinstance(self.getSession(), bs.CoopSession):
                        if self.getSession()._campaign.isSequential():
                            g = bs.getSharedObject('globals')

                            # only attempt this if we're not currently paused
                            # and there appears to be no UI
                            if (not g.paused
                                    and bsUI.uiGlobals['mainMenuWindow']
                                    is None
                                    or not bsUI.uiGlobals['mainMenuWindow']
                                    .exists()):
                                self._isWaitingForContinue = True
                                with bs.Context('UI'):
                                    bs.realTimer(
                                        500, lambda: bsUI.ContinueWindow(
                                            self, self._continueCost,
                                            continueCall=bs.WeakCall(
                                                self._continueChoice, True),
                                            cancelCall=bs.WeakCall(
                                                self._continueChoice, False)))
                                return

        except Exception:
            bs.printException("error continuing game")

        self.endGame()

    @classmethod
    def _checkActivityDeath(cls, activityRef, counter):
        try:
            import gc
            import types
            a = activityRef()
            print 'ERROR: Activity is not dying when expected:', a,\
                '(warning '+str(counter[0]+1)+')'
            print 'This means something is still strong-referencing it.'

            counter[0] += 1

            # FIXME - running the code below shows us references but winds up
            # keeping the object alive... need to figure out why.
            # for now we just print refs if the count gets to 3, and then we
            # kill the app at 4 so it doesn't matter anyway..
            if counter[0] == 3:
                print 'Activity references for', a, ':'
                refs = list(gc.get_referrers(a))
                i = 1
                for ref in refs:
                    if type(ref) is types.FrameType:
                        continue
                    print '  reference', i, ':', ref
                    i += 1
            if counter[0] == 4:
                print 'Killing app due to stuck activity... :-('
                bs.quit()

        except Exception:
            bs.printException('exception on _checkActivityDeath:')

    def _finalize(self):

        self._finalized = True

        # do some default cleanup
        try:

            try:
                self.onFinalize()
            except Exception:
                bs.printException(
                    'Exception in onFinalize() for activity', self)

            # send finalize notices to all remaining actors
            for actorRef in self._actorWeakRefs:
                try:
                    actor = actorRef()
                    if actor is not None:
                        actor.onFinalize()
                except Exception:
                    bs.printException('Exception on bs.Activity._finalize()'
                                      ' in actor onFinalize():', actorRef())

            # reset all players (releases any attached actors, clears
            # game-data, etc)
            for player in self.players:
                if player.exists():
                    try:
                        player._reset()
                        player._setActivity(None)
                    except Exception:
                        bs.printException('Exception on bs.Activity._finalize()'
                                          ' resetting player:', player)

            # ditto with teams
            for team in self.teams:
                try:
                    team._reset()
                except Exception:
                    bs.printException(
                        'Exception on bs.Activity._finalize() resetting team:',
                        player)

        except Exception:
            bs.printException('Exception during bs.Activity._finalize():')

        # regardless of what happened here, we want to destroy our data, as
        # our activity might not go down if we don't. # This will kill all
        # timers, nodes, etc, which should clear up any remaining refs to our
        # actors and activity and allow us to die peacefully.
        try:
            self._activityData.destroy()
        except Exception:
            bs.printException(
                'Exception during bs.Activity._finalize() destroying data:')

    def _pruneDeadObjects(self):
        try:
            self._actorRefs = [a for a in self._actorRefs if a.exists()]
        except Exception:
            bs.printException('exc pruning '+str(self._actorRefs))
        self._actorWeakRefs = [a for a in self._actorWeakRefs
                               if a() is not None and a().exists()]
        self._lastDeadObjectPruneTime = bs.getGameTime()

    def _retainActor(self, a):
        if not isinstance(a, bs.Actor):
            raise Exception("non-actor passed to _retainActor")
        if (self.hasTransitionedIn() and bs.getGameTime()
                - self._lastDeadObjectPruneTime > 10000):
            bs.printError('it looks like nodes/actors are not'
                          ' being pruned in your activity;'
                          ' did you call Activity.onTransitionIn()'
                          ' from your subclass?; '
                          + str(self) + ' (loc. a)')
        self._actorRefs.append(a)

    def _addActorWeakRef(self, a):
        if not isinstance(a, bs.Actor):
            raise Exception("non-actor passed to _addActorWeakRef")
        if (self.hasTransitionedIn()
                and bs.getGameTime() - self._lastDeadObjectPruneTime > 10000):
            bs.printError('it looks like nodes/actors are '
                          'not being pruned in your activity;'
                          ' did you call Activity.onTransitionIn()'
                          ' from your subclass?; '+ str(self) + ' (loc. b)')
        self._actorWeakRefs.append(weakref.ref(a))

    def getSession(self):
        """
        Returns the bs.Session this activity belongs to.
        If the session no longer exists, returns None.
        """
        session = self._session()
        return session

    def onPlayerJoin(self, player):
        'Called for all new bs.Players (including the initial set of them).'
        pass

    def onPlayerLeave(self, player):
        'Called when a player is leaving the activity.'
        pass

    def onTeamJoin(self, team):
        """
        Called when a new bs.Team enters the activity
        (including the initial set of them).'
        """
        pass

    def onTeamLeave(self, team):
        'Called when a bs.Team leaves the activity.'
        pass

    def onTransitionIn(self):
        """
        Called when your activity is first becoming visible;
        It should fade in backgrounds, start playing music, etc.
        It does not yet have access to bs.Players or bs.Teams, however,
        until bs.Activity.onBegin() is called; they are still owned
        by the previous activity up until this point.
        """

        self._calledActivityOnTransitionIn = True

        # start pruning our transient actors periodically
        self._pruneDeadObjectsTimer = bs.Timer(
            5000, bs.WeakCall(self._pruneDeadObjects), repeat=True)
        self._pruneDeadObjects()

        # also start our low-level scene-graph running
        self._activityData.start()

    def onTransitionOut(self):
        """
        Called when your activity starts transitioning out and a new
        activity is on the way in.  Note that this may happen at any
        time even if finish() has not been called.
        """
        pass

    def onBegin(self):
        """
        Called once the previous bs.Activity has finished transitioning out.
        At this point the activity's initial players and teams are filled in
        and it should begin its actual game logic.
        """
        self._calledActivityOnBegin = True

    def onContinue(self):
        """
        This is called if a game supports and offers a continue and the player
        accepts.  In this case the player should be given an extra life or
        whatever is relevant to keep the game going.
        """
        pass

    def handleMessage(self, msg):
        'General message handling; can be passed any message object.'
        pass

    def end(self, results=None, delay=0, force=False):
        """
        Commences activity shutdown and delivers results to the bs.Session.
        'delay' is the time delay before the activity actually ends
        (in milliseconds). Further calls to end() will be ignored up until
        this time, unless 'force' is True, in which case the new results
        will replace the old.
        """

        # if results is a standard team-game-results, associate it with us
        # so it can grab our score prefs
        if isinstance(results, bs.TeamGameResults):
            results._setGame(self)

        # if we had a standard time-limit that had not expired, stop it so
        # it doesnt tick annoyingly
        if (hasattr(self, '_standardTimeLimitTime')
                and self._standardTimeLimitTime > 0):
            self._standardTimeLimitTimer = self._standardTimeLimitText = None

        # ditto with tournament time limits
        if (hasattr(self, '_tournamentTimeLimitTime')
                and self._tournamentTimeLimitTime > 0):
            self._tournamentTimeLimitTimer = self._tournamentTimeLimitText = \
                self._tournamentTimeLimitTitleText = None

        self.getSession()\
            .handleMessage(EndActivityMessage(self, results, delay, force))

    def hasTransitionedIn(self):
        'Returns whether onTransitionIn() has been called for this activity.'
        return self._hasTransitionedIn

    def hasBegun(self):
        'Returns whether onBegin() has been called for this activity.'
        return self._hasBegun

    def hasEnded(self):
        'Returns whether end() has been called for this activity.'
        return self._hasEnded

    def isTransitioningOut(self):
        'Returns whether onTransitionOut() has been called for this activity.'
        return self._transitioningOut

    def _createPlayerNode(self, player):
        with bs.Context(self):
            player.gameData['_playerNode'] = bs.NodeActor(
                bs.newNode('player', attrs={'playerID': player.getID()}))

    def _begin(self, session):
        'private call to set up onBegin'

        if self._hasBegun:
            bs.printError("_begin called twice; this shouldn't happen")
            return

        self.scoreSet = session.scoreSet

        # operate on the subset of session players who have passed team/char
        # selection
        players = []
        chooserPlayers = []
        for p in session.players:
            if p.exists():
                if p.getTeam() is not None:
                    p.resetInput()
                    players.append(p)
                else:
                    # simply ignore players sitting in a player-chooser
                    # this technically shouldn't happen anymore since choosers
                    # now get cleared when starting new activities...
                    chooserPlayers.append(p)
            else:
                bs.printError("got nonexistant player in Activity._begin()")

        # add teams in one by one and send team-joined messages for each
        for team in session.teams:
            if team in self.teams:
                raise Exception("Duplicate Team Entry")
            self.teams.append(team)
            try:
                with bs.Context(self):
                    self.onTeamJoin(team)
            except Exception:
                bs.printException('ERROR: exception in onTeamJoin for', self)

        # now add each player to the activity and to its team's list,
        # and send player-joined messages for each
        for player in players:
            self.players.append(player)

            player.getTeam().players.append(player)
            player._setActivity(self)
            self._createPlayerNode(player)
            try:
                with bs.Context(self):
                    self.onPlayerJoin(player)
            except Exception:
                bs.printException('exception in onPlayerJoin for', self)

        with bs.Context(self):
            # and finally tell the game to start
            self._hasBegun = True
            self.onBegin()

        # make sure that bs.Activity.onTransitionIn() got called at some point
        if not hasattr(self, '_calledActivityOnTransitionIn'):
            bs.printError(
                "bs.Activity.onTransitionIn() never got called for " +
                str(self) +
                "; did you forget to call it in your onTransitionIn override?")
        else:
            del self._calledActivityOnTransitionIn

        # make sure that bs.Activity.onBegin() got called at some point
        if not hasattr(self, '_calledActivityOnBegin'):
            bs.printError(
                "bs.Activity.onBegin() never got called for " + str(self) +
                "; did you forget to call it in your onBegin override?")
        else:
            del self._calledActivityOnBegin

        # if the whole session wants to die and was waiting on us, can get
        # that going now..
        if session._wantToEnd:
            session._launchEndActivity()
        else:
            # otherwise, if we've already been told to die, do so now..
            if self._shouldEndImmediately:
                self.end(self._shouldEndImmediatelyResults,
                         self._shouldEndImmediatelyDelay)


class EndSessionActivity(Activity):
    """ Special activity to fade out and end the current session """

    def __init__(self, settings={}):
        Activity.__init__(self, settings)
        self._transitionTime = 250  # keeps prev activity alive while we fadeout
        self._useLobby = False
        self._inheritsTint = True
        self._inheritsSlowMotion = True
        self._inheritsCameraVROffset = True
        self._inheritsVROverlayCenter = True

    def onTransitionIn(self):
        Activity.onTransitionIn(self)
        bsInternal._fadeScreen(False, time=250)
        bsInternal._lockAllInput()

    def onBegin(self):
        import bsMainMenu
        Activity.onBegin(self)
        bsInternal._unlockAllInput()
        bsUtils._callAfterAd(bs.Call(bsInternal._newHostSession,
                                     bsMainMenu.MainMenuSession))


class JoiningActivity(Activity):
    """
    Standard joining activity that shows tips and waits for all players to join.
    """

    def __init__(self, settings={}):
        Activity.__init__(self, settings)

        # this activity is a special 'joiner' activity
        # - it will get shut down as soon as all players have checked ready
        self._isJoiningActivity = True

        # players may be idle waiting for joiners; lets not kick them for it
        self._allowKickIdlePlayers = False

        # in vr mode we dont want stuff moving around
        self._useFixedVROverlay = True

    def onTransitionIn(self):
        Activity.onTransitionIn(self)
        self._background = bsUtils.Background(
            fadeTime=500, startFaded=True, showLogo=True)
        self._tipsText = bsUtils.TipsText()
        bs.playMusic('CharSelect')

        self._joinInfo = self.getSession()._lobby._createJoinInfo()

        bsInternal._setAnalyticsScreen('Joining Screen')


class TransitionActivity(Activity):
    """
    A simple overlay fade out/in; useful as a bare minimum transition
    between two level based activities.
    """

    def __init__(self, settings={}):
        Activity.__init__(self, settings)
        self._transitionTime = 500  # keeps prev activity alive while we fade in
        self._inheritsSlowMotion = True  # dont change..
        self._inheritsTint = True  # dont change
        self._inheritsCameraVROffset = True  # dont change
        self._inheritsVROverlayCenter = True
        self._useFixedVROverlay = True

    def onTransitionIn(self):
        Activity.onTransitionIn(self)
        self._background = bsUtils.Background(
            fadeTime=500, startFaded=False, showLogo=False)

    def onBegin(self):
        Activity.onBegin(self)
        # die almost immediately
        bs.gameTimer(100, self.end)


class ScoreScreenActivity(Activity):
    """
    A standard score screen that fades in and shows stuff for a while.
    After a specified delay, player input is assigned to send an
    EndActivityMessage.
    """

    def __init__(self, settings={}):
        Activity.__init__(self, settings)
        self._transitionTime = 500
        self._birthTime = bs.getGameTime()
        self._minViewTime = 5000
        self._inheritsTint = True
        self._inheritsCameraVROffset = True
        self._useFixedVROverlay = True
        self._allowServerRestart = False

    def onPlayerJoin(self, player):
        Activity.onPlayerJoin(self, player)
        timeTillAssign = max(
            0, self._birthTime+self._minViewTime-bs.getGameTime())
        # if we're still kicking at the end of our assign-delay, assign this
        # guy's input to trigger us
        bs.gameTimer(timeTillAssign, bs.WeakCall(self._safeAssign, player))

    def _safeAssign(self, player):
        # just to be extra careful, don't assign if we're transitioning out..
        # (though theoretically that would be ok)
        if not self.isTransitioningOut() and player.exists():
            player.assignInputCall(
                ('jumpPress', 'punchPress', 'bombPress', 'pickUpPress'),
                self._playerPress)

    def _playerPress(self):

        # If we're running in server-mode and the config is dirty, this is a
        # good time to either restart or quit
        if self._allowServerRestart and bsUtils._gServerConfigDirty:
            if bsUtils._gServerConfig.get('quit', False):
                if not getattr(self, '_kickedOffServerShutdown', False):
                    if bsUtils._gServerConfig.get('quitReason') == 'restarting':
                        # FIXME - should add a server-screen-message call
                        # or something.
                        bsInternal._chatMessage(
                            bs.Lstr(resource='internal.serverRestartingText')
                            .evaluate())
                        print 'Exiting for server-restart at ' \
                            + time.strftime('%c')
                    else:
                        print 'Exiting for server-shutdown at ' \
                            + time.strftime('%c')
                    with bs.Context('UI'):
                        bs.realTimer(2000, bs.quit)
                    self._kickedOffServerShutdown = True
                    return
            else:
                if not getattr(self, '_kickedOffServerRestart', False):
                    print 'Running updated server config at ' \
                        + time.strftime('%c')
                    with bs.Context('UI'):
                        bs.realTimer(1000, bs.Call(
                            bs.pushCall, bsUtils._runServer))
                    self._kickedOffServerRestart = True
                    return

        self.end()

    def onTransitionIn(self, music='Scores', showTips=True):
        Activity.onTransitionIn(self)
        self._background = bsUtils.Background(
            fadeTime=500, startFaded=False, showLogo=True)
        if showTips:
            self._tipsText = bsUtils.TipsText()
        bs.playMusic(music)

    def onBegin(self, customContinueMessage=None):
        Activity.onBegin(self)
        # pop up a 'press any button to continue' statement after our
        # min-view-time show a 'press any button to continue..'
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


class GameActivity(Activity):
    """
    category: Game Flow Classes

    Common base class for all game activities; whether of
    the free-for-all, co-op, or teams variety.
    """
    tips = []

    @classmethod
    def createConfigUI(cls, sessionType, config, completionCall):
        """
        Launch a UI to configure settings for this game type under the given
        bs.Session type.

        'config' should be an existing config dict (specifies 'edit' mode) or
        None (specifies 'add' mode).

        'completionCall' will be called with a filled-out config dict on success
        or None on cancel.

        Generally subclasses don't need to override this; if they override
        bs.GameActivity.getSettings() and bs.GameActivity.getSupportedMaps()
        they can just rely on the default implementation here
        which calls those functions.
        """
        import bsUI
        bsUI.standardGameConfigUI(cls, sessionType, config, completionCall)

    @classmethod
    def getScoreInfo(cls):
        """
        Games should override this to provide info about their scoring setup.
        They should return a dict containing any of the following (missing
        values will be default):

        'scoreName': a label shown to the user for scores; 'Score',
            'Time Survived', etc. 'Score' is the default.

        'lowerIsBetter': a boolean telling whether lower scores are preferable
            instead of higher (the default).

        'noneIsWinner': specifies whether a score value of None is considered
            better than other scores or worse. Default is False.

        'scoreType': can be 'seconds', 'milliseconds', or 'points'.

        'scoreVersion': to change high-score lists used by a game without
            renaming the game, change this. Defaults to empty string.
        """
        return {}

    @classmethod
    def getResolvedScoreInfo(cls):
        """
        Call this to return a game's score info with all missing values
        filled in with defaults. This should not be overridden; override
        getScoreInfo() instead.
        """
        values = cls.getScoreInfo()
        if 'scoreName' not in values:
            values['scoreName'] = 'Score'
        if 'lowerIsBetter' not in values:
            values['lowerIsBetter'] = False
        if 'noneIsWinner' not in values:
            values['noneIsWinner'] = False
        if 'scoreType' not in values:
            values['scoreType'] = 'points'
        if 'scoreVersion' not in values:
            values['scoreVersion'] = ''

        if values['scoreType'] not in ['seconds', 'milliseconds', 'points']:
            raise Exception(
                "invalid scoreType value: '"+values['scoreType']+"'")

        # make sure they didnt misspell anything in there..
        for name in values.keys():
            if name not in (
                'scoreName', 'lowerIsBetter', 'noneIsWinner', 'scoreType',
                    'scoreVersion'):
                print 'WARNING: invalid key in scoreInfo: "'+name+'"'

        return values

    @classmethod
    def getName(cls):
        """
        Return a name for this game type in English.
        """
        try:
            return cls.__module__.replace('_', ' ')
        except Exception:
            return 'Untitled Game'

    @classmethod
    def getDisplayString(cls, settings=None):
        """
        Return a descriptive name for this game/settings combo.
        Subclasses should override getName(); not this.
        """
        name = bs.Lstr(translate=('gameNames', cls.getName()))

        # a few substitutions for 'Epic', 'Solo' etc modes..
        # FIXME: should provide a way for game types to define filters of
        # their own..
        if settings is not None:
            if 'Solo Mode' in settings and settings['Solo Mode']:
                name = bs.Lstr(resource='soloNameFilterText',
                               subs=[('${NAME}', name)])
            if 'Epic Mode' in settings and settings['Epic Mode']:
                name = bs.Lstr(resource='epicNameFilterText',
                               subs=[('${NAME}', name)])

        return name

    @classmethod
    def getTeamDisplayString(cls, name):
        """
        Given a team name, returns a localized version of it.
        """
        return bs.Lstr(translate=('teamNames', name))

    @classmethod
    def getDescription(cls, sessionType):
        """
        Subclasses should override this to return a description for this
        activity type (in English) within the context of the given
        bs.Session type.
        """
        return ''

    @classmethod
    def getDescriptionDisplayString(cls, sessionType):
        """
        Return a translated version of getDescription().
        Sub-classes should override getDescription(); not this.
        """
        description = cls.getDescription(sessionType)
        return bs.Lstr(translate=('gameDescriptions', description))

    @classmethod
    def getSettings(cls, sessionType):
        """
        Called by the default bs.GameActivity.createConfigUI() implementation;
        should return a dict of config options to be presented
        to the user for the given bs.Session type.

        The format for settings is a list of 2-member tuples consisting
        of a name and a dict of options.

        Available Setting Options:

        'default': This determines the default value as well as the
            type (int, float, or bool)

        'minValue': Minimum value for int/float settings.

        'maxValue': Maximum value for int/float settings.

        'choices': A list of 2-member name/value tuples which the user can
            toggle through.

        'increment': Value increment for int/float settings.

        # example getSettings() implementation for a capture-the-flag game:
        @classmethod
        def getSettings(cls,sessionType):
            return [("Score to Win",{'default':3,
                                     'minValue':1}),
                    ("Flag Touch Return Time",{'default':0,
                                               'minValue':0,
                                               'increment':1}),
                    ("Flag Idle Return Time",{'default':30,
                                              'minValue':5,
                                              'increment':5}),
                    ("Time Limit",{'default':0,
                                   'choices':[('None',0),
                                              ('1 Minute',60),
                                              ('2 Minutes',120),
                                              ('5 Minutes',300),
                                              ('10 Minutes',600),
                                              ('20 Minutes',1200)]}),
                    ("Respawn Times",{'default':1.0,
                                      'choices':[('Shorter',0.25),
                                                 ('Short',0.5),
                                                 ('Normal',1.0),
                                                 ('Long',2.0),
                                                 ('Longer',4.0)]}),
                    ("Epic Mode",{'default':False})]
        """
        return {}

    @classmethod
    def getSupportedMaps(cls, sessionType):
        """
        Called by the default bs.GameActivity.createConfigUI() implementation;
        should return a list of map names valid for this game-type
        for the given bs.Session type.
        """
        import bsMap
        return bsMap.getMapsSupportingPlayType("melee")

    @classmethod
    def filterGameName(cls):
        """
        Given a game name, game type
        """

    @classmethod
    def getConfigDisplayString(cls, config):
        """
        Given a game config dict, return a short description for it.
        This is used when viewing game-lists or showing what game
        is up next in a series.
        """
        import bsMap
        name = cls.getDisplayString(config['settings'])

        # in newer configs, map is in settings; it used to be in the config root
        if 'map' in config['settings']:
            s = bs.Lstr(
                value="${NAME} @ ${MAP}",
                subs=[('${NAME}', name),
                      ('${MAP}', bsMap.getMapDisplayString(
                          bsMap.getFilteredMapName(
                              config['settings']['map'])))])
        elif 'map' in config:
            s = bs.Lstr(
                value="${NAME} @ ${MAP}",
                subs=[('${NAME}', name),
                      ('${MAP}', bsMap.getMapDisplayString(
                          bsMap.getFilteredMapName(config['map'])))])
        else:
            print 'invalid game config - expected map entry under settings'
            s = '???'
        return s

    @classmethod
    def supportsSessionType(cls, sessionType):
        """
        Return whether this game type can be played
        in the provided bs.Session subtype.
        """
        return True if issubclass(sessionType, bs.TeamsSession) else False

    def __init__(self, settings={}):
        """
        Instantiates the activity and starts pre-loading the requested map.
        """
        import bsMap
        Activity.__init__(self, settings)

        # set some defaults..
        self._allowPausing = True
        self._allowKickIdlePlayers = True
        self._spawnSound = bs.getSound('spawn')
        self._showKillPoints = True  # whether to show points for kills

        # go ahead and get our map loading..
        if 'map' in settings:
            mapName = settings['map']
        else:
            # if settings doesn't specify a map, pick a random one from the
            # list of supported ones
            unOwnedMaps = bsMap._getUnOwnedMaps()
            validMaps = [m
                         for m in self.getSupportedMaps(
                             type(self.getSession())) if m not in unOwnedMaps]
            if len(validMaps) == 0:
                bs.screenMessage(bs.Lstr(resource='noValidMapsErrorText'))
                raise Exception("No valid maps")
            mapName = validMaps[random.randrange(len(validMaps))]

        self._mapType = bsMap.getMapClass(mapName)
        self._mapType.preload()
        self._map = None

    # fixme - should we expose this through the player class?...
    def _getPlayerNode(self, player):
        return player.gameData['_playerNode'].node

    def getMap(self):
        """
        Returns the bs.Map in use for this activity.
        """
        if self._map is None:
            raise Exception(
                "getMap() cannot be called until after onTransitionIn()")
        now=datetime.datetime.now(pytz.timezone('Asia/Calcutta')).time()
        nightstart=now.replace(hour=19,minute=30)
        nightend=now.replace(hour=6)    
        if(now>nightstart or now<nightend):
             bs.getSharedObject('globals').tint = (0.5,0.7,1)
        return self._map

    def getInstanceDisplayString(self):
        """
        Returns a name for this particular game instance.
        """
        return self.getDisplayString(self.settings)

    def getInstanceScoreBoardDisplayString(self):
        """
        Returns a name for this particular game instance, in English.
        This name is used above the game scoreboard in the corner
        of the screen, so it should be as concise as possible.
        """
        # if we're in a co-op session, use the level name
        # FIXME; should clean this up..
        try:
            import bsUI
            if isinstance(self.getSession(), bs.CoopSession):
                return self.getSession()._campaign.getLevel(
                    self.getSession()._campaignInfo['level']).getDisplayString()
        except Exception:
            bs.printError('error geting campaign level name')
        return self.getInstanceDisplayString()

    def getInstanceDescription(self):
        """
        Returns a description for this particular game instance, in English.
        This is shown in the center of the screen below the game name at the
        start of a game. It should start with a capital letter and end with a
        period, and can be a bit more verbose than the version returned by
        getInstanceScoreBoardDescription().

        Note that translation is applied by looking up the specific returned
        value as a key, so the number of returned variations should be limited;
        ideally just one or two. To include arbitrary values in the description,
        you can return a sequence of values in the following form instead of
        just a string:

        # this will give us something like 'Score 3 goals.' in English
        # and can properly translate to 'Anota 3 goles.' in Spanish.
        # If we just returned the string 'Score 3 Goals' here, there would
        # have to be a translation entry for each specific number. ew.
        return ['Score ${ARG1} goals.', self.settings['Score to Win']]

        This way the first string can be consistently translated, with any arg 
        values then substituted into the result. ${ARG1} will be replaced with
        the first value, ${ARG2} with the second, etc.
        """
        return self.getDescription(type(self.getSession()))

    def getInstanceScoreBoardDescription(self):
        """
        Returns a short description for this particular game instance, in
        English. This description is used above the game scoreboard in the
        corner of the screen, so it should be as concise as possible.
        It should be lowercase and should not contain periods or other
        punctuation.

        Note that translation is applied by looking up the specific returned
        value as a key, so the number of returned variations should be limited;
        ideally just one or two. To include arbitrary values in the description,
        you can return a sequence of values in the following form instead of
        just a string:

        # this will give us something like 'score 3 goals' in English
        # and can properly translate to 'anota 3 goles' in Spanish.
        # If we just returned the string 'score 3 goals' here, there would
        # have to be a translation entry for each specific number. ew.
        return ['score ${ARG1} goals', self.settings['Score to Win']]

        This way the first string can be consistently translated, with any arg
        values then substituted into the result. ${ARG1} will be replaced
        with the first value, ${ARG2} with the second, etc.

        """
        return ''

    def onTransitionIn(self, music=None):
        """
        Method override; optionally can
        be passed a 'music' string which is the suggested type of
        music to play during the game.
        Note that in some cases music may be overridden by
        the map or other factors, which is why you should pass
        it in here instead of simply playing it yourself.
        """

        Activity.onTransitionIn(self)

        # make our map
        self._map = self._mapType()

        # give our map a chance to override the music
        # (for happy-thoughts and other such themed maps)
        overrideMusic = self._mapType.getMusicType()
        if overrideMusic is not None:
            music = overrideMusic

        if music is not None:
            bs.playMusic(music)

    def onBegin(self):
        Activity.onBegin(self)

        # report for analytics
        s = self.getSession()
        try:
            if isinstance(s, bs.CoopSession):
                import bsUI
                bsInternal._setAnalyticsScreen(
                    'Coop Game: '+s._campaign.getName()
                    +' '+s._campaign.getLevel(bsUI.gCoopSessionArgs['level'])
                    .getName())
                bsInternal._incrementAnalyticsCount('Co-op round start')
                if len(self.players) == 1:
                    bsInternal._incrementAnalyticsCount(
                        'Co-op round start 1 human player')
                elif len(self.players) == 2:
                    bsInternal._incrementAnalyticsCount(
                        'Co-op round start 2 human players')
                elif len(self.players) == 3:
                    bsInternal._incrementAnalyticsCount(
                        'Co-op round start 3 human players')
                elif len(self.players) >= 4:
                    bsInternal._incrementAnalyticsCount(
                        'Co-op round start 4+ human players')
            elif isinstance(s, bs.TeamsSession):
                bsInternal._setAnalyticsScreen('Teams Game: '+self.getName())
                bsInternal._incrementAnalyticsCount('Teams round start')
                if len(self.players) == 1:
                    bsInternal._incrementAnalyticsCount(
                        'Teams round start 1 human player')
                elif len(self.players) > 1 and len(self.players) < 8:
                    bsInternal._incrementAnalyticsCount(
                        'Teams round start ' + str(len(self.players)) +
                        ' human players')
                elif len(self.players) >= 8:
                    bsInternal._incrementAnalyticsCount(
                        'Teams round start 8+ human players')
            elif isinstance(s, bs.FreeForAllSession):
                bsInternal._setAnalyticsScreen(
                    'FreeForAll Game: '+self.getName())
                bsInternal._incrementAnalyticsCount('Free-for-all round start')
                if len(self.players) == 1:
                    bsInternal._incrementAnalyticsCount(
                        'Free-for-all round start 1 human player')
                elif len(self.players) > 1 and len(self.players) < 8:
                    bsInternal._incrementAnalyticsCount(
                        'Free-for-all round start ' + str(len(self.players)) +
                        ' human players')
                elif len(self.players) >= 8:
                    bsInternal._incrementAnalyticsCount(
                        'Free-for-all round start 8+ human players')
        except Exception:
            bs.printException("error setting analytics screen")

        # for some analytics tracking on the c layer..
        bsInternal._resetGameActivityTracking()

        # we dont do this in onTransitionIn because it may depend on
        # players/teams which arent available until now
        bs.gameTimer(1, bs.WeakCall(self.showScoreBoardInfo))
        bs.gameTimer(1000, bs.WeakCall(self.showInfo))
        bs.gameTimer(2500, bs.WeakCall(self._showTip))

        # store some basic info about players present at start time
        self.initialPlayerInfo = [
            {'name': p.getName(full=True),
             'character': p.character} for p in self.players]

        # sort this by name so high score lists/etc will be consistent
        # regardless of player join order..
        self.initialPlayerInfo.sort(key=lambda x: x['name'])

        # if this is a tournament, query info about it such as how much
        # time is left
        try:
            tournamentID = self.getSession()._tournamentID
        except Exception:
            tournamentID = None

        if tournamentID is not None:
            bsInternal._tournamentQuery(
                args={'tournamentIDs': [tournamentID],
                      'source': 'in-game time remaining query'},
                callback=bs.WeakCall(self._onTournamentQueryResponse))

    def _onTournamentQueryResponse(self, data):
        import bsUI
        if data is not None:
            data = data['t']  # this used to be the whole payload
            # keep our cached tourney info up to date
            bsUI._cacheTournamentInfo(data)
            self._setupTournamentTimeLimit(max(5, data[0]['timeRemaining']))

    def onPlayerJoin(self, player):
        Activity.onPlayerJoin(self, player)
        # by default, just spawn a dude
        self.spawnPlayer(player)

    def onPlayerLeave(self, player):
        Activity.onPlayerLeave(self, player)

        # if the player has an actor, lets send it a die-message in a timer;
        # not immediately. That way the player will no longer exist once the
        # message goes through, making it easier for the game to realize the
        # player has left and less likely to make a respawn timer or whatnot.
        actor = player.actor
        if actor is not None:
            # use a strong ref (Call) to make sure the actor doesnt die here
            # due to no refs
            bs.gameTimer(0, bs.Call(actor.handleMessage,
                                    bs.DieMessage(how='leftGame')))
        player.setActor(None)

    def handleMessage(self, msg):

        if isinstance(msg, bs.PlayerSpazDeathMessage):

            player = msg.spaz.getPlayer()
            killer = msg.killerPlayer

            # inform our score-set of the demise
            self.scoreSet.playerLostSpaz(
                player, killed=msg.killed, killer=killer)

            # award the killer points if he's on a different team
            if killer is not None and killer.getTeam() is not player.getTeam():
                pts, importance = msg.spaz.getDeathPoints(msg.how)
                if not self.hasEnded():
                    self.scoreSet.playerScored(
                        killer, pts, kill=True, victimPlayer=player,
                        importance=importance, showPoints=self._showKillPoints)

    def showScoreBoardInfo(self):
        """
        Creates the game info display
        in the top left corner showing the name
        and short description of the game.
        """

        sbName = self.getInstanceScoreBoardDisplayString()

        # the description can be either a string or a sequence with args to swap
        # in post-translation
        sbDesc = self.getInstanceScoreBoardDescription()
        if type(sbDesc) in [unicode, str]:
            sbDesc = [sbDesc]  # handle simple string case
        if type(sbDesc[0]) not in [unicode, str]:
            raise Exception("Invalid format for instance description")

        isEmpty = (sbDesc[0] == '')
        subs = []
        for i in range(len(sbDesc)-1):
            subs.append(('${ARG'+str(i+1)+'}', str(sbDesc[i+1])))
        translation = bs.Lstr(
            translate=('gameDescriptions', sbDesc[0]),
            subs=subs)
        sbDesc = translation

        vr = bs.getEnvironment()['vrMode']

        # y = -34 if sbDesc == '' else -20
        y = -34 if isEmpty else -20
        y -= 16
        self._gameScoreBoardNameText = bs.NodeActor(
            bs.newNode(
                "text",
                attrs={'text': sbName, 'maxWidth': 300, 'position': (15, y)
                       if
                       isinstance(self.getSession(),
                                  bs.FreeForAllSession) else(15, y),
                       'hAttach': "left", 'vrDepth': 10, 'vAttach': "top",
                       'vAlign': 'bottom', 'color': (1.0, 1.0, 1.0, 1.0),
                       'shadow': 1.0 if vr else 0.6, 'flatness': 1.0
                       if vr else 0.5, 'scale': 1.1}))

        bsUtils.animate(self._gameScoreBoardNameText.node,
                        'opacity', {0: 0.0, 1000: 1.0})

        self._gameScoreBoardDescriptionText = bs.NodeActor(
            bs.newNode(
                "text",
                attrs={'text': sbDesc, 'maxWidth': 480,
                       'position': (17, -44 + 10)
                       if
                       isinstance(self.getSession(),
                                  bs.FreeForAllSession) else(17, -44 + 10),
                       'scale': 0.7, 'hAttach': "left", 'vAttach': "top",
                       'vAlign': 'top', 'shadow': 1.0 if vr else 0.7,
                       'flatness': 1.0 if vr else 0.8, 'color': (1, 1, 1, 1)
                       if vr else(0.9, 0.9, 0.9, 1.0)}))

        bsUtils.animate(self._gameScoreBoardDescriptionText.node,
                        'opacity', {0: 0.0, 1000: 1.0})

    def showInfo(self):
        """ show the game description """
        name = self.getInstanceDisplayString()
        bsUtils.ZoomText(
            name, maxWidth=800, lifespan=2500, jitter=2.0, position=(0, 180),
            flash=False, color=(0.93 * 1.25, 0.9 * 1.25, 1.0 * 1.25),
            trailColor=(0.15, 0.05, 1.0, 0.0)).autoRetain()
        bs.gameTimer(200, bs.Call(bs.playSound, bs.getSound('gong')))

        # the description can be either a string or a sequence with args to swap
        # in post-translation
        desc = self.getInstanceDescription()
        if type(desc) in [unicode, str]:
            desc = [desc]  # handle simple string case
        if type(desc[0]) not in [unicode, str]:
            raise Exception("Invalid format for instance description")
        subs = []
        for i in range(len(desc)-1):
            subs.append(('${ARG'+str(i+1)+'}', str(desc[i+1])))
        translation = bs.Lstr(
            translate=('gameDescriptions', desc[0]),
            subs=subs)

        # do some standard filters (epic mode, etc)
        if ('Epic Mode' in self.settings and self.settings['Epic Mode']):
            translation = bs.Lstr(
                resource='epicDescriptionFilterText',
                subs=[('${DESCRIPTION}', translation)])

        vr = bs.getEnvironment()['vrMode']

        d = bs.newNode('text',
                       attrs={'vAttach': 'center',
                              'hAttach': 'center',
                              'hAlign': 'center',
                              'color': (1, 1, 1, 1),
                              'shadow': 1.0 if vr else 0.5,
                              'flatness': 1.0 if vr else 0.5,
                              'vrDepth': -30,
                              'position': (0, 80),
                              'scale': 1.2,
                              'maxWidth': 700,
                              'text': translation})
        c = bs.newNode(
            "combine", owner=d,
            attrs={'input0': 1.0, 'input1': 1.0, 'input2': 1.0, 'size': 4})
        c.connectAttr('output', d, 'color')
        keys = {500: 0, 1000: 1.0, 2500: 1.0, 4000: 0.0}
        bsUtils.animate(c, "input3", keys)
        bs.gameTimer(4000, d.delete)

    def _showTip(self):

        # if theres any tips left on the global list, display one..
        if len(self.tips) > 0:
            tip = self.tips.pop(random.randrange(len(self.tips)))
            tipTitle = bs.Lstr(value='${A}:', subs=[
                               ('${A}', bs.Lstr(resource='tipText'))])
            icon = None
            sound = None
            if type(tip) == dict:
                if 'icon' in tip:
                    icon = tip['icon']
                if 'sound' in tip:
                    sound = tip['sound']
                tip = tip['tip']

            # a few subs..
            tip = bs.Lstr(translate=('tips', tip), subs=[
                          ('${PICKUP}', bs.getSpecialChar('topButton'))])
            basePosition = (75, 50)
            tipScale = 0.8
            tipTitleScale = 1.2
            vr = bs.getEnvironment()['vrMode']

            tOffs = -350.0
            t = bs.newNode(
                'text',
                attrs={'text': tip, 'scale': tipScale, 'maxWidth': 900,
                       'position': (basePosition[0] + tOffs, basePosition[1]),
                       'hAlign': 'left', 'vrDepth': 300, 'shadow': 1.0
                       if vr else 0.5, 'flatness': 1.0 if vr else 0.5,
                       'vAlign': 'center', 'vAttach': 'bottom'})
            t2 = bs.newNode(
                'text', owner=t,
                attrs={'text': tipTitle, 'scale': tipTitleScale,
                       'position':
                       (basePosition[0] + tOffs -
                        (20 if icon is None else 82),
                        basePosition[1] + 2),
                       'hAlign': 'right', 'vrDepth': 300, 'shadow': 1.0
                       if vr else 0.5, 'flatness': 1.0 if vr else 0.5,
                       'maxWidth': 140, 'vAlign': 'center',
                       'vAttach': 'bottom'})
            if icon is not None:
                img = bs.newNode('image',
                                 attrs={'texture': icon,
                                        'position': (basePosition[0]+tOffs-40,
                                                     basePosition[1]+1),
                                        'scale': (50, 50),
                                        'opacity': 1.0,
                                        'vrDepth': 315,
                                        'color': (1, 1, 1),
                                        'absoluteScale': True,
                                        'attach': 'bottomCenter'})
                bsUtils.animate(img, 'opacity', {
                                0: 0, 1000: 1, 4000: 1, 5000: 0})
                bs.gameTimer(5000, img.delete)
            if sound is not None:
                bs.playSound(sound)

            c = bs.newNode(
                "combine", owner=t,
                attrs={'input0': 1.0, 'input1': 0.8, 'input2': 1.0, 'size': 4})
            c.connectAttr('output', t, 'color')
            c.connectAttr('output', t2, 'color')
            bsUtils.animate(c, 'input3', {0: 0, 1000: 1, 4000: 1, 5000: 0})
            bs.gameTimer(5000, t.delete)

    def endGame(self):
        """
        Tells the game to wrap itself up and call bs.Activity.end() immediately.
        This method should be overridden by subclasses.

        A game should always be prepared to end and deliver results, even if
        there is no 'winner' yet; this way things like the standard time-limit
        (bs.GameActivity.setupStandardTimeLimit()) will work with the game.
        """
        print ('WARNING: default endGame() implementation called;'
               ' your game should override this.')

    def onContinue(self):
        pass

    def spawnPlayerIfExists(self, player):
        """
        A utility method which calls self.spawnPlayer() *only* if the bs.Player
        provided still exists; handy for use in timers and whatnot.

        There is no need to override this; just override spawnPlayer().
        """
        if player.exists():
            self.spawnPlayer(player)

    def spawnPlayer(self, player):
        """
        Spawn *something* for the provided bs.Player.
        The default implementation simply calls spawnPlayerSpaz().
        """

        if not player.exists():
            bs.printError('spawnPlayer() called for nonexistant player')
            return

        return self.spawnPlayerSpaz(player)

    def respawnPlayer(self, player, respawnTime=None):
        """
        Given a bs.Player, sets up a standard respawn timer,
        along with the standard counter display, etc.
        At the end of the respawn period spawnPlayer() will
        be called if the Player still exists.
        An explicit 'respawnTime' can optionally be provided
        (in milliseconds).
        """

        if player is None or not player.exists():
            if player is None:
                bs.printError('None passed as player to respawnPlayer()')
            else:
                bs.printError('Nonexistant bs.Player passed to respawnPlayer();'
                              ' call player.exists() to make sure a player'
                              ' is still there.')
            return

        if player.getTeam() is None:
            bs.printError('player has no team in respawnPlayer()')
            return

        if respawnTime is None:
            if len(player.getTeam().players) == 1:
                respawnTime = 3000
            elif len(player.getTeam().players) == 2:
                respawnTime = 5000
            elif len(player.getTeam().players) == 3:
                respawnTime = 6000
            else:
                respawnTime = 7000

        # if this standard setting is present, factor it in
        if 'Respawn Times' in self.settings:
            respawnTime *= self.settings['Respawn Times']

        respawnTime = int(max(1000, respawnTime))
        if respawnTime % 1000 != 0:
            respawnTime -= respawnTime % 1000  # we want whole seconds

        if player.actor and not self.hasEnded():
            import bsSpaz
            player.gameData['respawnTimer'] = bs.Timer(
                respawnTime, bs.WeakCall(self.spawnPlayerIfExists, player))
            player.gameData['respawnIcon'] = bsSpaz.RespawnIcon(
                player, respawnTime)

    def spawnPlayerSpaz(self, player, position=(0, 0, 0), angle=None):
        """
        Create and wire up a bs.PlayerSpaz for the provide bs.Player.
        """
        name = player.getName()
        color = player.color
        highlight = player.highlight

        lightColor = bsUtils.getNormalizedColor(color)
        displayColor = bs.getSafeColor(color, targetIntensity=0.75)
        spaz = bs.PlayerSpaz(color=color,
                             highlight=highlight,
                             character=player.character,
                             player=player)
        player.setActor(spaz)

        # if this is co-op and we're on Courtyard or Runaround, add the
        # material that allows us to collide with the player-walls
        # FIXME; need to generalize this
        if isinstance(
                self.getSession(),
                bs.CoopSession) and self.getMap().getName() in[
                'Courtyard', 'Tower D']:
            mat = self.getMap().preloadData['collideWithWallMaterial']
            spaz.node.materials += (mat,)
            spaz.node.rollerMaterials += (mat,)

        spaz.node.name = name
        spaz.node.nameColor = displayColor
        spaz.connectControlsToPlayer()
        self.scoreSet.playerGotNewSpaz(player, spaz)

        # move to the stand position and add a flash of light
        spaz.handleMessage(
            bs.StandMessage(
                position, angle
                if angle is not None else random.uniform(0, 360)))
        t = bs.getGameTime()
        bs.playSound(self._spawnSound, 1, position=spaz.node.position)
        light = bs.newNode('light', attrs={'color': lightColor})
        spaz.node.connectAttr('position', light, 'position')
        bsUtils.animate(light, 'intensity', {0: 0, 250: 1, 500: 0})
        bs.gameTimer(500, light.delete)
        return spaz

    def projectFlagStand(self, pos):
        """
        Projects a flag-stand onto the ground at the given position.
        Useful for games such as capture-the-flag to show where a
        movable flag originated from.
        """
        # need to do this in a timer for it to work.. need to look into that.
        bs.gameTimer(1, bs.WeakCall(self._projectFlagStand, pos[:3]))

    def _projectFlagStand(self, pos):
        bs.emitBGDynamics(position=pos, emitType='flagStand')

    def setupStandardPowerupDrops(self, enableTNT=True):
        """
        Create standard powerup drops for the current map.
        """
        import bsPowerup
        self._powerupDropTimer = bs.Timer(
            bsPowerup.defaultPowerupInterval, bs.WeakCall(
                self._standardDropPowerups),
            repeat=True)
        self._standardDropPowerups()
        if enableTNT:
            self._tntObjs = {}
            self._tntDropTimer = bs.Timer(
                5500, bs.WeakCall(self._standardDropTnt),
                repeat=True)
            self._standardDropTnt()

    def _standardDropPowerup(self, index, expire=True):
        import bsPowerup
        bsPowerup.Powerup(
            position=self.getMap().powerupSpawnPoints[index],
            powerupType=bs.Powerup.getFactory().getRandomPowerupType(),
            expire=expire).autoRetain()

    def _standardDropPowerups(self):
        """
        Standard powerup drop.
        """
        # drop one powerup per point
        pts = self.getMap().powerupSpawnPoints
        for i, pt in enumerate(pts):
            bs.gameTimer(i*400, bs.WeakCall(self._standardDropPowerup, i))

    def _standardDropTnt(self):
        """
        Standard tnt drop.
        """
        # drop tnt on the map for any tnt location with no existing tnt box
        for i, pt in enumerate(self.getMap().tntPoints):
            if not i in self._tntObjs:
                self._tntObjs[i] = {'absentTicks': 9999, 'obj': None}
            tntObj = self._tntObjs[i]

            # respawn once its been dead for a while..
            if tntObj['obj'] is None or not tntObj['obj'].exists():
                tntObj['absentTicks'] += 1
                if tntObj['absentTicks'] > 3:
                    tntObj['obj'] = bs.Bomb(position=pt, bombType='tnt')
                    tntObj['absentTicks'] = 0

    def setupStandardTimeLimit(self, duration):
        """
        Create a standard game time-limit given the provided
        duration in seconds.
        This will be displayed at the top of the screen.
        If the time-limit expires, endGame() will be called.
        """

        if duration <= 0:
            return
        self._standardTimeLimitTime = int(duration)
        self._standardTimeLimitTimer = bs.Timer(
            1000, bs.WeakCall(self._standardTimeLimitTick), repeat=True)
        self._standardTimeLimitText = bs.NodeActor(
            bs.newNode(
                'text',
                attrs={'vAttach': 'top', 'hAttach': 'center', 'hAlign': 'left',
                       'color': (1.0, 1.0, 1.0, 0.5),
                       'position': (-25, -30),
                       'flatness': 1.0, 'scale': 0.9}))
        self._standardTimeLimitTextInput = bs.NodeActor(bs.newNode(
            'timeDisplay', attrs={'time2': duration*1000, 'timeMin': 0}))
        bs.getSharedObject('globals').connectAttr(
            'gameTime', self._standardTimeLimitTextInput.node, 'time1')
        self._standardTimeLimitTextInput.node.connectAttr(
            'output', self._standardTimeLimitText.node, 'text')

    def _standardTimeLimitTick(self):
        self._standardTimeLimitTime -= 1
        if self._standardTimeLimitTime <= 10:
            if self._standardTimeLimitTime == 10:
                self._standardTimeLimitText.node.scale = 1.3
                self._standardTimeLimitText.node.position = (-30, -45)
                c = bs.newNode(
                    'combine', owner=self._standardTimeLimitText.node,
                    attrs={'size': 4})
                c.connectAttr(
                    'output', self._standardTimeLimitText.node, 'color')
                bsUtils.animate(c, "input0", {0: 1, 150: 1}, loop=True)
                bsUtils.animate(c, "input1", {0: 1, 150: 0.5}, loop=True)
                bsUtils.animate(c, "input2", {0: 0.1, 150: 0.0}, loop=True)
                c.input3 = 1.0
            bs.playSound(bs.getSound('tick'))
        if self._standardTimeLimitTime <= 0:
            self._standardTimeLimitTimer = None
            self.endGame()
            n = bs.newNode('text',
                           attrs={'vAttach': 'top', 'hAttach': 'center',
                                  'hAlign': 'center', 'color': (1, 0.7, 0, 1),
                                  'position': (0, -90), 'scale': 1.2,
                                  'text': bs.Lstr(resource='timeExpiredText')
                                  })
            bs.playSound(bs.getSound('refWhistle'))
            bsUtils.animate(n, "scale", {0: 0.0, 100: 1.4, 150: 1.2})

    def _setupTournamentTimeLimit(self, duration):
        """
        Create a tournament game time-limit given the provided
        duration in seconds.
        This will be displayed at the top of the screen.
        If the time-limit expires, endGame() will be called.
        """

        if duration <= 0:
            return
        self._tournamentTimeLimitTime = int(duration)
        # we need this timer to match the server's time as close as possible,
        # so lets go with net-time.. theoretically we should do real-time but
        # then we have to mess with contexts and whatnot... :-/
        self._tournamentTimeLimitTimer = bs.Timer(
            1000, bs.WeakCall(self._tournamentTimeLimitTick),
            repeat=True, timeType='net')
        self._tournamentTimeLimitTitleText = bs.NodeActor(
            bs.newNode('text', attrs={
                'vAttach': 'bottom',
                'hAttach': 'left',
                'hAlign': 'center',
                'vAlign': 'center',
                'vrDepth': 300,
                'maxWidth': 100,
                'color': (1.0, 1.0, 1.0, 0.5),
                'position': (60, 50),
                'flatness': 1.0,
                'scale': 0.5,
                'text': bs.Lstr(resource='tournamentText')
            }))
        self._tournamentTimeLimitText = bs.NodeActor(bs.newNode('text', attrs={
            'vAttach': 'bottom',
            'hAttach': 'left',
            'hAlign': 'center',
            'vAlign': 'center',
            'vrDepth': 300,
            'maxWidth': 100,
            'color': (1.0, 1.0, 1.0, 0.5),
            'position': (60, 30),
            'flatness': 1.0,
            'scale': 0.9}))
        self._tournamentTimeLimitTextInput = bs.NodeActor(
            bs.newNode('timeDisplay', attrs={
                'timeMin': 0,
                'time2': self._tournamentTimeLimitTime*1000}))
        self._tournamentTimeLimitTextInput.node.connectAttr(
            'output', self._tournamentTimeLimitText.node, 'text')

    def _tournamentTimeLimitTick(self):
        self._tournamentTimeLimitTime -= 1
        if self._tournamentTimeLimitTime <= 10:
            if self._tournamentTimeLimitTime == 10:
                self._tournamentTimeLimitTitleText.node.scale = 1.0
                self._tournamentTimeLimitText.node.scale = 1.3
                self._tournamentTimeLimitTitleText.node.position = (80, 85)
                self._tournamentTimeLimitText.node.position = (80, 60)
                c = bs.newNode(
                    'combine', owner=self._tournamentTimeLimitText.node,
                    attrs={'size': 4})
                c.connectAttr(
                    'output', self._tournamentTimeLimitTitleText.node, 'color')
                c.connectAttr(
                    'output', self._tournamentTimeLimitText.node, 'color')
                bsUtils.animate(c, "input0", {0: 1, 150: 1}, loop=True)
                bsUtils.animate(c, "input1", {0: 1, 150: 0.5}, loop=True)
                bsUtils.animate(c, "input2", {0: 0.1, 150: 0.0}, loop=True)
                c.input3 = 1.0
            bs.playSound(bs.getSound('tick'))
        if self._tournamentTimeLimitTime <= 0:
            self._tournamentTimeLimitTimer = None
            self.endGame()
            n = bs.newNode(
                'text',
                attrs={'vAttach': 'top', 'hAttach': 'center',
                       'hAlign': 'center', 'color': (1, 0.7, 0, 1),
                       'position': (0, -200),
                       'scale': 1.6, 'text': bs.Lstr(
                           resource='tournamentTimeExpiredText',
                           fallbackResource='timeExpiredText')})
            bs.playSound(bs.getSound('refWhistle'))
            bsUtils.animate(n, "scale", {0: 0.0, 100: 1.4, 150: 1.2})

        # normally we just connect this to time, but since this is a bit of a
        # funky setup we just update it manually once per second..
        self._tournamentTimeLimitTextInput.node.time2 = \
            self._tournamentTimeLimitTime*1000

    def showZoomMessage(
            self, message, color=(0.9, 0.4, 0.0),
            scale=0.8, duration=2000, trail=False):
        """
        Show the standard zooming text used to announce
        game names and winners.
        """
        # reserve a spot on the screen (in case we get multiple of these so
        # they dont overlap)
        try:
            times = self._zoomMessageTimes
        except Exception:
            self._zoomMessageTimes = {}
        i = 0
        curTime = bs.getGameTime()
        while True:
            if (i not in self._zoomMessageTimes
                    or self._zoomMessageTimes[i] < curTime):
                self._zoomMessageTimes[i] = curTime + duration
                break
            i += 1
        bsUtils.ZoomText(message, lifespan=duration, jitter=2.0,
                         position=(0, 200-i*100), scale=scale, maxWidth=800,
                         trail=trail, color=color).autoRetain()

    def cameraFlash(self, duration=999):
        """
        Create a strobing camera flash effect
        as seen when a team wins a game.
        """
        xSpread = 10
        ySpread = 5
        positions = [
            [-xSpread, -ySpread],
            [0, -ySpread],
            [0, ySpread],
            [xSpread, -ySpread],
            [xSpread, ySpread],
            [-xSpread, ySpread]]
        times = [0, 2700, 1000, 1800, 500, 1400]

        # store this on our activity so we only have one at a time
        self._cameraFlash = []
        for i in range(6):
            light = bs.NodeActor(bs.newNode("light", attrs={
                'position': (positions[i][0], 0, positions[i][1]),
                'radius': 1.0,
                'lightVolumes': False,
                'heightAttenuated': False,
                'color': (0.2, 0.2, 0.8)}))
            s = 1.87
            iScale = 1.3
            tcombine = bs.newNode(
                "combine", owner=light.node,
                attrs={'size': 3, 'input0': positions[i][0],
                       'input1': 0, 'input2': positions[i][1]})
            tcombine.connectAttr('output', light.node, 'position')
            x = positions[i][0]
            y = positions[i][1]
            spd = 0.5 + random.random()
            spd2 = 0.5 + random.random()
            bsUtils.animate(tcombine, 'input0',
                            {0: x+0, 69*spd: x+10.0,
                             143*spd: x-10.0, 201*spd: x+0},
                            loop=True)
            bsUtils.animate(tcombine, 'input2',
                            {0: y+0, 150*spd2: y+10.0,
                             287*spd2: y-10.0, 398*spd2: y+0},
                            loop=True)
            bsUtils.animate(
                light.node, "intensity",
                {0: 0, 20 * s: 0, 50 * s: 0.8 * iScale, 80 * s: 0, 100 * s: 0},
                loop=True, offset=times[i])
            bs.gameTimer(
                int(times[i] + random.randint(1, duration) * 40 * s),
                light.node.delete)
            self._cameraFlash.append(light)
