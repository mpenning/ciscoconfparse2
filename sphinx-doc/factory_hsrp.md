(factory-hsrp)=

# HSRP Factory

As of version 0.4.2, ciscoconfparse2 supports multiple HSRP Groups per interface. An example of extracting multiple HSRP groups per interface follows.

Assume we use the following configuration:

```text
!
interface GigabitEthernet1/0
 ip address 172.16.0.1 255.255.255.0
 standby ip 172.16.0.251
 standby priority 15
 standby 100 ip 172.16.0.252
 standby 100 ipv6 autoconfig
 standby 100 priority 150
 standby 100 preempt delay 15
 standby 100 track Dialer1 75
 standby 100 track Dialer2 30
 standby 101 ip 172.16.0.253
!
interface Dialer1
 ip address 172.31.1.1 255.255.255.0
!
interface Dialer2
 ip address 172.31.2.1 255.255.255.0
```

The following script should be used to extract the HSRP Groups from `GigabitEthernet1/0`.

```python
from ciscoconfparse2 import CiscoConfParse

parse = CiscoConfParse("/path/to/config/file", syntax="ios", factory=True)

hsrp_intf = parse.find_objects("interface GigabitEthernet1/0")[0]

# iterate over the list of HSRP Groups
for hsrp_group_obj in hsrp_intf.get_hsrp_groups():
    # An integer HSRP Group number
    hsrp_group = hsrp_group_obj.group
    # An integer HSRP Group priority, default to 100
    hsrp_priority = hsrp_group_obj.priority
    # An integer HSRP Group preempt delay, default to 0 seconds
    hsrp_preempt_delay = hsrp_group_obj.preempt_delay
    # A string HSRP Group IPv4 address, default to ''
    hsrp_ipv4 = hsrp_group_obj.ipv4
    # A string HSRP Group IPv6 info, default to ''
    hsrp_ipv6 = hsrp_group_obj.ipv6
```
