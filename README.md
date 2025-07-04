[![logo][66]][66]

# ciscoconfparse2

[![git commits][41]][42] [![Version][2]][3] [![Downloads][6]][7] [![License][8]][9] [![Hatch project][68]][69]

[![SonarCloud][51]][52] [![SonarCloud Maintainability Rating][53]][54] [![SonarCloud Lines of Code][55]][56] [![SonarCloud Bugs][59]][60] [![SonarCloud Code Smells][57]][58] [![SonarCloud Tech Debt][61]][62]

# Introduction: What is ciscoconfparse2?

## Summary

[ciscoconfparse2][17] is similar to an advanced grep and diff that
handles **multi-vendor network configuration files** (such as those from
Arista, Cisco, F5, Juniper, Palo Alto, etc); it is the next generation of
[ciscoconfparse][64], which was the primary development package
from 2007 until 2023.

## A ciscoconfparse2 example

Assume you have a bunch of interfaces in a configuration.  How do you find which ones are shutdown?

One way is manually reading the whole Cisco IOS-XE configuration.  Another option is [ciscoconfparse2][17]

```python
>>> from ciscoconfparse2 import CiscoConfParse
>>>
>>> parse = CiscoConfParse('/path/to/config/file')
>>> intf_cmds = parse.find_parent_objects(['interface', 'shutdown'])
>>>
>>> shut_intf_names = [" ".join(cmd.split()[1:]) for cmd in intf_cmds]
>>>
>>> shut_intf_names
['GigabitEthernet1/5', 'TenGigabitEthernet2/2', 'TenGigabitEthernet2/3']
>>>
```


## Another ciscoconfparse2 example

Assume you have this IOS-XR bgp configuration:

```none
router bgp 65534
  bgp router-id 10.0.0.100
  address-family ipv4 unicast
  !
  neighbor 10.0.0.37
    remote-as 64000
    route-policy EBGP_IN in
    route-policy EBGP_OUT out
  !
  neighbor 10.0.0.1
    remote-as 65534
    update-source Loopback0
    route-policy MANGLE_IN in
    route-policy MANGLE_OUT out
      next-hop-self
  !
  neighbor 10.0.0.34
    remote-as 64000
    route-policy EBGP_IN in
    route-policy EBGP_OUT out
```

You can generate the list of EBGP peers pretty quickly with this script:

```python
from ciscoconfparse2 import CiscoConfParse

parse = CiscoConfParse('/path/to/config/file')   # Or read directly from a list of strings

# Get all neighbor configuration branches
branches = parse.find_object_branches(('router bgp',
                                       'neighbor',
                                       'remote-as'))

# Get the local BGP ASN
bgp_cmd = branches[0][0]
local_asn = bgp_cmd.split()[-1]

# Find EBGP neighbors for any number of peers
for branch in branches:
    neighbor_addr = branch[1].split()[-1]
    remote_asn = branch[2].split()[-1]
    if local_asn != remote_asn:
        print("EBGP NEIGHBOR", neighbor_addr)
```

When you run that, you'll see:

```none
$ python example.py
EBGP NEIGHBOR 10.0.0.37
EBGP NEIGHBOR 10.0.0.34
$
```

There is a lot more possible; see the [tutorial](http://www.pennington.net/py/ciscoconfparse2/tutorial.html).

## CLI Tool

[ciscoconfparse2][17] distributes a [CLI tool][67] that will diff and grep various
network configuration or text files.

## API Examples

The API examples are [documented on the web][70]


# Why

[ciscoconfparse2][17] is a [Python][10] library
that helps you quickly search for questions like these in your
router / switch / firewall / load-balancer / wireless text
configurations:

- What interfaces are shutdown?
- Which interfaces are in trunk mode?
- What address and subnet mask is assigned to each interface?
- Which interfaces are missing a critical command?
- Is this configuration missing a standard config line?

It can help you:

- Audit existing router / switch / firewall / wlc configurations
- Modify existing configurations
- Build new configurations

Speaking generally, the library examines a text network config and breaks
it into a set of linked parent / child relationships. You can perform
complex queries about these relationships.

[![Cisco IOS config: Parent / child][11]][11]

## What changed in ciscoconfparse2?

In late 2023, I started a rewrite because [ciscoconfparse][64] is too large
and has some defaults that I wish it didn't have.  I froze
[ciscoconfparse][64] PYPI releases at [version 1.9.52][65]; there will be no
more [ciscoconfparse][64] PYPI releases.

What do you do?  Upgrade to [ciscoconfparse2][17]!

Here's why, it:

- Includes a handy [CLI command][67] (including greps for mac addresses and IPv4 / IPv6 subnets)
- Streamlines the API towards a simpler user interface.
- Removes legacy and flawed methods from the original (this could be a breaking change for old scripts).
- Adds string methods to `BaseCfgLine()` objects
- Defaults `ignore_blank_lines=False` (this could be a breaking change for old scripts).
- Is better at handling multiple-child-level configurations (such as IOS XR and JunOS)
- Can search for parents and children using an *arbitrary list of ancestors*
- Adds the concept of change commits; this is a config-modification safety feature that [ciscoconfparse][64] lacks
- Adds an `auto_commit` keyword, which defaults True
- Documents much more of the API
- Intentionally requires a different import statement to minimize confusion between the original and [ciscoconfparse2][17]
- Vasly improves Cisco IOS diffs

# Docs, Installation, and Dependencies

- The latest copy of the docs are [archived on the web][15]

## Installation and Downloads

-   Use `pip` for Python3.x\... :

        python -m pip install ciscoconfparse2

## Dependencies

- [Python 3](https://python.org/)
- [attrs](https://github.com/python-attrs/attrs)
- [passlib](https://github.com/glic3rinu/passlib)
- [dnspython](https://github.com/rthalley/dnspython)
- [`hier_config`](https://github.com/netdevops/hier_config)
- [`scrypt`](https://github.com/holgern/py-scrypt)
- [`PyYAML`](https://github.com/yaml/pyyaml)
- [`macaddress`](https://github.com/mentalisttraceur/python-macaddress)
- [`pyparsing`](https://github.com/pyparsing/pyparsing)
- [`traitlets`](https://github.com/ipython/traitlets)
- [`rich`](https://github.com/Textualize/rich)
- [`typeguard`](https://github.com/agronholm/typeguard)
- [loguru](https://github.com/Delgan/loguru)


## Pre-requisites

[The ciscoconfparse2 python package][3] requires Python versions 3.9+.

## What is the pythonic way of handling script credentials?

1. Never hard-code credentials
2. Use [python-dotenv](https://github.com/theskumar/python-dotenv)

# Other Resources

- [Dive into Python3](http://www.diveintopython3.net/) is a good way to learn Python
- [Team CYMRU][30] has a [Secure IOS Template][29], which is especially useful for external-facing routers / switches
- [Cisco\'s Guide to hardening IOS devices][31]
- [Center for Internet Security Benchmarks][32] (An email address, cookies, and javascript are required)

## Are you releasing licensing besides GPLv3?

I will not. however, if it's truly a problem for your company, there are commercial solutions available (to include purchasing the project, or hiring me).

## Bug Tracker and Support

- Please report any suggestions, bug reports, or annoyances with a [github bug report][24].
- If you\'re having problems with general python issues, consider searching for a solution on [Stack Overflow][33].  If you can\'t find a solution for your problem or need more help, you can [ask on Stack Overflow][34] or [reddit/r/Python][39].
- If you\'re having problems with your Cisco devices, you can contact:
  - [Cisco TAC][28]
  - [reddit/r/Cisco][35]
  - [reddit/r/networking][36]
  - [NetworkEngineering.se][23]

# License and Copyright

[ciscoconfparse2][3] is licensed [GPLv3][21]

- Copyright (C) 2023-2024 David Michael Pennington

The word \"Cisco\" is a registered trademark of [Cisco Systems][27].

# Author

[ciscoconfparse2][3] was written by [David Michael Pennington][25].



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
  [64]: https://github.com/mpenning/ciscoconfparse
  [65]: https://pypi.org/project/ciscoconfparse/1.9.52/
  [66]: https://raw.githubusercontent.com/mpenning/ciscoconfparse2/main/sphinx-doc/_static/ciscoconfparse_logo_bw_01.png
  [67]: http://www.pennington.net/py/ciscoconfparse2/cli.html
  [68]: https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg
  [69]: https://github.com/pypa/hatch
  [70]: http://www.pennington.net/py/ciscoconfparse2/examples.html
