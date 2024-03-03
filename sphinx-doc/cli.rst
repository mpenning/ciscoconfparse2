.. _cli:

===========
CLI Command
===========

Overview
--------

ciscoconfparse2 adds a CLI command to search and diff configurations.  The
syntax follows the API.

All CLI examples will use this example configuration...

.. code-block:: none

   !
   router bgp 65111
    bgp router-id 192.0.2.200
    neighbor 192.0.2.1 remote-as 64000
    address-family ipv4 unicast
     default-information originate
     neighbor 192.0.2.1 activate
   !

Example 1: Find parent lines
----------------------------

If you want to find ``router bgp 65111``, use this CLI command

.. code-block:: none

   $ ccp parent -a 'router bgp' conf/path/or/file/glob.conf

The output will be:

.. code-block:: none

   Syntax      : ios
   Returing    : parent text
   Ouput as    : raw_text
     parent: router bgp
   ---------- file: conf/path/or/file/glob.conf ----------
   router bgp 65111

That CLI command is the equivalent of running this
:func:`~ciscoconfparse2.CiscoConfParse.find_parent_objects` script:

.. code-block:: python

   >>> from ciscoconfparse2 import CiscoConfParse
   >>> parse = CiscoConfParse('conf/path/or/file/glob.conf')
   >>> for obj in parse.find_parent_objects(['router bgp'):
   ...     print(obj.text)
   >>>

Example 2: Find child lines
---------------------------

If you want to find ``default-information originate``, use this CLI command

.. code-block:: none

   $ ccp child -a 'router bgp,address-family,default-information' conf/path/or/file/glob.conf

The output will be:

.. code-block:: none

   Syntax      : ios
   Returing    : child text
   Ouput as    : raw_text
     parent: router bgp
   ---------- file: conf/path/or/file/glob.conf ----------
   default-information originate

That CLI command is the equivalent of running this
:func:`~ciscoconfparse2.CiscoConfParse.find_child_objects` script:

.. code-block:: python

   >>> from ciscoconfparse2 import CiscoConfParse
   >>> parse = CiscoConfParse('conf/path/or/file/glob.conf')
   >>> for obj in parse.find_child_objects(['router bgp',
   ...                                      'address-family',
   ...                                      'default-information']):
   ...     print(obj.text)
   >>>

Example 3: Find branches as lists
---------------------------------

A branch is just a list of all parents and the child text.  To find the branch
for 'default-information originate'...

.. code-block:: none

   $ ccp branch -a 'router bgp,address-family,default-information' conf/path/or/file/glob.conf

The output will be:

.. code-block:: none

   Syntax      : ios
   Returing    : branch text
   Ouput as    : raw_text
     parent: router bgp
     child : address-family ipv4 unicast
     child : default-information originate
   ---------- file: conf/path/or/file/glob.conf ----------
   ['router bgp 65111', ' address-family ipv4 unicast', '  default-information originate']

That CLI command is the equivalent of running this
:func:`~ciscoconfparse2.CiscoConfParse.find_object_branches` script:

.. code-block:: python

   >>> from ciscoconfparse2 import CiscoConfParse
   >>> parse = CiscoConfParse('conf/path/or/file/glob.conf')
   >>> for branch in parse.find_object_branches(['router bgp',
   ...                                           'address-family',
   ...                                           'default-information']):
   ...     print([obj.text for obj in branch])
   ...     
   >>>

Example 4: Find branches as the original configuration
------------------------------------------------------

You can also find branches as shown in the original configuration... just use:

.. code-block:: none

   $ ccp branch -a 'router bgp' -o original conf/path/or/file/glob.conf

This will print...

.. code-block:: none

   Syntax      : ios
   Returing    : branch text
   Ouput as    : original
     parent: router bgp
   ---------- file: conf/path/or/file/glob.conf ----------
   router bgp 65111
    bgp router-id 192.0.2.200
    neighbor 192.0.2.1 remote-as 64000
    address-family ipv4 unicast
     default-information originate
     neighbor 192.0.2.1 activate

It should be noted that searching ``ccp branch -a 'router bgp'`` is a special
case that is local to the CLI script.

.. note::

   When searching with only one term, this is a special case of the CLI
   script.  If you only use one branch search term, all configuration children
   matching the configuation parent will be shown (the parent is included as well).

