
from pyMyriade import *
from pyMyriade.tabular import flatten

dtree = DataTree(
    s = SplitDataNode(
        split_var="VAR",
        node=LvlDataNode(
            split_lvl="lvl1",
            group1=DataNode(
                label="Group 1",
                summary={"x": 10, "err": 5}
            ),
            group2=DataNode(
                label="Group 2",
                summary={"x": 100, "err": 50}
            )
        ),
        node2=LvlDataNode(
            split_lvl="lvl2",
            group1=DataNode(
                label="Group 1",
                summary={"x": 8, "err": 9}
            ),
            group2=DataNode(
                label="Group 2",
                summary={"x": 88, "err": 99}
            )
        )
    ),
    a = DataNode(
        label=None,
        summary={"x": 15, "err": 8}
    )
)

from pyMyriade.plots import forest_plot

forest_plot(dtree)

