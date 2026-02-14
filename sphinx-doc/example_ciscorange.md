(example-CiscoRange)=

# {class}`~ciscoconfparse2.ccp_util.CiscoRange` Example

First let's handle the basics; what exactly is a "Cisco Range"?  In
Cisco IOS, you sometimes see strings like this: "Eth1/5-8,15,18,22,30-33";

Let's break that down; that string encapsulates a list of Cisco IOS 
interface numbers.  In this case expanding the string results
in this list of `CiscoIOSInterface()` instances:

- `<CiscoIOSInterface Eth1/5>`
- `<CiscoIOSInterface Eth1/6>`
- `<CiscoIOSInterface Eth1/7>`
- `<CiscoIOSInterface Eth1/8>`
- `<CiscoIOSInterface Eth1/15>`
- `<CiscoIOSInterface Eth1/18>`
- `<CiscoIOSInterface Eth1/22>`
- `<CiscoIOSInterface Eth1/30>`
- `<CiscoIOSInterface Eth1/31>`
- `<CiscoIOSInterface Eth1/32>`
- `<CiscoIOSInterface Eth1/33>`

In short, `CiscoRange()` explodes "Eth1/5-8,15,18,22,30-33" into something you
can iterate over.  You can walk all those interfaces like this:

```python
from ciscoconfparse2 import CiscoRange

# Print all the individual interface names...
for intf in CiscoRange("Eth1/5-8,15,18,22,30-33"):
    # Convert the CiscoIOSInterface() instances into a string...
    print(intf)
```

But there's more; you can also check membership with the `CiscoRange().__contains__()` method like this:

Option 1, compare with the string name:

```python
from ciscoconfparse2 import CiscoRange
# This is True
"Eth1/5" in CiscoRange("Eth1/5-8,15,18,22,30-33")
```

Option 2, compare with the string name:

```python
from ciscoconfparse2 import CiscoRange, CiscoIOSInterface
# This is True
CiscoIOSInterface("Eth1/5") in CiscoRange("Eth1/5-8,15,18,22,30-33")
```

Option 3, compare with another `CiscoRange()`...

```python
from ciscoconfparse2 import CiscoRange
# This is True
CiscoRange("Eth1/5-7,18") in CiscoRange("Eth1/5-8,15,18,22,30-33")
```

To be explicit, this is an example of a False membership test...

```python
from ciscoconfparse2 import CiscoRange
# This is False
"Eth1/1" in CiscoRange("Eth1/5-8,15,18,22,30-33")
```

