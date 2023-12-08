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
from ciscoconfparse2 import CiscoConfParse

parse = CiscoConfParse('exampleswitch.conf', syntax='ios')

for intf_obj in parse.find_parent_objects('^interface', '^\s+shutdown'):
    print("Shutdown: " + intf_obj.text)
```

The next example will find the IP address assigned to interfaces.

```python
from ciscoconfparse2 import CiscoConfParse

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

CiscoConfParse has a special feature that abstracts common IOS / NXOS / ASA / IOSXR fields; at this time, it is only supported on those configuration types. You will see factory parsing in CiscoConfParse code as parsing the configuration with `factory=True`.

## Are you releasing licensing besides GPLv3?

I will not. however, if it's truly a problem for your company, there are commercial solutions available (to include purchasing the project, or hiring me).

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

- The latest copy of the docs are [archived on the web][15]

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
  - Where `S1313` is a False-positive that [SonarCloud](https://sonarcloud.io) flags
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
