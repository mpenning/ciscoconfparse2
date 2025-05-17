.. _intro:

=============
Introduction
=============

Overview
---------

ciscoconfparse2_ is similar to an advanced grep and diff API for python_; it
should be used with text network configuration files (such as those from
Arista, Cisco, Juniper, Palo Alto, etc).  It is the next generation of ciscoconfparse_,
which was the primary development vehicle from 2007 until 2023.

ciscoconfparse2_ can:

- Audit existing router / switch / firewall / wlc configurations against a text configuration template
- Retrieve portions of the configuration
- Modify existing configurations
- Build new configurations

The library examines a Cisco or JunOS-style configuration and breaks it into a set
of linked parent / child relationships; each configuration line is stored in a
different :class:`~ciscoconfparse2.models_cisco.IOSCfgLine` object.

.. figure:: _static/ciscoconfparse_overview.png
   :width: 600px
   :alt: ciscoconfparse2 overview
   :align: left

   Figure 1. An Example of Parent-line / Child-line relationships

.. raw:: html

   <br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>

Then you issue queries against these relationships using a familiar family
syntax model. Queries can either be in the form of a simple string, or you can
use `regular expressions`_. The API provides powerful query tools, including
the ability to find all parents that have or do not have children matching a
certain template.

The package also provides a set of methods to query and manipulate the
:class:`~ciscoconfparse2.models_cisco.IOSCfgLine` objects themselves. This gives you a flexible
mechanism to build your own custom queries, because the
:class:`~ciscoconfparse2.models_cisco.IOSCfgLine` objects store all the parent / child
hierarchy in them.

|br|
|br|

What's new in ciscoconfparse2
-----------------------------

I wrote the original `ciscoconfparse`_ in 2007 as literally my first Python
project.

After many years of updates, `ciscoconfparse`_ grew too large. `ciscoconfparse2`_:

- Is tested against Python3.9+ (limited to Python 3.9+ due to python type annotation dynamics before 3.9)
- Includes a `CLI tool`_ to grep / search for a variety of things from the CLI
- Streamlines the API on a simpler user interface.
- Removes legacy and flawed methods from the original (*this could be a breaking change for old scripts*).
- Defaults ``ignore_blank_lines=False`` (*this could be a breaking change for old scripts*).
- Adds the concept of change commits; this is a config-modification performance feature that `ciscoconfparse`_ lacks
- Is better at handling multiple-child-level configurations (such as IOS XR and JunOS)
- Can search for parents and children using an arbitrary-length list of ancestors
- Adds an ``auto_commit`` keyword, which defaults ``True``; however, many loading thousands of configuration lines could be slow with ``auto_commit=True``.
- Brings vast improvements to Cisco IOS diffs
- Intentionally requires a *different import statement* to minimize confusion between them

As such, `ciscoconfparse2`_ API is not the same; it uses different syntax
than the original `ciscoconfparse`_.  However, the new syntax is less magical,
and more pythonic.

The biggest difference in the two APIs is the multi-level search capability.  To illustrate, assume we parse this fake multi-level configuration of interface features:

.. parsed-literal::

   interface Ethernet0/0
    feature00
     parameter01
   interface Ethernet0/1
    feature01
     parameter01
   interface Serial1/0
    feature01
     parameter01

The original `ciscoconfparse`_ could not find ``parameter01`` on ``Ethernet0/1`` without
iterating in a loop (because two different interfaces have ``parameter01``).  However,
`ciscoconfparse2`_ can easily identify it by searching a list of elements with
:py:meth:`~ciscoconfparse2.CiscoConfParse.find_child_objects`:

.. code-block:: python

   >>> from ciscoconfparse2 import CiscoConfParse
   >>> # Assume we parsed the config into 'parse'
   >>> parse
   <CiscoConfParse: 9 lines / syntax: ios / comment delimiters: ['!'] / auto_indent_width: 1 / factory: False / ignore_blank_lines: False / encoding: 'UTF-8' / auto_commit: True>
   >>>
   >>> # Expect to see a list with single child here...
   >>> parse.find_child_objects(["Ethernet", "feature01", "parameter"])
   [<IOSCfgLine # 5 '  parameter01' (parent is # 4)>]
   >>>

However, you can still get multiple children by using a less-specific
regex:

.. code-block:: python

   >>>
   >>> # Expect to see a list of two children here... search across
   >>> # any Ethernet feature
   >>> parse.find_child_objects(["Ethernet", "feature", "parameter"])
   [<IOSCfgLine # 2 '  parameter01' (parent is # 1)>, <IOSCfgLine # 5 '  parameter01' (parent is # 4)>]

Finally, you can still get parent objects with :py:meth:`~ciscoconfparse2.CiscoConfParse.find_parent_objects`:

.. code-block:: python

   >>> parse.find_parent_objects(["Ethernet", "feature01", "parameter"])
   [<IOSCfgLine # 3 'interface Ethernet0/1'>]

What is ciscoconfparse2 good for?
----------------------------------

After several network evolutions, you may have a tangled mess of conflicting or
misconfigured network devices.  Misconfigurations of proxy-arp, static routes,
FHRP timers, routing protocols, duplicated subnets, cdp, console passwords, or
aaa schemes have a measurable affect on up time and beg for a tool to audit them.
However, manually scrubbing configurations is a long and error-prone process.

Audits aren't the only use for ciscoconfparse2.  Let's suppose you are working
on a design and need a list of dot1q trunks on a switch with more than 400
interfaces.  You can't grep for them because you need the interface names of
layer2 trunks; the interface name is stored on one line, and the trunk
configuration is stored somewhere below the interface name.  With
ciscoconfparse, it's really this easy...

.. sourcecode:: python

   >>> from ciscoconfparse2 import CiscoConfParse
   >>> parse = CiscoConfParse('/tftpboot/largeConfig.conf', syntax='ios', factory=False)
   >>>
   >>> # Find parent interfaces that are configured with 'switchport trunk'
   >>> dot1q_trunks = parse.find_parent_objects(["^interface", "switchport trunk"])
   >>> for intf in dot1q_trunks:
   ...     print(intf)
   <IOSCfgLine # 217 'interface GigabitEthernet1/1'>
   <IOSCfgLine # 237 'interface GigabitEthernet1/2'>
   ...
   >>>

This example:

- Imports `ciscoconfparse2`_
- Searches a Cisco IOS configuration file stored in ``/tftpboot/largeConfig.conf``

  - Use the default 'ios' syntax for the configuration file
  - Use the default 'factory' setting, which is disabled

- Search for configuration lines which have:

  - The parent beginning with ``interface`` (and anything else on the config line); ``^`` is a special character that requests to anchor the string at the beginning of the config line.
  - A child of that parent configured with ``switchport trunk`` (and anything else on the config line)

The search found two configuration lines.

We don't have Ciscos
--------------------

Don't let that stop you.  CiscoConfParse parses anything that has a Cisco IOS
style of configuration, which includes:

- Cisco IOS, Cisco Nexus, Cisco IOS-XR, Cisco IOS-XE, Aironet OS, Cisco ASA, Cisco CatOS
- Arista EOS
- Brocade
- HP Switches
- Force 10 Switches
- Dell PowerConnect Switches
- Extreme Networks
- Enterasys

You can also parse `brace-delimited configurations`_ into a Cisco IOS style, which means that CiscoConfParse understands these configurations too:

- Juniper Networks Junos, and Screenos
- Palo Alto Networks Firewall configurations
- F5 Networks configurations

.. _`brace-delimited configurations`: https://github.com/mpenning/ciscoconfparse/blob/81cb4bee7c5ad95301b9e8b3562d70f11fa32505/configs/sample_01.junos
.. _`Dive into Python3`: https://diveintopython3.problemsolving.io/
.. _`regular expressions`: https://docs.python.org/3/howto/regex.html
.. _Python: http://python.org/
.. _CiscoConfParse: https://github.com/mpenning/ciscoconfparse
.. _ciscoconfparse: https://github.com/mpenning/ciscoconfparse
.. _ciscoconfparse2: https://github.com/mpenning/ciscoconfparse2
.. _`CLI tool`: http://www.pennington.net/py/ciscoconfparse2/cli.html

.. |br| raw:: html

   <br>
