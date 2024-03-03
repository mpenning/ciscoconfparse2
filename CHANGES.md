## Version: GIT HEAD

- Released: Not released
- Summary:
    - Insert something here

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
