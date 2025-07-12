## Version: GIT HEAD

- Released: Not released
- Summary:
    - Insert something here

## Version: 0.8.23

- Released: 2025-07-12
- Summary:
    - Replace https://pypi.org/project/scrypt/ with `hashlib.scrypt()`

## Version: 0.8.22

- Released: 2025-07-04
- Summary:
    - attempting to retire use of passlib==1.7.4, which is now unmaintained.  [`libpass`][2] will be used instead...

## Version: 0.8.21

- Released: 2025-07-04
- Summary:
    - Add hypothesis `IPv4Obj()` and `IPv6Obj()` tests
    - Remove unused sshd mock
    - Remove tomlkit and tox as dev dependencies
    - Update typeguard to the latest version
    - Remove `requirements/` directory

## Version: 0.8.20

- Released: 2025-05-17
- Summary:
    - Add initial context-manager support to `CiscoConfParse()`
    - Add initial context-manager support to `ConfigList()`
    - Remove support for the `ConfigList().CiscoConfParse` attribute
    - Implement `traitlets` on non-container objects instead of typeguard

## Version: 0.8.19

- Released: 2025-05-17
- Summary:
    - Make dev dependencies explicit

## Version: 0.8.18

- Released: 2025-05-17
- Summary:
    - Add dependabot runs on a dedicated `dependabot-pr` branch
    - Bump `heir_config` to version 2.3.1
    - Bump `typeguard` to version 4.4.2
    - Bump development dependencies
    - Add a `router isis` Diff test
    - Update to Sphinx version 8.x
    - Fix some documentation build bugs

## Version: 0.8.17

- Released: 2025-05-10
- Summary:
    - Port .pre-commit-config.yaml from ciscoconfparse
    - Run pre-commit and commit changes in Makefile
    - Run yamlfix and commit changes in Makefile

## Version: 0.8.16

- Released: 2025-05-10
- Summary:
    - Rename create release workflow

## Version: 0.8.15

- Released: 2025-05-10
- Summary:
    - Remove duplicate SonarCloud workflow scanner
    - Add automatic Github Release on git tag

## Version: 0.8.14

- Released: 2025-05-10
- Summary:
    - Refactor loguru handlers code

## Version: 0.8.13

- Released: 2025-05-10
- Summary:
    - Update loguru package name and add more debug logging

## Version: 0.8.12

- Released: 2025-05-10
- Summary:
    - Upgrade setup-python to v5

## Version: 0.8.11

- Released: 2025-05-10
- Summary:
    - Revert loguru error on pyparsing failure

## Version: 0.8.10

- Released: 2025-05-10
- Summary:
    - Add loguru error on pyparsing failure

## Version: 0.8.9

- Released: 2025-05-04
- Summary:
    - Fix SonarCloud password hash iteration alert

## Version: 0.8.8

- Released: 2025-05-04
- Summary:
    - Fix CiscoConfParse(loguru=False)

## Version: 0.8.7

- Released: 2025-03-02
- Summary:
    - Fix duplicated test names
    - Improve code quality
    - Remove native CLI optparse argument parsing.  Use `ciscoconfparse2.cli_script` instead.

## Version: 0.8.6

- Released: 2025-03-02
- Summary:
    - Improve test coverage measurement

## Version: 0.8.5

- Released: 2025-03-02
- Summary:
    - Relocate `coverage.xml`

## Version: 0.8.4

- Released: 2025-03-02
- Summary:
    - Add `tests/coverage.xml`


## Version: 0.8.3

- Released: 2025-03-02
- Summary:
    - Remove strings which annoy SonarQube

## Version: 0.8.2

- Released: 2025-03-02
- Summary:
    - Bump copyrights to include 2025
    - run `black` on some files
    - Fix many pylint flags
    - Fix `CiscoRange().insert()` and add tests for it
    - Improve `CiscoRange().member_type`
    - Improve `CiscoRange().text`
    - Remove `CiscoRange().parse_floats()`
    - Fix `repr(CiscoRange())`

## Version: 0.8.1

- Released: 2025-03-02
- Summary:
    - Bump `gh-action-pypi-publish` version

## Version: 0.8.0

- Released: 2025-03-02
- Summary:
    - Bump hatchling requirement at least 1.26.3
    - Modify `embold.yaml` to explicitly scan as Python
    - Aggregate changes since version 0.7.0 warrant a minor version change at this point

## Version: 0.7.83

- Released: 2025-02-09
- Summary:
    - Relax `attrs` version requirements in `pyproject.toml`

## Version: 0.7.82

- Released: 2025-01-04
- Summary:
    - Tweak comment in IPv6Obj()

## Version: 0.7.81

- Released: 2025-01-04
- Summary:
    - Tweak algorithm to get a decimal representation of an IPv6Obj()

## Version: 0.7.80

- Released: 2025-01-04
- Summary:
    - Add more error-checking for IPv4 embedded in IPv6

## Version: 0.7.79

- Released: 2025-01-04
- Summary:
    - Attempt to fix problems with IPv4 addresses embedded in IPv6Obj (such as '::ffff:192.0.2.4')

## Version: 0.7.78

- Released: 2025-01-04
- Summary:
    - Make explicit comments about the source reference for Cisco Type 8 and 9 hashes
    - Add Python3.13 to the test matrix
    - Deprecate support for Python3.8 (it went end of life in October 2024)

## Version: 0.7.77

- Released: 2025-01-04
- Summary:
    - Attempt to fix version publishing due to changes in `gh-action-pypi-publish`

## Version: 0.7.76

- Released: 2025-01-04
- Summary:
    - Remove crypt-r due to it missing in python 3.10 and lower

## Version: 0.7.75

- Released: 2025-01-04
- Summary:
    - Fix [Github issue #12](https://github.com/mpenning/ciscoconfparse2/issues/12) related to ciscoconfparse2 pickling
    - Update for [Github issue #15](https://github.com/mpenning/ciscoconfparse2/issues/15) related to ciscoconfparse2 pyyaml dependency conflict with netmiko 4.5.0
    - Fix missing dunder methods in `models_junos.py`
    - Change several version dependencies in `pyproject.toml` to be more flexible (ref: github issue #15)
    - Update tests


## Version: 0.7.74

- Released: 2024-07-06
- Summary:
    - Implement `BaseCfgLinne().__getitem__()` string slicing method
    - Update tests
    - Update documentation

## Version: 0.7.73

- Released: 2024-07-04
- Summary:
    - Automatically parse multi-line string inputs into `CiscoConfParse()` instead of requiring a manual `str().splitlines()`
    - Replace `list()` with an explicit `Branch()` object in `CiscoConfParse().find_object_branches()`
    - Update tests
    - Update documentation

## Version: 0.7.72

- Released: 2024-06-30
- Summary:
    - Update Makefile such that version tags are optional

## Version: 0.7.71

- Released: 2024-06-30
- Summary:
    - Update documentation

## Version: 0.7.70

- Released: 2024-06-30
- Summary:
    - Update documentation

## Version: 0.7.69

- Released: 2024-06-30
- Summary:
    - Update documentation

## Version: 0.7.68

- Released: 2024-06-30
- Summary:
    - Add markdown support to documentation tree
    - Simplify `README.md`
    - Update Sphinx version to 6.2.1
    - Add [`MyRST`](https://github.com/executablebooks/MyST-Parser/) as a dev dependency
    - Add `requirements/requirements-dev.txt`

## Version: 0.7.67

- Released: 2024-06-29
- Summary:
    - fix: Make `BaseCfgLine().__str__()` return `BaseCfgLine().text`

## Version: 0.7.66

- Released: 2024-06-29
- Summary:
    - feat: Add `__contains__()` and `__iter__()` support to `BaseCfgLine()`
    - chore: add more tests

## Version: 0.7.65

- Released: 2024-06-29
- Summary:
    - chore: More documentation updates

## Version: 0.7.64

- Released: 2024-06-29
- Summary:
    - chore: Update documentation with examples

## Version: 0.7.63

- Released: 2024-06-22
- Summary:
    - chore: remove `/usr/bin/env` calls in `tests/`
    - Update package editing instructions in the `README.md` file

## Version: 0.7.62

- Released: 2024-05-28
- Summary:
    - Add more documentation

## Version: 0.7.61

- Released: 2024-05-28
- Summary:
    - Add more documentation

## Version: 0.7.60

- Released: 2024-05-11
- Summary:
    - Make rust `deploy_docs.rs` return values explicit

## Version: 0.7.59

- Released: 2024-05-11
- Summary:
    - Attempt to shorten github conditional test runner logic

## Version: 0.7.58

- Released: 2024-05-11
- Summary:
    - Attempt to fix github conditional test runner logic

## Version: 0.7.57

- Released: 2024-05-11
- Summary:
    - Attempt to fix github conditional test runner logic


## Version: 0.7.56

- Released: 2024-05-11
- Summary:
    - Attempt to fix github conditional test runner logic

## Version: 0.7.55

- Released: 2024-05-11
- Summary:
    - Update an error message

## Version: 0.7.54

- Released: 2024-05-11
- Summary:
    - Add code comments in `deploy_docs.rs`

## Version: 0.7.53

- Released: 2024-05-11
- Summary:
    - Enhance github workflows test runner

## Version: 0.7.52

- Released: 2024-05-11
- Summary:
    - Add `colog` logging implementation in `deploy_docs.rs` instead of `println!()`

## Version: 0.7.51

- Released: 2024-05-10
- Summary:
    - Add a new `deploy_docs` executable in Rust

## Version: 0.7.50

- Released: 2024-05-07
- Summary:
    - Fix Github issue #11 'global spanning-tree portfast lines create errors', syntax error in `super()` call

## Version: 0.7.49

- Released: 2024-05-05
- Summary:
    - Enhance `hier_config.Host()` call to use nxos, iosxr, and ios syntax natively when calling `Diff()`

## Version: 0.7.48

- Released: 2024-05-02
- Summary:
    - Enhance `hier_config.Host()` call to use nxos, iosxr, and ios syntax natively when calling `Diff()`

## Version: 0.7.47

- Released: 2024-04-27
- Summary:
    - Documentation updates

## Version: 0.7.46

- Released: 2024-04-20
- Summary:
    - Dynamic version rendering in the sphinx installation documentation

## Version: 0.7.45

- Released: 2024-04-16
- Summary:
    - Fix [github issue #9](https://github.com/mpenning/ciscoconfparse2/issues/9) - broken `save_as()`

## Version: 0.7.44

- Released: 2024-04-15
- Summary:
    - Simplify versioning internally

## Version: 0.7.43

- Released: 2024-04-14
- Summary:
    - More hatch versioning fixes

## Version: 0.7.42

- Released: 2024-04-14
- Summary:
    - Fix `pyproject.toml` dynamic versioning typo

## Version: 0.7.41

- Released: 2024-04-14
- Summary:
    - Fix `Makefile` versioning to use the hatch backend

## Version: 0.7.40

- Released: 2024-04-14
- Summary:
    - Migrate to hatch dynamic versioning (i.e. `hatch version 0.7.40` bumps the version in `ciscoconfparse2/__about__.py`)

## Version: 0.7.39

- Released: 2024-04-14
- Summary:
    - Update documentation

## Version: 0.7.38

- Released: 2024-04-10
- Summary:
    - Update documentation

## Version: 0.7.37

- Released: 2024-04-07
- Summary:
    - Add a file `Diff()` unit test
    - Update documentation

## Version: 0.7.36

- Released: 2024-04-06
- Summary:
    - Enhance Makefile to be more resilient for unexpected workflows

## Version: 0.7.35

- Released: 2024-04-06
- Summary:
    - Fix release bug

## Version: 0.7.34

- Released: 2024-04-06
- Summary:
    - Fix bug in `Diff()` for filename inputs

## Version: 0.7.33

- Released: 2024-03-17
- Summary:
    - Add `options_ios.hier_config.yml`

## Version: 0.7.32

- Released: 2024-03-17
- Summary:
    - Update tests

## Version: 0.7.12 - 0.7.31

- Released: 2024-03-17
- Summary:
    - Work on github CI/CD workflow and packaging fixes
    - Migrate from local twine PYPI uploads to gi-action-pypi-publish PYPI uploads
    - Fix cosmetic SonarCloud gripe

## Version: 0.7.11

- Released: 2024-03-16
- Summary:
    - Add `ccp macgrep` command
    - Add `cisco` to the valid `EUI64Obj` formats
    - Add equality methods to `MACObj` and `EUI64Obj`
    - Modify `ccp parent` command, `-S` (`--separator`) to be `-d` (`--delimiter`)
    - Modify `ccp child` command, `-S` (`--separator`) to be `-d` (`--delimiter`)
    - Modify `ccp branch` command, `-S` (`--separator`) to be `-d` (`--delimiter`)
    - Add a `tests/fixtures/plain_text/` directory for things like generic `ccp ipgrep` tests
    - Fix bug in `IPv6Obj()` which silently allowed non-IPv6 characters
    - Temporarily remove IPv6 route factory parsing (needs reimplementation in `models_cisco.py` after the `IPv6Obj()` fix above)
    - Skip `pytest.mark.skip()` tests for `ipv6 route` factory parsing after the `IPv6Obj()` fix
    - Update `hatch` installer configuration in `pyproject.toml`: ref [hatch github issue 1328](https://github.com/pypa/hatch/issues/1328)
    - Expand test cases

## Version: 0.7.10

- Released: 2024-03-10
- Summary:
    - Modify `ccp ipgrep` to support multiple subnets
    - Add more `ccp ipgrep` tests to cover multiple subnets
    - More documentation updates

## Version: 0.7.9

- Released: 2024-03-05
- Summary:
    - Add `--unique` flag to `ccp ipgrep`
    - Add `--line` flag to `ccp ipgrep`
    - Add `--word_delimiter` argument to `ccp ipgrep`
    - Prevent `--subnet` from being used more than once with `ccp ipgrep`
    - Add tests for `ccp` utility
    - Bump `dnspython` and `tomlkit` dependency versions to the latest
    - Misc code refactoring
    - More documentation updates

## Version: 0.7.8

- Released: 2024-03-04
- Summary:
    - Fix problem with `echo '172.16.1.1' | ccp ipgrep -s feed:beef::/64'` (i.e. grepping for different IP versions)
    - Adjust code to address SonarCloud issues introduced in version 0.7.7
    - Raise an `AddressValueError()` if `IPv6Obj()` initialization fails (to be consistent with `IPv4Obj()` behavior).  This could be a breaking change if someone uses `IPv6Obj()` in a try / except
    - Other misc code refactoring

## Version: 0.7.7

- Released: 2024-03-03
- Summary:
    - Misc code refactoring

## Version: 0.7.6

- Released: 2024-03-03
- Summary:
    - Add `ccp branch -s junos` CLI option
    - More documentation updates

## Version: 0.7.5

- Released: 2024-03-03
- Summary:
    - Add `ccp branch -o original` CLI option
    - More documentation updates

## Version: 0.7.4

- Released: 2024-03-03
- Summary:
    - Fix hatch changelog github url
    - Adjust `ccp branch` command commands
    - More documentation updates

## Version: 0.7.3

- Released: 2024-03-03
- Summary:
    - Fix hatch changelog github url
    - Fix `ccp` commands when the search term only contains one element

## Version: 0.7.2

- Released: 2024-03-02
- Summary:
    - Fix github workflows after upgrading to hatch

## Version: 0.7.0

- Released: 2024-03-02
- Summary:
    - Migrate from poetry builds to hatch builds
    - Add new ccp CLI script, installed by hatch

## Version: 0.6.8

- Released: 2024-03-01
- Summary:
    - Update scrypt to version 0.8.24
    - More documentation updates

## Version: 0.6.7

- Released: 2024-02-22
- Summary:
    - Fix missing `self`
    - Add test for hashing cisco type 5 and cisco type 8 passwords

## Version: 0.6.6

- Released: 2024-02-22
- Summary:
    - Remove `backports` as a dependendency

## Version: 0.6.5

- Released: 2024-02-22
- Summary:
    - Add missing configuration

## Version: 0.6.4

- Released: 2024-02-22
- Summary:
    - Fix `pyproject.toml` complaints about backports

## Version: 0.6.3

- Released: 2024-02-22
- Summary:
    - Fix missing backports requirement

## Version: 0.6.2

- Released: 2024-02-22
- Summary:
    - Add example SDWAN configuration as `sample_10.ios`.  Thanks to [sjhloco@github](https://github.com/sjhloco/sdwan_bgp_lab/issues/1) for permission to use his SDWAN lab configuration.
    - Rename `CiscoPassword()` type 7 password methods
    - Add cisco password ecryption for type 5, type 8 and type 9 passwords
    - More documentation updates

## Version: 0.6.1

- Released: 2024-02-17
- Summary:
    - Enforce requirement for at least python 3.9
    - More documentation updates

## Version: 0.6.0

- Released: 2024-02-14
- Summary:
    - Fix comment-detection bug
    - More documentation updates

## Version: 0.5.1

- Released: 2024-02-12
- Summary:
    - Remove [deprecated](https://pypi.org/project/Deprecated/) as a dependency
    - Add `typeguard` as a dependency
    - Add `pyparsing` as a dependency
    - Reimplement `BraceParse()` with `pyparsing`
    - Fix `junos` pytest race-condition in CiscoConfParse when `factory` and `ignore_blank_lines` are both True
    - Fix some type annotations
    - More documentation updates

## Version: 0.5.0

- Released: 2024-02-05
- Summary:
    - Fix attributes in JunosCfgLine
    - Fix attributes in BaseCfgLine
    - Replace `parse_line_braces()` with `BraceParse()` to fix original [ciscoconfparse issue #287](https://github.com/mpenning/ciscoconfparse/issues/287)

## Version: 0.4.2

- Released: 2024-01-30
- Summary:
    - Add more HSRP support
    - More documentation updates

## Version: 0.4.1

- Released: 2024-01-14
- Summary:
    - BREAKING CHANGE Rename `hsrp_interface_groups` property to `get_hsrp_groups()` method
    - More documentation updates

## Version: 0.4.0

- Released: 2024-01-10
- Summary:
    - Add `re_list_iter_typed()` to return a list of all child matches
    - Add `MACObj()` and `EUI64Obj()`
    - BREAKING CHANGE:  Replace all `models_nxos.py` and `models_iosxr.py` code with a copy of `models_cisco.py` since there are so many broken parts of the aforementioned NXOS and IOS XR code.  These files will be re-implemented over time.
    - Revise 'make coverage' to only use `coveragepy` instead of the `pytest-cov` plugin
    - Rename 'make pypi-package-infra' as `make dep`
    - More documentation updates

## Version: 0.3.4

- Released: 2024-01-03
- Summary:
    - Remove all `reset()` and `build_reset_string()` methods
    - Add `attrs` to `CiscoIOSInterface()` and `CiscoIOSXRInterface()`
    - Upgrade from `attrs` version 23.1.0 to version 23.2.0.
    - BREAKING CHANGE:  Multiple deletions / changes to factory processing.  Integer defaults were changed from 0 to -1.  Float defaults were changed from 0.0 to -1.0.
    - More documentation updates

## Version: 0.3.3

- Released: 2023-12-21
- Summary:
    - Fix JunOS factory parsing, and enable attrs on JunOS factory classes
    - Add `BaseCfgLine().replace()` method
    - Add `BaseCfgLine().replace_text()` method
    - Remove `CiscoRange()._list` property and setter
    - Documentation updates

## Version: 0.3.2

- Released: 2023-12-19
- Summary:
    - Ensure that all `find_*` methods take a list input
    - Fix `Diff()` to remove the `hostname` kwarg
    - Rename `Diff().diff()` to `Diff().get_diff()`
    - Rename `Diff().rollback()` to `Diff().get_rollback()`
    - Documentation updates

## Version: 0.3.1

- Released: 2023-12-15
- Summary:
    - Add `typing.Optional` to the primary argument for `CiscoConfParse()`, `ConfigList()`, `IPv4Obj()` and `IPv6Obj()`
    - Add string `brace_termination` attribute to `BaseCfgLine()`
    - Remove deprecated methods
    - Documentation updates

## Version: 0.3.0

- Released: 2023-12-15
- Summary:
    - Rename `atomic()` to `commit()` in all places
    - Remove `recurse` keyword from `BaseCfgLine().delete()`
    - Remove unnecessary keywords from several methods
    - Delete several unused methods
    - Remove Python3.8 from `tox.ini` as part of type-hinting support (due to missing `...` in Python3.8 `tuple` type-hint)
    - Documentation updates

## Version: 0.2.5

- Released: 2023-12-14
- Summary:
    - Overhaul `ConfigList().commit()` operations to make them faster on very large configurations
    - Documentation updates

## Version: 0.2.4

- Released: 2023-12-13
- Summary:
    - Remove `BaseCfgLine().uncfgtext` and `CiscoConfParse()._objects_to_uncfg()`
    - Documentation updates

## Version: 0.2.3

- Released: 2023-12-13
- Summary:
    - Modify `BaseCfgLine().strip()`, `BaseCfgLine().lstrip()`, and `BaseCfgLine().rstrip()`
    - Documentation updates

## Version: 0.2.2

- Released: 2023-12-13
- Summary:
    - Convert the `BaseCfgLine().get_indent()` method to a `BaseCfgLine().indent` property
    - Documentation updates

## Version: 0.2.1

- Released: 2023-12-13
- Summary:
    - Fix Python3.8 test failure for `list[str]`, which is not supported until Python3.9

## Version: 0.2.0

- Released: 2023-12-13
- Summary:
    - Fix some `BaseCfgLine().append_to_family()` cases
    - Documentation updates

## Version: 0.1.13

- Released: 2023-12-12
- Summary:
    - Documentation updates
    - Update `escape_chars`

## Version: 0.1.12

- Released: 2023-12-11
- Summary:
    - Documentation updates

## Version: 0.1.11

- Released: 2023-12-11
- Summary:
    - Migrate `pyproject.toml` to [tomlkit](https://github.com/sdispater/tomlkit) version 0.12.3

## Version: 0.1.10

- Released: 2023-12-11
- Summary:
    - Add `reverse` keyword
    - Add [tomlkit](https://github.com/sdispater/tomlkit) version 0.12.3

## Version: 0.1.9

- Released: 2023-12-11
- Summary:
    - Remove debugging print() statements

## Version: 0.1.8

- Released: 2023-12-11
- Summary:
    - Fix missed code deletion

## Version: 0.1.7

- Released: 2023-12-11
- Summary:
    - Fix SonarCloud bugs

## Version: 0.1.6

- Released: 2023-12-11
- Summary:
    - Add test configurations to git repo

## Version: 0.1.5

- Released: 2023-12-11
- Summary:
    - Add test suite to git repo

## Version: 0.1.4

- Released: 2023-12-11
- Summary:
    - Add test suite

## Version: 0.1.1

- Released: 2023-12-01
- Summary:
    - Start new project as `ciscoconfparse2` from the original `ciscoconfparse` version 1.9.51

[1]: http://www.pennington.net/py/ciscoconfparse2/
[2]: https://github.com/notypecheck/passlib
