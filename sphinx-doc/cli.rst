.. _cli:

===========
CLI Command
===========

Overview
--------

ciscoconfparse2 adds a CLI command to search and diff configurations.  The
syntax follows the API.

All CLI examples will use this configuration...

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

If you want to find ``router bgp 65111`` (which has the child: ``bgp router-id 192.0.2.200``) , use this CLI command...

.. code-block:: none

   $ ccp parent -a 'router bgp,router-id' conf/path/or/file/glob.conf

The parent will be printed, and you should see:

.. code-block:: none

   Syntax      : ios
   Returing    : parent text
   Output as   : raw_text
     parent: router bgp
     child : router-id
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

The last child will be printed, and you should see:

.. code-block:: none

   Syntax      : ios
   Returing    : child text
   Output as   : raw_text
     parent: router bgp
     child : address-family
     child : default-information
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

A branch is just a list of all matching parent and child text lines.  To find the branch
for 'default-information originate'...

.. code-block:: none

   $ ccp branch -a 'router bgp,address-family,default-information' conf/path/or/file/glob.conf

The output will be:

.. code-block:: none

   Syntax      : ios
   Returing    : branch text
   Output as   : raw_text
     parent: router bgp
     child : address-family
     child : default-information
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
   Output as   : original
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

   When searching with only one branch  search term, this is a special case of
   the CLI script.  If you only use one branch search term, all configuration
   children matching the configuation parent will be shown (the parent is
   included as well).


Example 5: Find IP addresses within a CIDR range
------------------------------------------------

``ccp ipgrep`` can find IP addresses in a CIDR range.  By default,
``ccp ipgrep`` splits words on whitespace and checks whether a word is an IP
address and that it falls within the requested CIDR range.

For instance, assume we have the following file contents:

.. code-block:: none

   This file contains the addresses: 172.16.1.1 172.16.1.1 and 172.16.1.2

If you run this command, you'll get both IP addresses printed to
STDOUT: ``ccp ipgrep -s 172.16.1.0/24 path/to/file.txt``.

.. code-block:: none

   $ ccp ipgrep -s 172.16.1.0/24 path/to/file.txt
   172.16.1.1
   172.16.1.1
   172.16.1.2
   $

As you see, you can get duplicate IP addresses unless you
use ``ccp ipgrep -u -s 172.16.1.0/24 path/to/file.txt``.  The
``-u`` option stands for ``--unique``.

The default mode is just listing the IP addresses, but you can also
get matching lines
with ``ccp ipgrep -l -s 172.16.1.0/24 path/to/file.txt``.

All the options for ``ccp ipgrep`` are:


.. code-block:: none

   $ ccp ipgrep -h
   usage: ccp ipgrep [-h] [-s SUBNETS] [-w WORD_DELIMITER] [-l | -u] [ipgrep_file]

   options:
     -h, --help            show this help message and exit

   required:
     ipgrep_file           Grep for IPs in these files, defaults to STDIN.
       -s SUBNETS, --subnets SUBNETS
                           Comma-separated IPv4 and/or IPv6 addresses or prefixes,
                           such as '192.0.2.1,2001:db8::/32'. If the mask is not
                           specified, a host-mask assumed.

   optional:
     -w WORD_DELIMITER, --word_delimiter WORD_DELIMITER
                           Word delimiter regular expression, defaults to all whitespace.
                           Join multiple regex delimiters with a pipe character.
     -l, --line            Enable line mode (return lines instead of only returning the IP)
     -u, --unique          Only print unique IPs (remove duplicates)
