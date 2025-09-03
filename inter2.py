import pandas as pd
import numpy as np
from pyMyriade import *
from pyMyriade.tabular import flatten

dtree = DataTree(
    s = SplitDataNode(
        split_var="VAR",
        node=LvlDataNode(
            split_lvl="lvl1",
            group1=DataNode(
                label="Group 1",
                summary={"mean_val": 10, "count": 5}
            ),
            group2=DataNode(
                label="Group 2",
                summary={"mean_val": 20, "count": 3}
            )
        )
    ),
    a = DataNode(
        label="Overall",
        summary={"mean_val": 15, "count": 8}
    )
)
print(flatten(dtree, unnest=True))

