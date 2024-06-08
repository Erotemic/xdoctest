# This demonstrates dynamics of properties with clobbering any
# namespace variables, so its entirely clear what variables exist and how they
# are transformed as the property dectorators are applied
import pytest


def my_getter_func(self):
    " getter doc"
    print('call getter')
    return 'value'


def my_setter_func(self, value):
    " setter doc"
    print('call setter for value = {!r}'.format(value))


def my_deleter_func(self):
    " deleter doc"
    print('call deleter')


# Use the property decorator directly with normal call syntax
# Note properties --- like most other decorators --- return new function
# objects and do not change the underlying function object. Hense we can still
# print the original functions and see how they are assigned to the fset / fget
# / fdel attributes of the returned property object.
my_getter_prop = property(my_getter_func)
my_setter_prop = my_getter_prop.setter(my_setter_func)
my_deleter_prop = my_setter_prop.deleter(my_deleter_func)

print('my_getter_func = {!r}'.format(my_getter_func))
print('my_setter_func = {!r}'.format(my_setter_func))
print('my_deleter_func = {!r}'.format(my_deleter_func))

print('my_getter_prop = {!r}'.format(my_getter_prop))
print('my_setter_prop = {!r}'.format(my_setter_prop))
print('my_deleter_prop = {!r}'.format(my_deleter_prop))

print('my_getter_prop = {!r}'.format(my_getter_prop))
print('my_getter_prop.fget = {!r}'.format(my_getter_prop.fget))
print('my_getter_prop.fset = {!r}'.format(my_getter_prop.fset))
print('my_getter_prop.fdel = {!r}'.format(my_getter_prop.fdel))
print('my_getter_prop.__doc__ = {!r}'.format(my_getter_prop.__doc__))

print('my_setter_prop = {!r}'.format(my_setter_prop))
print('my_setter_prop.fget = {!r}'.format(my_setter_prop.fget))
print('my_setter_prop.fset = {!r}'.format(my_setter_prop.fset))
print('my_setter_prop.fdel = {!r}'.format(my_setter_prop.fdel))
print('my_setter_prop.__doc__ = {!r}'.format(my_setter_prop.__doc__))

print('my_deleter_prop = {!r}'.format(my_deleter_prop))
print('my_deleter_prop.fget = {!r}'.format(my_deleter_prop.fget))
print('my_deleter_prop.fset = {!r}'.format(my_deleter_prop.fset))
print('my_deleter_prop.fdel = {!r}'.format(my_deleter_prop.fdel))
print('my_deleter_prop.__doc__ = {!r}'.format(my_deleter_prop.__doc__))

# Note: each function has its own doc, but only the doc of the getter is stored

# my_getter_func          = <function my_getter_func at 0x7f2f14a6d700>
# my_setter_func          = <function my_setter_func at 0x7f2f14a6d0d0>
# my_deleter_func         = <function my_deleter_func at 0x7f2f14b88ee0>
# my_getter_prop          = <property object at 0x7f2f14c7b180>
# my_setter_prop          = <property object at 0x7f2f14d318b0>
# my_deleter_prop         = <property object at 0x7f2f14c81e00>
# my_getter_prop          = <property object at 0x7f2f14c7b180>
# my_getter_prop.fget     = <function my_getter_func at 0x7f2f14a6d700>
# my_getter_prop.fset     = None
# my_getter_prop.fdel     = None
# my_getter_prop.__doc__  = ' getter doc'
# my_setter_prop          = <property object at 0x7f2f14d318b0>
# my_setter_prop.fget     = <function my_getter_func at 0x7f2f14a6d700>
# my_setter_prop.fset     = <function my_setter_func at 0x7f2f14a6d0d0>
# my_setter_prop.fdel     = None
# my_setter_prop.__doc__  = ' getter doc'
# my_deleter_prop         = <property object at 0x7f2f14c81e00>
# my_deleter_prop.fget    = <function my_getter_func at 0x7f2f14a6d700>
# my_deleter_prop.fset    = <function my_setter_func at 0x7f2f14a6d0d0>
# my_deleter_prop.fdel    = <function my_deleter_func at 0x7f2f14b88ee0>
# my_deleter_prop.__doc__ = ' getter doc'


# Create an empty type
class Husk:
    pass

# Assigning properties to the class itself is equivalent to how they are
# normally defined in the scope of the class definition.
Husk.x = my_deleter_prop
Husk.y = my_setter_prop
Husk.z = my_getter_prop


# Creating an instance of the class will let us use our property variables
self = Husk()

# The "deleter" property has fget, fset, and fdel defined
self.x
self.x = 3
del self.x


# The "setter" property only had fget and fset defined
self.y
self.y = 3
with pytest.raises(AttributeError):
    del self.y


# The "getter" property only had fget defined
self = Husk()
self.z
with pytest.raises(AttributeError):
    self.z = 3
    del self.z
