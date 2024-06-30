.. _example_simple:

:class:`~ciscoconfparse2.CiscoConfParse` Simple Example
=======================================================

In addition to the CLI tool, ciscoconfparse2 also offers a Python API.

This example code parses a configuration stored in
``tests/fixtures/configs/sample_02.ios`` and selects interfaces that are shutdown.

In this case, the parent is a line containing ``interface`` and the child is a
line containing the word ``shutdown``.

Save this code in a file named example.py

.. code-block:: python

   # filename: example.py
   from ciscoconfparse2 import CiscoConfParse

   ##############################################################################
   # Find all Cisco IOS interface names that are shutdown
   ##############################################################################
   #
   # Search for:
   #     !
   #     interface Foo
   #      description ignore-this-line
   #      shutdown
   #     !

   # Search a configuration in the test fixutres directory
   parse = CiscoConfParse('tests/fixtures/configs/sample_02.ios', syntax='ios')

   # Find a parent line containing 'interface' and child line with 'shutdown'
   for intf_obj in parse.find_parent_objects(['interface', 'shutdown']):
       intf_name = " ".join(intf_obj.split()[1:])
       print(f"Shutdown: {intf_name}")

That will print:

.. code-block:: none

   $ python example.py
   Shutdown: FastEthernet0/7
   Shutdown: FastEthernet0/8
   Shutdown: FastEthernet0/9
   Shutdown: FastEthernet0/11
   Shutdown: FastEthernet0/13
   Shutdown: FastEthernet0/15
   Shutdown: FastEthernet0/17
   Shutdown: FastEthernet0/19
   Shutdown: FastEthernet0/20
   Shutdown: FastEthernet0/22
   Shutdown: VLAN1
