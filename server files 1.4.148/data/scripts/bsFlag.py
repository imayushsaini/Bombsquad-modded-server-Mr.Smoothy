import bs


class FlagFactory(object):
    """
    category: Game Flow Classes

    Wraps up media and other resources used by bs.Flags.
    A single instance of this is shared between all flags
    and can be retrieved via bs.Flag.getFactory().

    Attributes:

       flagMaterial
          The bs.Material applied to all bs.Flags.

       impactSound
          The bs.Sound used when a bs.Flag hits the ground.

       skidSound
          The bs.Sound used when a bs.Flag skids along the ground.

       noHitMaterial
          A bs.Material that prevents contact with most objects;
          applied to 'non-touchable' flags.

       flagTexture
          The bs.Texture for flags.
    """

    def __init__(self):
        """
        Instantiate a FlagFactory.
        You shouldn't need to do this; call bs.Flag.getFactory() to get
        a shared instance.
        """

        self.flagMaterial = bs.Material()
        self.flagMaterial.addActions(
            conditions=(('weAreYoungerThan', 100),
                        'and',
                        ('theyHaveMaterial', bs.getSharedObject(
                            'objectMaterial'))),
            actions=(('modifyNodeCollision', 'collide', False)))

        self.flagMaterial.addActions(
            conditions=('theyHaveMaterial',
                        bs.getSharedObject('footingMaterial')),
            actions=(('message', 'ourNode', 'atConnect', 'footing', 1),
                     ('message', 'ourNode', 'atDisconnect', 'footing', -1)))

        self.impactSound = bs.getSound('metalHit')
        self.skidSound = bs.getSound('metalSkid')
        self.flagMaterial.addActions(
            conditions=('theyHaveMaterial',
                        bs.getSharedObject('footingMaterial')),
            actions=(('impactSound', self.impactSound, 2, 5),
                     ('skidSound', self.skidSound, 2, 5)))

        self.noHitMaterial = bs.Material()
        self.noHitMaterial.addActions(
            conditions=(('theyHaveMaterial',
                         bs.getSharedObject('pickupMaterial')), 'or',
                        ('theyHaveMaterial',
                         bs.getSharedObject('attackMaterial'))),
            actions=(('modifyPartCollision', 'collide', False)))

        # we also dont want anything moving it
        self.noHitMaterial.addActions(
            conditions=(('theyHaveMaterial',
                         bs.getSharedObject('objectMaterial')), 'or',
                        ('theyDontHaveMaterial',
                         bs.getSharedObject('footingMaterial'))),
            actions=(('modifyPartCollision', 'collide', False),
                     ('modifyPartCollision', 'physical', False)))

        self.flagTexture = bs.getTexture('flagColor')


class FlagPickedUpMessage(object):
    """
    category: Message Classes


    A bs.Flag has been picked up.

    Attributes:

       flag
          The bs.Flag that has been picked up.

       node
          The bs.Node doing the picking up.
    """

    def __init__(self, flag, node):
        'Instantiate with given values.'
        self.flag = flag
        self.node = node


class FlagDeathMessage(object):
    """
    category: Message Classes

    A bs.Flag has died.

    Attributes:

       flag
          The bs.Flag that died.
    """

    def __init__(self, flag):
        'Instantiate with given values.'
        self.flag = flag


class FlagDroppedMessage(object):
    """
    category: Message Classes

    A bs.Flag has been dropped.

    Attributes:

       flag
          The bs.Flag that was dropped.

       node
          The bs.Node that was holding it.
    """

    def __init__(self, flag, node):
        'Instantiate with given values.'
        self.flag = flag
        self.node = node


class Flag(bs.Actor):
    """
    category: Game Flow Classes

    A flag; used in games such as capture-the-flag or king-of-the-hill.
    Can be stationary or carry-able by players.
    """

    def __init__(
            self, position=(0, 1, 0),
            color=(1, 1, 1),
            materials=[],
            touchable=True, droppedTimeout=None):
        """
        Instantiate a flag.

        If 'touchable' is False, the flag will only touch terrain;
        useful for things like king-of-the-hill where players should
        not be moving the flag around.

        'materials is a list of extra bs.Materials to apply to the flag.

        If 'droppedTimeout' is provided (in seconds), the flag will die
        after remaining untouched for that long once it has been moved
        from its initial position.
        """
        bs.Actor.__init__(self)

        self._initialPosition = None
        self._hasMoved = False

        factory = self.getFactory()

        if type(materials) is not list:
            # in case they passed a tuple or whatnot..
            materials = list(materials)
        if not touchable:
            materials = [factory.noHitMaterial]+materials

        self.node = bs.newNode(
            "flag",
            attrs={'position': (position[0],
                                position[1] + 0.75, position[2]),
                   'colorTexture': factory.flagTexture, 'color': color,
                   'materials':
                   [bs.getSharedObject('objectMaterial'),
                    factory.flagMaterial] + materials},
            delegate=self)

        self._droppedTimeout = droppedTimeout
        if self._droppedTimeout is not None:
            self._count = self._droppedTimeout
            self._tickTimer = bs.Timer(
                1000, call=bs.WeakCall(self._tick),
                repeat=True)
            self._counter = bs.newNode(
                'text', owner=self.node,
                attrs={'inWorld': True, 'color': (1, 1, 1, 0.7),
                       'scale': 0.015, 'shadow': 0.5, 'flatness': 1.0,
                       'hAlign': 'center'})
        else:
            self._counter = None

        self._heldCount = 0

    @classmethod
    def getFactory(cls):
        """
        Returns a shared bs.FlagFactory object, creating it if necessary.
        """
        activity = bs.getActivity()
        try:
            return activity._sharedFlagFactory
        except Exception:
            f = activity._sharedFlagFactory = FlagFactory()
            return f

    def _tick(self):
        if self.node.exists():

            # grab our initial position after one tick (in case we fall)
            if self._initialPosition is None:
                self._initialPosition = self.node.position

                # keep track of when we first move; we don't count down
                # until then
            if not self._hasMoved:
                t = self.node.position
                if (max(abs(t[i] - self._initialPosition[i])
                        for i in range(3)) > 1.0):
                    self._hasMoved = True

            if self._heldCount > 0 or not self._hasMoved:
                self._count = self._droppedTimeout
                self._counter.text = ''
            else:
                self._count -= 1
                if self._count <= 10:
                    t = self.node.position
                    self._counter.position = (t[0], t[1]+1.3, t[2])
                    self._counter.text = str(self._count)
                    if self._count < 1:
                        self.handleMessage(bs.DieMessage())
                else:
                    self._counter.text = ''

    def _hideScoreText(self):
        bs.animate(self._scoreText, 'scale', {0: self._scoreText.scale, 200: 0})

    def setScoreText(self, text):
        """
        Utility func to show a message over the flag; handy for scores.
        """
        if not self.node.exists():
            return
        try:
            exists = self._scoreText.exists()
        except Exception:
            exists = False
        if not exists:
            startScale = 0.0
            math = bs.newNode('math', owner=self.node, attrs={
                              'input1': (0, 1.4, 0), 'operation': 'add'})
            self.node.connectAttr('position', math, 'input2')
            self._scoreText = bs.newNode('text',
                                         owner=self.node,
                                         attrs={'text': text,
                                                'inWorld': True,
                                                'scale': 0.02,
                                                'shadow': 0.5,
                                                'flatness': 1.0,
                                                'hAlign': 'center'})
            math.connectAttr('output', self._scoreText, 'position')
        else:
            startScale = self._scoreText.scale
            self._scoreText.text = text
        self._scoreText.color = bs.getSafeColor(self.node.color)
        bs.animate(self._scoreText, 'scale', {0: startScale, 200: 0.02})
        self._scoreTextHideTimer = bs.Timer(
            1000, bs.WeakCall(self._hideScoreText))

    def handleMessage(self, msg):
        self._handleMessageSanityCheck()
        if isinstance(msg, bs.DieMessage):
            if self.node.exists():
                self.node.delete()
                if not msg.immediate:
                    self.getActivity().handleMessage(FlagDeathMessage(self))
        elif isinstance(msg, bs.HitMessage):
            self.node.handleMessage(
                "impulse", msg.pos[0],
                msg.pos[1],
                msg.pos[2],
                msg.velocity[0],
                msg.velocity[1],
                msg.velocity[2],
                msg.magnitude, msg.velocityMagnitude, msg.radius, 0, msg.
                forceDirection[0],
                msg.forceDirection[1],
                msg.forceDirection[2])
        elif isinstance(msg, bs.OutOfBoundsMessage):
            # we just kill ourselves when out-of-bounds.. would we ever not
            # want this?..
            self.handleMessage(bs.DieMessage(how='fall'))
        elif isinstance(msg, bs.PickedUpMessage):
            self._heldCount += 1
            if self._heldCount == 1 and self._counter is not None:
                self._counter.text = ''
            a = self.getActivity()
            if a is not None:
                a.handleMessage(FlagPickedUpMessage(self, msg.node))
        elif isinstance(msg, bs.DroppedMessage):
            self._heldCount -= 1
            if self._heldCount < 0:
                print 'Flag held count < 0'
                self._heldCount = 0
            a = self.getActivity()
            if a is not None:
                a.handleMessage(FlagDroppedMessage(self, msg.node))
        else:
            bs.Actor.handleMessage(self, msg)
