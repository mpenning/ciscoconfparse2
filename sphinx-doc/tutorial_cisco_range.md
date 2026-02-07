# Getting Ranges of interfaces

Suppose you want to iterate over all individual interface names in the string "Ethernet1/1,3,5,10-13,20".

This is pretty simple to do with `CiscoRange()`.

## CiscoRange() example

```{code-block} python
>>> from ciscoconfparse2 import CiscoRange
>>>
>>> for intf in CiscoRange("Ethernet1/1,3,5,10-13,20"):
...     print(str(intf))
Ethernet1/1
Ethernet1/3
Ethernet1/5
Ethernet1/10
Ethernet1/11
Ethernet1/12
Ethernet1/13
Ethernet1/20
>>>
```

## CiscoRange() Contains Example

`CiscoRange()` also supports the common 'foo in bar' syntax; additionally, you can use 
string interface names for the comparision if you want.

```{code-block} python
>>> from ciscoconfparse2 import CiscoRange
>>>
>>> big_range = CiscoRange("Ethernet1/1,3-48")
>>> "Ethernet1/1" in big_range
True
>>>
>>> "Ethernet1/2" in big_range
False
>>>
```

## CiscoRange() Contents

When you build a `CiscoRange()`, it actually contains `CiscoIOSInterface()` instances...

You can use attributes on `CiscoIOSInterface()` instances to get components of the interface.

```{code-block} python
>>> from ciscoconfparse2 import CiscoRange
>>>
>>> intf = CiscoRange("Ethernet1/3,10")[0]
>>> intf
<CiscoIOSInterface Ethernet1/3>
>>>
>>> intf.slot
1
>>>
>>> intf.port
3
>>>
>>> intf.prefix
'Ethernet'
>>>
```
