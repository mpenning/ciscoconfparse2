# ciscoconfparse

[![git commits][41]][42] [![Version][2]][3] [![Downloads][6]][7] [![License][8]][9]

[![SonarCloud][51]][52] [![SonarCloud Maintainability Rating][53]][54] [![SonarCloud Lines of Code][55]][56] [![SonarCloud Bugs][59]][60] [![SonarCloud Code Smells][57]][58] [![SonarCloud Tech Debt][61]][62]

[![Snyk Package Health][37]][38]


## Introduction: What is ciscoconfparse?

Short answer: ciscoconfparse is a [Python][10] library
that helps you quickly answer questions like these about your
Cisco configurations:

- What interfaces are shutdown?
- Which interfaces are in trunk mode?
- What address and subnet mask is assigned to each interface?
- Which interfaces are missing a critical command?
- Is this configuration missing a standard config line?

It can help you:

- Audit existing router / switch / firewall / wlc configurations
- Modify existing configurations
- Build new configurations

Speaking generally, the library examines an IOS-style config and breaks
it into a set of linked parent / child relationships. You can perform
complex queries about these relationships.

[![Cisco IOS config: Parent / child][11]][11]

## Generic Usage

The following code will parse a configuration stored in
`exampleswitch.conf` and select interfaces that are shutdown.

In this case, the parent is a line containing `interface` and
the child is a line containing the word `shutdown`.

```python
from ciscoconfparse import CiscoConfParse

parse = CiscoConfParse('exampleswitch.conf', syntax='ios')

for intf_obj in parse.find_parent_objects('^interface', '^\s+shutdown'):
    print("Shutdown: " + intf_obj.text)
```

The next example will find the IP address assigned to interfaces.

```python
from ciscoconfparse import CiscoConfParse

parse = CiscoConfParse('exampleswitch.conf', syntax='ios')

for ccp_obj in parse.find_objects('^interface'):

    intf_name = ccp_obj.re_match_typed('^interface\s+(\S.+?)$')

    # Search children of all interfaces for a regex match and return
    # the value matched in regex match group 1.  If there is no match,
    # return a default value: ''
    intf_ip_addr = ccp_obj.re_match_iter_typed(
        r'ip\saddress\s(\d+\.\d+\.\d+\.\d+)\s', result_type=str,
        group=1, default='')
    print(f"{intf_name}: {intf_ip_addr}")
```

## Cisco IOS Factory Usage

CiscoConfParse has a special feature that abstracts common IOS / NXOS / ASA / IOSXR fields; at this time, it is only supported on those configuration types. You will see factory parsing in CiscoConfParse code as parsing the configuration with `factory=True`.  A fraction of these pre-parsed Cisco IOS fields follows; some variables are not used below, but simply called out for quick reference.

```python
from ciscoconfparse import IPv4Obj, IPv6Obj
from ciscoconfparse import CiscoConfParse

##############################################################################
# Parse an example Cisco IOS HSRP configuration from:
#     tests/fixtures/configs/sample_08.ios
#
# !
# interface FastEthernet0/0
#  ip address 172.16.2.1 255.255.255.0
#  ipv6 dhcp server IPV6_2FL_NORTH_LAN
#  ipv6 address fd01:ab00::/64 eui-64
#  ipv6 address fe80::1 link-local
#  ipv6 enable
#  ipv6 ospf 11 area 0
#  standby 110 ip 172.16.2.254
#  standby 110 ipv6 autoconfig
#  standby 110 priority 150
#  standby 110 preempt delay minimum 15
#  standby 110 track Dialer1 75
#  standby 110 track FastEthernet 0/1
#  standby 110 track FastEthernet1/0 30
#  standby 111 ip 172.16.2.253
#  standby 111 priority 150
#  standby 111 preempt delay minimum 15
#  standby 111 track Dialer1 50
#
##############################################################################
parse = CiscoConfParse('tests/fixtures/configs/sample_08.ios', syntax='ios', factory=True)
for ccp_obj in parse.find_objects('^interface'):

    # Skip if there are no HSRPInterfaceGroup() instances...
    if len(ccp_obj.hsrp_interfaces) == 0:
        continue

    # Interface name, such as 'FastEthernet0/0'
    intf_name = ccp_obj.name

    # Interface description
    intf_description = ccp_obj.description

    # IPv4Obj
    intf_v4obj = ccp_obj.ipv4_addr_object

    # IPv4 address object: ipaddress.IPv4Address()
    intf_v4addr = ccp_obj.ipv4_addr_object.ip

    # IPv4 netmask object: ipaddress.IPv4Address()
    intf_v4masklength = ccp_obj.ipv4_addr_object.masklength

    # set() of IPv4 secondary address/prefixlen strings
    intf_v4secondary_networks = ccp_obj.ip_secondary_networks

    # set() of IPv4 secondary address strings
    intf_v4secondary_addresses = ccp_obj.ip_secondary_addresses

    # List of HSRP IPv4 addrs from the ciscoconfpasre/models_cisco.py HSRPInterfaceGroup()
    intf_hsrp_addresses = [hsrp_grp.ip for hsrp_grp in ccp_obj.hsrp_interfaces]

    # A bool for using HSRP bia mac-address...
    intf_hsrp_usebia = any([ii.use_bia for ii in ccp_obj.hsrp_interfaces])

    ##########################################################################
    # Print a simple interface summary
    ##########################################################################
    print("----")
    print(f"Interface {ccp_obj.interface_object.name}: {intf_v4addr}/{intf_v4masklength}")
    print(f"  Interface {intf_name} description: {intf_description}")

    ##########################################################################
    # Print HSRP Group interface tracking information
    ##########################################################################
    print("")
    print(f"  HSRP tracking for {set([ii.interface_name for ii in ccp_obj.hsrp_interfaces])}")
    for hsrp_intf_group in ccp_obj.hsrp_interfaces:
        group = hsrp_intf_group.hsrp_group
        # hsrp_intf_group.interface_tracking is a list of dictionaries
        if len(hsrp_intf_group.interface_tracking) > 0:
            print(f"  --- HSRP Group {group} ---")
            for track_intf in hsrp_intf_group.interface_tracking:
                print(f"    --- Tracking {track_intf.interface} ---")
                print(f"    Tracking interface: {track_intf.interface}")
                print(f"    Tracking decrement: {track_intf.decrement}")
                print(f"    Tracking weighting: {track_intf.weighting}")


    ##########################################################################
    # Break out inidividual interface name components
    #   Example: 'Serial3/4/5.6:7 multipoint'
    ##########################################################################
    # The base ciscoconfparse/ccp_util.py CiscoInterface() instance
    intf_cisco_interface = ccp_obj.interface_object
    # The ciscoconfparse/ccp_util.py CiscoInterface() name, 'Serial3/4/5.6:7 multipoint'
    intf_name = ccp_obj.interface_object.name
    # The ciscoconfparse/ccp_util.py CiscoInterface() prefix, 'Serial'
    intf_prefix = ccp_obj.interface_object.prefix
    # The ciscoconfparse/ccp_util.py CiscoInterface() digit separator, '/'
    digit_separator = ccp_obj.interface_object.digit_separator or ""
    # The ciscoconfparse/ccp_util.py CiscoInterface() slot, 3
    intf_slot = ccp_obj.interface_object.slot or ""
    # The ciscoconfparse/ccp_util.py CiscoInterface() card, 4
    intf_card = ccp_obj.interface_object.card or ""
    # The ciscoconfparse/ccp_util.py CiscoInterface() card, 5
    intf_port = ccp_obj.interface_object.port
    # The ciscoconfparse/ccp_util.py CiscoInterface() subinterface, 6
    intf_subinterface = ccp_obj.interface_object.subinterface or ""
    # The ciscoconfparse/ccp_util.py CiscoInterface() channel, 7
    intf_channel = ccp_obj.interface_object.channel or ""
    # The ciscoconfparse/ccp_util.py CiscoInterface() interface_class, 'multipoint'
    intf_class = ccp_obj.interface_object.interface_class or ""

    ##########################################################################
    # Extract all IPv4Obj() with re_match_iter_typed()
    ##########################################################################
    _default = None
    for _obj in ccp_obj.children:
        # Get a dict() from re_match_iter_typed() by caling it with 'groupdict'
        intf_dict = _obj.re_match_iter_typed(
            # Add a regex match-group called 'v4addr'
            r"ip\s+address\s+(?P<v4addr>\S.+?\d)\s*(?P<secondary>secondary)*$",
            # Cast the v4addr regex match group as an IPv4Obj() type
            groupdict={"v4addr": IPv4Obj, "secondary": str},
            # Default to None if there is no regex match
            default=_default,
        )
        intf_ipv4obj = intf_dict["v4addr"]

    ##########################################################################
    # Extract all IPv6Obj() with re_match_iter_typed()
    ##########################################################################
    _default = None
    for _obj in ccp_obj.children:
        # Get a dict() from re_match_iter_typed() by caling it with 'groupdict'
        intf_dict = _obj.re_match_iter_typed(
            # Add regex match-groups called 'v6addr' and an optional 'ipv6type'
            r"ipv6\s+address\s+(?P<v6addr>\S.+?\d)\s*(?P<v6type>eui.64|link.local)*$",
            # Cast the v6addr regex match group as an IPv6Obj() type
            groupdict={"v6addr": IPv6Obj, "v6type": str},
            # Default to None if there is no regex match
            default=_default,
        )
        intf_ipv6obj = intf_dict["v6addr"]
        intf_ipv6type = intf_dict["v6type"]
        # Skip this object if it has no IPv6 address
        if intf_ipv6obj is _default:
            continue
```

When that is run, you will see information similar to this...

```
----
Interface FastEthernet0/0: 172.16.2.1/24
  Interface FastEthernet0/0 description: [IPv4 and IPv6 desktop / laptop hosts on 2nd-floor North LAN]

  HSRP Group tracking for {'FastEthernet0/0'}
  --- HSRP Group 110 ---
    --- Tracking Dialer1 ---
    Tracking interface: Dialer1
    Tracking decrement: 75
    Tracking weighting: None
    --- Tracking FastEthernet 0/1 ---
    Tracking interface: FastEthernet 0/1
    Tracking decrement: 10
    Tracking weighting: None
    --- Tracking FastEthernet1/0 ---
    Tracking interface: FastEthernet1/0
    Tracking decrement: 30
    Tracking weighting: None
  --- HSRP Group 111 ---
    --- Tracking Dialer1 ---
    Tracking interface: Dialer1
    Tracking decrement: 50
    Tracking weighting: None
GRP {'addr': <IPv6Obj fd01:ab00::/64>}
RESULT <IOSIntfLine # 231 'FastEthernet0/0' primary_ipv4: '172.16.2.1/24'> <IPv6Obj fd01:ab00::/64>
```


## Are there private copies of CiscoConfParse()?

Yes.  [Cisco Systems][27] maintains their own copy of `CiscoConfParse()`. The terms of the GPLv3
license allow this as long as they don't distribute their modified private copy in
binary form.  Also refer to this [GPLv3 License primer / GPLv3 101][45].  Officially, [modified
copies of CiscoConfParse source-code must also be licensed as GPLv3][45].

Dear [Cisco Systems][27]: please consider porting your improvements back into
the [`github ciscoconfparse2 repo`](https://github.com/mpenning/ciscoconfparse2).

## Are you releasing licensing besides GPLv3?

[I will not](https://github.com/mpenning/ciscoconfparse/issues/270#issuecomment-1774035592); however, you can take the solution Cisco does above as long as you comply with the GPLv3 terms.  If it's truly a problem for your company, there are commercial solutions available (to include purchasing the project, or hiring me).

## What if we don\'t use Cisco IOS?

Don\'t let that stop you.

As of original CiscoConfParse 1.2.4, you can parse [brace-delimited configurations][13] into a Cisco IOS style (see [Github Issue \#17][14]), which means that CiscoConfParse can parse these configurations:

- Juniper Networks Junos
- Palo Alto Networks Firewall configurations
- F5 Networks configurations

CiscoConfParse also handles anything that has a Cisco IOS style of configuration, which includes:

- Cisco IOS, Cisco Nexus, Cisco IOS-XR, Cisco IOS-XE, Aironet OS, Cisco ASA, Cisco CatOS
- Arista EOS
- Brocade
- HP Switches
- Force 10 Switches
- Dell PowerConnect Switches
- Extreme Networks
- Enterasys
- Screenos

## Docs

- Blogs
  - Kirk Byers published [a ciscoconfparse blog piece](https://pynet.twb-tech.com/blog/parsing-configurations-w-ciscoconfparse.html)
  - Henry Ölsner published [a ciscoconfparse blog piece](https://codingnetworker.com/2016/06/parse-cisco-ios-configuration-ciscoconfparse/)
- The latest copy of the docs are [archived on the web][15]
- There is also a [CiscoConfParse Tutorial][16]

## Installation and Downloads

-   Use `poetry` for Python3.x\... :

        python -m pip install ciscoconfparse2

## What is the pythonic way of handling script credentials?

1. Never hard-code credentials
2. Use [python-dotenv](https://github.com/theskumar/python-dotenv)


## Is this a tool, or is it artwork?

That depends on who you ask.  Many companies use CiscoConfParse as part of their
network engineering toolbox; others regard it as a form of artwork.

## Pre-requisites

[The ciscoconfparse2 python package][3] requires Python versions 3.7+ (note: Python version 3.7.0 has a bug - ref [Github issue \#117][18], but version 3.7.1 works); the OS should not matter.


## Other Resources

- [Dive into Python3](http://www.diveintopython3.net/) is a good way to learn Python
- [Team CYMRU][30] has a [Secure IOS Template][29], which is especially useful for external-facing routers / switches
- [Cisco\'s Guide to hardening IOS devices][31]
- [Center for Internet Security Benchmarks][32] (An email address, cookies, and javascript are required)

## Bug Tracker and Support

- Please report any suggestions, bug reports, or annoyances with a [github bug report][24].
- If you\'re having problems with general python issues, consider searching for a solution on [Stack Overflow][33].  If you can\'t find a solution for your problem or need more help, you can [ask on Stack Overflow][34] or [reddit/r/Python][39].
- If you\'re having problems with your Cisco devices, you can contact:
  - [Cisco TAC][28]
  - [reddit/r/Cisco][35]
  - [reddit/r/networking][36]
  - [NetworkEngineering.se][23]

## Dependencies

- [Python 3](https://python.org/)
- [attrs](https://github.com/python-attrs/attrs)
- [passlib](https://github.com/glic3rinu/passlib)
- [toml](https://github.com/uiri/toml)
- [dnspython](https://github.com/rthalley/dnspython)
- [hier_config](https://github.com/netdevops/hier_config)
- [loguru](https://github.com/Delgan/loguru)
- [deprecated](https://github.com/tantale/deprecated)


## Unit-Tests and Development

- We are manually disabling some [SonarCloud](https://sonarcloud.io/) alerts with:
  - `#pragma warning disable S1313`
  - `#pragma warning restore S1313`
  - Where `S1313` is a False-positive that [SonarCloud](https://sonarcloud.io) flags in [CiscoConfParse](https://github.com/mpenning/ciscoconfparse2/).
  - Those `#pragma warning` lines should be carefully-fenced to ensure that we don't disable a [SonarCloud](https://sonarcloud.io/) alert that is useful.

### Semantic Versioning and Conventional Commits

- At this point, [ciscoconfparse2][3] does NOT adhere to [Semantic Versioning][49]
- Although we added [commitizen][48] as a dev dependency, we are NOT enforcing commit rules (such as [Conventional Commits][50]) yet.

### Execute Unit tests

The project\'s [test workflow][1] checks ciscoconfparse2 on Python versions 3.7 and higher, as well as a [pypy JIT][22] executable.

If you already git cloned the repo and want to manually run tests either run with `make test` from the base directory, or manually run with [`pytest`][63] in a unix-like system...

```shell
$ cd tests
$ pytest ./test*py
...
```

### Execute Test Coverage Line-Miss Report

If you already have have `pytest` and `pytest-cov` installed, run a test line miss report as shown below.

```shell
$ # Install the latest ciscoconfparse2
$ # (assuming the latest code is on pypi)
$ pip install -U ciscoconfparse2
$ pip install -U pytest-cov
$ cd tests
$ pytest --cov-report=term-missing --cov=ciscoconfparse2 ./
...
```


## Editing the Package

This uses the example of editing the package on a git branch called `develop`...

-   `git clone https://github.com/mpenning/ciscoconfparse2`
-   `cd ciscoconfparse2`
-   `git branch develop`
-   `git checkout develop`
-   Add / modify / delete on the `develop` branch
-   `make test`
-   If tests run clean, `git commit` all the pending changes on the `develop` branch
-   If you plan to publish this as an official version rev, edit the version number in [pyproject.toml][12].  In the future, we want to integrate `commitizen` to manage versioning.
-   `git checkout main`
-   `git merge develop`
-   `make test`
-   `git push origin main`
-   `make pypi`

## Sphinx Documentation

Building the ciscoconfparse2 documentation tarball comes down to this one wierd trick:

- `cd sphinx-doc/`
- `pip install -r ./requirements.txt;  # install Sphinx dependencies`
- `pip install -r ../requirements.txt; # install ccp dependencies`
- `make html`

## License and Copyright

[ciscoconfparse2][3] is licensed [GPLv3][21]

- Copyright (C) 2023 David Michael Pennington

The word \"Cisco\" is a registered trademark of [Cisco Systems][27].

## Author

[ciscoconfparse2][3] was written by [David Michael Pennington][25] (mike \[\~at\~\] pennington \[.dot.\] net).



  [1]: https://github.com/mpenning/ciscoconfparse2/blob/main/.github/workflows/tests.yml
  [2]: https://img.shields.io/pypi/v/ciscoconfparse2.svg
  [3]: https://pypi.python.org/pypi/ciscoconfparse2/
  [4]: https://github.com/mpenning/ciscoconfparse2/actions/workflows/tests.yml/badge.svg
  [5]: https://github.com/mpenning/ciscoconfparse2/actions/workflows/tests.yml
  [6]: https://pepy.tech/badge/ciscoconfparse2
  [7]: https://pepy.tech/project/ciscoconfparse2
  [8]: http://img.shields.io/badge/license-GPLv3-blue.svg
  [9]: https://www.gnu.org/copyleft/gpl.html
  [10]: https://www.python.org
  [11]: https://raw.githubusercontent.com/mpenning/ciscoconfparse/master/sphinx-doc/_static/ciscoconfparse_overview_75pct.png
  [12]: https://github.com/mpenning/ciscoconfparse2/blob/main/pyproject.toml
  [13]: https://github.com/mpenning/ciscoconfparse2/blob/master/configs/sample_01.junos
  [14]: https://github.com/mpenning/ciscoconfparse/issues/17
  [15]: http://www.pennington.net/py/ciscoconfparse2/
  [16]: http://pennington.net/tutorial/ciscoconfparse2/ccp_tutorial.html
  [17]: https://github.com/mpenning/ciscoconfparse2
  [18]: https://github.com/mpenning/ciscoconfparse/issues/117
  [19]: https://github.com/mpenning/ciscoconfparse/issues/13
  [20]: https://github.com/CrackerJackMack/
  [21]: http://www.gnu.org/licenses/gpl-3.0.html
  [22]: https://pypy.org
  [23]: https://networkengineering.stackexchange.com/
  [24]: https://github.com/mpenning/ciscoconfparse2/issues/new/choose
  [25]: https://github.com/mpenning
  [26]: https://github.com/muir
  [27]: https://www.cisco.com/
  [28]: https://www.cisco.com/go/support
  [29]: https://www.cymru.com/Documents/secure-ios-template.html
  [30]: https://team-cymru.com/company/
  [31]: http://www.cisco.com/c/en/us/support/docs/ip/access-lists/13608-21.html
  [32]: https://learn.cisecurity.org/benchmarks
  [33]: https://stackoverflow.com
  [34]: http://stackoverflow.com/questions/ask
  [35]: https://www.reddit.com/r/Cisco/
  [36]: https://www.reddit.com/r/networking
  [37]: https://snyk.io/advisor/python/ciscoconfparse2/badge.svg
  [38]: https://snyk.io/advisor/python/ciscoconfparse2
  [39]: https://www.reddit.com/r/Python/
  [41]: https://img.shields.io/github/commit-activity/m/mpenning/ciscoconfparse2
  [42]: https://img.shields.io/github/commit-activity/m/mpenning/ciscoconfparse2
  [43]: https://www.codefactor.io/Content/badges/B.svg
  [44]: https://www.codefactor.io/repository/github/mpenning/ciscoconfparse2/
  [45]: https://fossa.com/blog/open-source-software-licenses-101-gpl-v3/
  [46]: https://app.codacy.com/project/badge/Grade/4774ebb0292d4e1d9dc30bf263d9df14
  [47]: https://app.codacy.com/gh/mpenning/ciscoconfparse2/dashboard
  [48]: https://commitizen-tools.github.io/commitizen/
  [49]: https://semver.org/
  [50]: https://www.conventionalcommits.org/en/v1.0.0/
  [51]: https://sonarcloud.io/api/project_badges/measure?project=mpenning_ciscoconfparse2&metric=alert_status
  [52]: https://sonarcloud.io/summary/new_code?id=mpenning_ciscoconfparse2
  [53]: https://sonarcloud.io/api/project_badges/measure?project=mpenning_ciscoconfparse2&metric=sqale_rating
  [54]: https://sonarcloud.io/summary/new_code?id=mpenning_ciscoconfparse2
  [55]: https://sonarcloud.io/api/project_badges/measure?project=mpenning_ciscoconfparse2&metric=ncloc
  [56]: https://sonarcloud.io/summary/new_code?id=mpenning_ciscoconfparse2
  [57]: https://sonarcloud.io/api/project_badges/measure?project=mpenning_ciscoconfparse2&metric=code_smells
  [58]: https://sonarcloud.io/summary/new_code?id=mpenning_ciscoconfparse2
  [59]: https://sonarcloud.io/api/project_badges/measure?project=mpenning_ciscoconfparse2&metric=bugs
  [60]: https://sonarcloud.io/summary/new_code?id=mpenning_ciscoconfparse2
  [61]: https://sonarcloud.io/api/project_badges/measure?project=mpenning_ciscoconfparse2&metric=sqale_index
  [62]: https://sonarcloud.io/summary/new_code?id=mpenning_ciscoconfparse2
  [63]: https://docs.pytest.org/en/
