# Example Usage: Build configuration diffs

Getting diffs is a common need when something happens and you want to know "what changed" between
two configs.  This example will demonstrate how to find diffs between two configurations.

```{note}
Diffs of both files or multi-line strings are supported; however, a single-line string is always understood as a file name.
```

## Baseline Configurations

### `bucksnort_before.conf`

This tutorial will run all the queries this example base configuration, the "before" version is shown below.

```{code-block} none
:linenos: true

! Filename: /tftpboot/bucksnort_before.conf
!
hostname bucksnort
!
interface Ethernet0/0
 ip address 1.1.2.1 255.255.255.0
 no cdp enable
!
interface Serial1/0
 encapsulation ppp
 ip address 1.1.1.1 255.255.255.252
!
interface Serial1/1
 encapsulation ppp
 ip address 1.1.1.5 255.255.255.252
!
```

### `bucksnort_after.conf`

This tutorial will run diff against this example after configuration, which has MPLS enabled on 'Serial1/0'.

```{code-block} none
:linenos: true

! Filename: /tftpboot/bucksnort_after.conf
!
hostname bucksnort
!
interface Ethernet0/0
 ip address 1.1.2.1 255.255.255.0
 no cdp enable
!
interface Serial1/0
 encapsulation ppp
 ip address 1.1.1.1 255.255.255.252
 mpls ip
!
interface Serial1/1
 encapsulation ppp
 ip address 1.1.1.5 255.255.255.252
!
```

## Diff Script

The script below will build read the configurations from disk and check to see whether
there are diffs.

```python
>>> from ciscoconfparse2.ciscoconfparse2 import Diff
>>> # Parse the original configuration
>>> old_config = '/tftpboot/bucksnort_before.conf'
>>> new_config = '/tftpboot/bucksnort_after.conf'
>>> diff = Diff(old_config=old_config, new_config=new_config)
>>> diff.get_diff()
['interface Serial1/0', ' mpls ip']
>>>
>>> for line in diff.get_diff():
...     print(line)
...
!
interface Serial1/0
 mpls ip
!
>>>
```

## Rollback Script

The script below will build read the configurations from disk and build rollback diff configs.

```python
>>> from ciscoconfparse2.ciscoconfparse2 import Diff
>>> # Parse the original configuration
>>> old_config = '/tftpboot/bucksnort_before.conf'
>>> new_config = '/tftpboot/bucksnort_after.conf'
>>> diff = Diff(old_config=old_config, new_config=new_config)
>>> diff.get_rollback()
['interface Serial1/0', ' mpls ip']
>>>
>>> for line in diff.get_rollback():
...     print(line)
...
!
interface Serial1/0
 no mpls ip
!
>>>
```
