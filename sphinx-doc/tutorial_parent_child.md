# {class}`~ciscoconfparse2.CiscoConfParse` Fundamentals: Using Parent / Child Relationships

## IOS Parent-child relationships

As we saw in a previous section, {class}`~ciscoconfparse2.CiscoConfParse()` reads an
IOS configuration and breaks it into a list of parent-child relationships.  Used correctly, these
relationships can reveal a lot of useful information.  The concept of IOS
parent and child is pretty intuitive, but we'll go through a another example
for in detail for clarity.

```{note}
CiscoConfParse assumes the configuration is in the *exact format* rendered by Cisco IOS devices when you use `show runn` or `show start`.
```

Line 1 is a parent:

```{code-block} none
:emphasize-lines: 1

policy-map QOS_1
 class GOLD
  priority percent 10
 class SILVER
  bandwidth 30
  random-detect
 class default
!
```

Child lines are indented more than parent lines; thus, lines 2, 4 and 7
are children of line 1:

```{code-block} none
:emphasize-lines: 2,4,7

policy-map QOS_1
 class GOLD
  priority percent 10
 class SILVER
  bandwidth 30
  random-detect
 class default
!
```

Furthermore, line 3 (highlighted) is a child of line 2:

```{code-block} none
:emphasize-lines: 3

policy-map QOS_1
 class GOLD
  priority percent 10
 class SILVER
  bandwidth 30
  random-detect
 class default
!
```

In short:

- Line 1 is a parent, and its children are lines 2, 4, and 7.
- Line 2 is also a parent, and it only has one child: line 3.

{class}`~ciscoconfparse2.CiscoConfParse()` uses these parent-child relationships
to build queries.  For instance, you can find a list of all parents with or
without a child; or you can find all the configuration elements that are
required to reconfigure a certain class-map.

### Example: Retrieving text from an {class}`~ciscoconfparse2.models_cisco.IOSCfgLine` object

This example:

- Parses through a configuration
- Finds an {class}`~ciscoconfparse2.models_cisco.IOSCfgLine` object with {func}`~ciscoconfparse2.CiscoConfParse.find_objects()`
- Retrieves the configuration text from that object (highlighted in yellow)

```{code-block} python
:emphasize-lines: 9

>>> from ciscoconfparse2.ciscoconfparse2 import CiscoConfParse
>>> parse = CiscoConfParse([
...     '!',
...     'interface Serial1/0',
...     ' ip address 1.1.1.5 255.255.255.252'
...     ])
>>> for cmd in parse.find_objects(r"interface"):
...     print("Object: " + repr(cmd))
...     print("Config text: " + cmd.text)
...
Object: <IOSCfgLine # 1 'interface Serial1/0'>
Config text: interface Serial1/0
>>>
>>> quit()
```

In the example, `cmd.text` refers to the {class}`~ciscoconfparse2.models_cisco.IOSCfgLine`
`.text` attribute, which retrieves the text of the original IOS configuration
statement.  You can also use the python [str] function to the the configuration text.

## Baseline configuration for these examples

This tutorial will run all the queries against a sample configuration, which is shown below.

```none
! Filename: /tftpboot/bucksnort.conf
!
policy-map QOS_1
 class GOLD
  priority percent 10
 class SILVER
  bandwidth 30
  random-detect
 class default
!
interface Ethernet0/0
 ip address 1.1.2.1 255.255.255.0
 no cdp enable
!
interface Serial1/0
 encapsulation ppp
 ip address 1.1.1.1 255.255.255.252
!
interface Serial1/1
 encapsulation ppp
 ip address 1.1.1.5 255.255.255.252
 service-policy output QOS_1
!
interface Serial1/2
 encapsulation hdlc
 ip address 1.1.1.9 255.255.255.252
!
class-map GOLD
 match access-group 102
class-map SILVER
 match protocol tcp
!
```

## Example Usage: Finding interface names that match a substring

The following script will load a configuration file from
`/tftpboot/bucksnort.conf` and use
{func}`~ciscoconfparse2.CiscoConfParse.find_objects` to find the
Serial interfaces.

Note that the `^` symbol at the beginning of the search string is a regular expression; `^interface Serial` tells python to limit the search to lines that
*begin* with `interface Serial`.

```{code-block} python
:emphasize-lines: 3

>>> from ciscoconfparse2.ciscoconfparse2 import CiscoConfParse
>>> parse = CiscoConfParse("/tftpboot/bucksnort.conf")
>>> serial_objs = parse.find_objects("^interface Serial")
```

The assuming we use the configuration in the example above,
{func}`~ciscoconfparse2.CiscoConfParse.find_objects()` scans the
configuration for matching config objects and stores a list of
{class}`~ciscoconfparse2.models_cisco.IOSCfgLine` objects in `serial_objs`.

```python
>>> serial_objs
[<IOSCfgLine # 14 'interface Serial1/0'>,
<IOSCfgLine # 18 'interface Serial1/1'>,
<IOSCfgLine # 23 'interface Serial1/2'>]
```

As you can see, the config statements are stored inside
{class}`~ciscoconfparse2.models_cisco.IOSCfgLine` objects.  If you want to access the
text inside the {class}`~ciscoconfparse2.models_cisco.IOSCfgLine` objects, just call their
`text` attribute.  For example...

```{code-block} python
:emphasize-lines: 2

>>> for obj in serial_objs:
...     print(obj.text)
...
interface Serial1/0
interface Serial1/1
interface Serial1/2
```

Going forward, I will assume that you know how to use regular expressions; if
you would like to know more about regular expressions, O'Reilly's
[Mastering Regular Expressions](http://www.amazon.com/Mastering-Regular-Expressions-Jeffrey-Friedl/dp/0596528124/) book is very good.

## Example Usage: Finding parents with a specific child

Suppose we need to find interfaces with the `QOS_1` service-policy applied
outbound... we should use {func}`~ciscoconfparse2.CiscoConfParse.find_parent_objects()` because
we want the interface name (which is the parent line).

### {func}`~ciscoconfparse2.CiscoConfParse.find_parent_objects()`

```{code-block} python
:emphasize-lines: 2,3

>>> parse = CiscoConfParse("/tftpboot/bucksnort.conf")
>>> qos_intfs = parse.find_parent_objects([r"^interf", r"service-policy output QOS_1"])
...
>>> # Note that `qos_intfs` is a list
>>> qos_intfs
[<IOSCfgLine # 18 'interface Serial1/1'>]
>>>
>>> # Use index number zero to get the first (and only) element
>>> qos_intfs[0]
<IOSCfgLine # 18 'interface Serial1/1'>
>>>
>>> # Use the `.text` property to get the actual command text
>>> qos_intfs[0].text
'interface Serial1/1'
```

```{note}
`find_parent_objects()` supports an arbitrary list of search terms; this makes searching multiple child levels very simple.
```

## Example Usage: Finding parents *without* a specific child

Let's suppose you wanted a list of all interfaces that have CDP enabled; this implies a couple of things:

1. CDP has not been disabled globally with `no cdp run`
2. The interfaces in question are not configured with `no cdp enable`

{func}`~ciscoconfparse2.CiscoConfParse.find_parent_objects_wo_child` is a function to
find parents without a specific child; it requires arguments similar to
{func}`~ciscoconfparse2.CiscoConfParse.find_parent_objects`:

- The first argument is a regular expression to match the parents
- The second argument is a regular expression to match the child's *exclusion*

Since we need to find parents that do not have `no cdp enable`, we will use
{func}`~ciscoconfparse2.CiscoConfParse.find_parent_objects_wo_child` for this query.
Note that the script below makes use of a special property of python lists...
empty lists test False in Python; thus, we can
use `if not bool(parse.find_objects(r'no cdp run'))` to ensure that CDP is
running globally on this device.

```{code-block} python
:emphasize-lines: 2-4

>>> parse = CiscoConfParse("/tftpboot/bucksnort.conf")
>>> if not bool(parse.find_objects(r'no cdp run')):
...     cdp_intfs = parse.find_parent_objects_wo_child(r'^interface',
...         r'no cdp enable')
```

Results:

```python
>>> cdp_intfs
[<IOSCfgLine # 14 'interface Serial1/0'>, <IOSCfgLine # 18 'interface Serial1/1'>, <IOSCfgLine # 23 'interface Serial1/2'>]
```

[list-comprehension]: https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions
