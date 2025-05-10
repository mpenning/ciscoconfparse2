# {class}`~ciscoconfparse2` Configuration branches

We have already seen how to use parents and children to find configuration relationships, but sometimes it's helpful to get the parent and it's children (plus any children of children) all at once.  {class}`~ciscoconfparse2` calls this object branches.

Let's look at an example of getting object branches with {func}`~ciscoconfparse2.CiscoConfParse.find_object_branches`.

```{code-block} python
:emphasize-lines: 9,13,16,19
>>> from ciscoconfparse2 import CiscoConfParse
>>> config = """!
... router bgp 65534
...  neighbor 10.0.0.1
...   remote-as 65534
... """
>>> parse = CiscoConfParse(config)
>>>
>>> branches = parse.find_object_branches((r'router bgp', r'neighbor', r'remote-as'))
>>> branches
[Branch(['router bgp 65534', ' neighbor 10.0.0.1', '  remote-as 65534'])]
>>>
>>> branches[0][0]
<IOSCfgLine # 1 'router bgp 65534'>
>>>
>>> branches[0][1]
<IOSCfgLine # 2 ' neighbor 10.0.0.1' (parent is # 1)>
>>>
>>> branches[0][2]
<IOSCfgLine # 3 '  remote-as 65534' (parent is # 2)>
>>>
```

As you can see, with one query we got three config statements:

* The parent: `router bgp 65534`
* The child: ` neighbor 10.0.0.1`
* The grandchild: `  remote-as 65534`

There may be times when it's better to avoid looping through individual children and just get the whole configuration branch all at once.
