from pyMyriad import DataTree, DataNode, LvlDataNode, SplitDataNode


def test_data_tree_empty():
    dt = DataTree()
    assert isinstance(dt, DataTree)
    assert len(dt) == 0
    assert str(dt) == "Data Tree\n"


def test_data_node():
    dn = DataNode(data=[1, 2, 3], summary={"mean": 2}, label="MyData", depth=1)
    assert isinstance(dn, DataNode)
    assert dn.data == [1, 2, 3]
    assert dn.summary == {"mean": 2}
    assert dn.label == "MyData"
    assert dn.depth == 1
    assert str(dn) == "└─ analysis: MyData\n   └─ mean: 2\n"


def test_lvl_data_node():
    dn1 = DataNode(data=[1, 2, 3], summary={"mean": 2}, label="MyData1", depth=1)
    dn2 = DataNode(data=[4, 5, 6], summary={"mean": 5}, label="MyData2", depth=1)
    ldn = LvlDataNode(dn1=dn1, dn2=dn2, split_lvl="Level1", meta={"info": "test"})

    assert isinstance(ldn, LvlDataNode)
    assert ldn.split_lvl == "Level1"
    assert ldn.meta == {"info": "test"}
    assert len(ldn) == 2
    assert "dn1" in ldn
    assert "dn2" in ldn
    assert (
        str(ldn)
        == "└─ Level1\n   ├─ analysis: MyData1\n   │  └─ mean: 2\n   └─ analysis: MyData2\n      └─ mean: 5\n"
    )


def test_split_data_node():
    dn1 = DataNode(data=[1, 2, 3], summary={"mean": 2}, label="MyData1", depth=1)
    dn2 = DataNode(data=[4, 5, 6], summary={"mean": 5}, label="MyData2", depth=1)
    ldn = LvlDataNode(dn1=dn1, dn2=dn2, split_lvl="Level1", meta={"info": "test"})
    sdn = SplitDataNode(split_var="Var1", T=ldn)

    assert isinstance(sdn, SplitDataNode)
    assert sdn.split_var == "Var1"
    assert len(sdn) == 1
    assert "T" in sdn
    assert (
        str(sdn)
        == "└─ Split: Var1\n   └─ Level1\n      ├─ analysis: MyData1\n      │  └─ mean: 2\n      └─ analysis: MyData2\n         └─ mean: 5\n"
    )


def test_lvl_data_node_with_N_list():
    """LvlDataNode stores _N as a list when provided."""
    dn = DataNode(data=[1, 2, 3], summary={"mean": 2}, label="MyData", depth=1)
    ldn = LvlDataNode(dn=dn, split_lvl="Level1", _N=[3, 2])
    assert ldn._N == [3, 2]


def test_data_node_with_N_list():
    """DataNode stores _N as a list when provided."""
    dn = DataNode(data=[1, 2], summary={"n": 2}, label="L", _N=[5, 3])
    assert dn._N == [5, 3]


def test_data_tree_with_N_list():
    """DataTree stores _N as a list when provided."""
    dn = DataNode(data=[1], summary={"n": 1}, label="L")
    ldn = LvlDataNode(dn=dn, split_lvl="A")
    sdn = SplitDataNode(split_var="Var", A=ldn)
    dt = DataTree(_N=[4], Var=sdn)
    assert dt._N == [4]
