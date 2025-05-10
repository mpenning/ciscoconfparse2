.. _example_complex:

:class:`~ciscoconfparse2.CiscoConfParse` Complex Example
========================================================

In addition to the CLI tool, ciscoconfparse2 also offers a Python API.

This example code parses a configuration stored in
``tests/fixtures/configs/sample_08.ios`` and will find the
IP address / switchport parameters assigned to interfaces.

Save this code in a file named example.py

.. code-block:: python

   from ciscoconfparse2 import CiscoConfParse
   from ciscoconfparse2 import IPv4Obj

   def intf_csv(intf_obj) -> str:
       """
       :return: CSV for each interface object.
       :rtype: str
       """

       # intf_obj is an BaseCfgLine() subclass containing
       #   something like 'interface Loopback0'
       intf_name = " ".join(intf_obj.split()[1:])

       admin_status = intf_obj.re_match_iter_typed("^\s+(shutdown)",
                                                   default="not_shutdown",
                                                   result_type=str)

       # Search children of all interfaces for a regex match and return
       # the value matched in regex match group 1.  If there is no match,
       # return a default value: 0.0.0.1/32
       addr_netmask = intf_obj.re_match_iter_typed(r"^\s+ip\saddress\s(\d+\.\d+\.\d+\.\d+\s\S+)",
                                                   result_type=IPv4Obj,
                                                   group=1,
                                                   default=IPv4Obj("0.0.0.1/32"))

       # Find the description and replace all commas in it
       description = intf_obj.re_match_iter_typed("description\s+(\S.*)").replace(",", "_")

       switchport_status = intf_obj.re_match_iter_typed("(switchport)",
                                                        default="not_switched")

       # Return a csv based on whether this is a switchport
       if switchport_status == "not_switched":
           return f"{intf_name},{admin_status},{addr_netmask.as_cidr_addr},{switchport_status},,,{description}"

       else:
           # Only calculate switchport values if this is a switchport
           trunk_access = intf_obj.re_match_iter_typed("switchport mode (trunk)",
                                                       default="access",
                                                       result_type=str)
           access_vlan = intf_obj.re_match_iter_typed("switchport access vlan (\d+)",
                                                      default=1,
                                                      result_type=int)

           # Return the CSV string of values...
           return f"{intf_name},{admin_status},{switchport_status},{trunk_access},{access_vlan},{description}"

   parse = CiscoConfParse('tests/fixtures/configs/sample_08.ios', syntax='ios')

   # Find interface BaseCfgLine() instances...
   for intf_obj in parse.find_objects('^interface'):
       print(intf_csv(intf_obj))


That will print a CSV with detailed interface information in it:

.. code-block:: none

   $ python example.py
   Loopback0,not_shutdown,172.16.0.1/32,not_switched,,,SEE http://www.cymru.com/Documents/secure-ios-template.html
   Null0,not_shutdown,0.0.0.1/32,not_switched,,,
   ATM0/0,not_shutdown,0.0.0.1/32,not_switched,,,
   ATM0/0.32 point-to-point,not_shutdown,0.0.0.1/32,not_switched,,,
   FastEthernet0/0,not_shutdown,172.16.2.1/24,not_switched,,,[IPv4 and IPv6 desktop / laptop hosts on 2nd-floor North LAN]
   FastEthernet0/1,not_shutdown,172.16.3.1/30,not_switched,,,[IPv4 and IPv6 OSPF Transit via West side of building]
   FastEthernet1/0,not_shutdown,172.16.4.1/30,not_switched,,,[IPv4 and IPv6 OSPF Transit via North side of building]
   FastEtheret1/1,not_shutdown,,switchport,access,12,[switchport to the comptroller cube]
   FastEtheret1/2,not_shutdown,,switchport,access,12,[switchport to the IDF media converter]
   Virtual-Template1,not_shutdown,0.0.0.1/32,not_switched,,,
   Dialer1,not_shutdown,0.0.0.1/32,not_switched,,,[IPv4 and IPv6 OSPF Transit via WAN Dialer: NAT_ CBWFQ interface]
