import pytest
import pandas as pd
import numpy as np

from pyMyriad import AnalysisTree, AnalysisNode, SplitNode
from pyMyriad.listing import gt_table


def test_gt_table_basic():
    gt = pytest.importorskip("great_tables")

    # Simple tree with one split and one analysis
    df = pd.DataFrame({
        "A": [1, 2, 3, 4],
        "B": [10, 20, 30, 40],
        "grp": ["X", "X", "Y", "Y"],
    })

    atree = (
        AnalysisTree()
        .split_by("df.grp")
        .analyze_by(m="np.mean(df.A)", s="np.std(df.B)")
    )

    # Provide numpy for string evals
    environ = {"np": np}
    dtree = atree.run(df, environ=environ)

    tbl = gt_table(dtree, by="df.grp", title="Test Table", unnest=True)

    # Validate we got a GT object back
    GT = getattr(gt, "GT")
    assert isinstance(tbl, GT)
