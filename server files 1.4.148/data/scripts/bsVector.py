import math
import types

class Vector(object):
    """
    category: General Utility Classes

    A 3d Vector.
    """
    isVector = 1

    def __init__(self, x=0., y=0., z=0.):
        'Instantiate with given x, y, and z values.'
	self.data = [x,y,z]

    def __repr__(self):
	return 'Vector(%s,%s,%s)' % (`self.data[0]`,\
				     `self.data[1]`,`self.data[2]`)

    def __str__(self):
	return `self.data`

    def __add__(self, other):
	return Vector(self.data[0]+other.data[0],\
		      self.data[1]+other.data[1],self.data[2]+other.data[2])
    __radd__ = __add__

    def __neg__(self):
	return Vector(-self.data[0], -self.data[1], -self.data[2])

    def __sub__(self, other):
	return Vector(self.data[0]-other.data[0],\
		      self.data[1]-other.data[1],self.data[2]-other.data[2])

    def __rsub__(self, other):
	return Vector(other.data[0]-self.data[0],\
		      other.data[1]-self.data[1],other.data[2]-self.data[2])

    def __mul__(self, other):
	if isVector(other):
	    return reduce(lambda a,b: a+b,
			  map(lambda a,b: a*b, self.data, other.data))
	else:
	    return Vector(self.data[0]*other, self.data[1]*other,
			  self.data[2]*other)

    def __rmul__(self, other):
	if isVector(other):
	    return reduce(lambda a,b: a+b,
			  map(lambda a,b: a*b, self.data, other.data))
	else:
	    return Vector(other*self.data[0], other*self.data[1],
			  other*self.data[2])

    def __div__(self, other):
	if isVector(other):
	    raise TypeError, "Can't divide by a vector"
	else:
	    return Vector(_div(self.data[0],other), _div(self.data[1],other),
			  _div(self.data[2],other))

    def __rdiv__(self, other):
        raise TypeError, "Can't divide by a vector"

    def __cmp__(self, other):
	return cmp(self.data[0],other.data[0]) \
	       or cmp(self.data[1],other.data[1]) \
	       or cmp(self.data[2],other.data[2])

    def __getitem__(self, index):
	return self.data[index]

    def __setitem__(self, index, value):
	self.data[index] = value
    
    def x(self):
        'Return this Vector\'s x component'
	return self.data[0]

    def y(self):
        'Return this Vector\'s y component'
	return self.data[1]

    def z(self):
        'Return this Vector\'s z component'
	return self.data[2]

    def length(self):
        'Return this Vector\'s length.'
	return math.sqrt(self*self)

    def normal(self):
        'Return this Vector\'s normal.'
	len = self.length()
	if len == 0: self.data = [1.0,0.0,0.0]
	return self/len

    def cross(self, other):
        'Return the cross product between this and another Vector.'
	if not isVector(other):
	    raise TypeError, "Cross product with non-vector"
	return Vector(self.data[1]*other.data[2]-self.data[2]*other.data[1],
		      self.data[2]*other.data[0]-self.data[0]*other.data[2],
		      self.data[0]*other.data[1]-self.data[1]*other.data[0])

    def angle(self, other):
        'Return the angle between this and another Vector.'
	if not isVector(other):
	    raise TypeError, "Angle between vector and non-vector"
	cosa = (self*other)/(self.length()*other.length())
	cosa = max(-1.,min(1.,cosa))
	return math.acos(cosa)

def isVector(x):
    return hasattr(x,'isVector')

def _div(a,b):
    if type(a) == types.IntType and type(b) == types.IntType:
	return float(a)/float(b)
    else:
        if b < 0.00001: b = 0.00001
	return a/b


ex = Vector(1.,0.,0.)
ey = Vector(0.,1.,0.)
ez = Vector(0.,0.,1.)
