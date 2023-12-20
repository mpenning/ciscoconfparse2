## Version: GIT HEAD

- Released: Not released
- Summary:
    - Insert something here

## Version: 0.3.3

- Released: 2023-12-20
- Summary:
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
