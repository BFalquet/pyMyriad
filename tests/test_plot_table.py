import numpy as np
import pytest
import pandas as pd
from importlib import import_module
from contextlib import contextmanager

from great_tables import GT
from pyMyriad import AnalysisTree, gt_forest_table


@contextmanager
def with_module(module_name, module_abr):
    module = import_module(module_name)
    yield {module_abr: module}


@pytest.fixture
def simple_dtree():
    atree = (
        AnalysisTree()
        .split_by("df.VAR1")
        .split_by("df.VAR2 > 50")
        .analyze_by(
            x="np.mean(df.val)",
            xmin="np.min(df.val)",
            xmax="np.max(df.val)",
        )
    )
    df = pd.DataFrame(
        {
            "VAR1": ["A", "A", "A", "B", "B", "B"],
            "VAR2": [10, 60, 70, 20, 80, 90],
            "val": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        }
    )
    with with_module("numpy", "np") as environ:
        return atree.run(df, environ=environ)


@pytest.fixture
def mixed_label_dtree():
    """Tree with two analyses: one with CI columns, one without."""
    atree = (
        AnalysisTree()
        .analyze_by(
            x="np.mean(df.val)",
            xmin="np.min(df.val)",
            xmax="np.max(df.val)",
            label="ci",
        )
        .analyze_by(n="len(df)", label="count")
    )
    df = pd.DataFrame({"val": [1.0, 2.0, 3.0, 4.0]})
    with with_module("numpy", "np") as environ:
        return atree.run(df, environ=environ)


def test_import():
    from pyMyriad import gt_forest_table  # noqa: F401


def test_returns_gt_object(simple_dtree):
    result = gt_forest_table(simple_dtree, x="x", xmin="xmin", xmax="xmax")
    assert isinstance(result, GT)


def test_cascade_true(simple_dtree):
    result = gt_forest_table(simple_dtree, x="x", xmin="xmin", xmax="xmax", cascade=True)
    assert isinstance(result, GT)


def test_title_and_subtitle(simple_dtree):
    result = gt_forest_table(
        simple_dtree, x="x", xmin="xmin", xmax="xmax",
        title="Test", subtitle="Sub",
    )
    assert isinstance(result, GT)


def test_ref_line_zero(simple_dtree):
    result = gt_forest_table(simple_dtree, x="x", xmin="xmin", xmax="xmax", ref_line=0.0)
    assert isinstance(result, GT)


def test_autoscale_false(simple_dtree):
    result = gt_forest_table(simple_dtree, x="x", xmin="xmin", xmax="xmax", autoscale=False)
    assert isinstance(result, GT)


def test_suppress_duplicates_false(simple_dtree):
    result = gt_forest_table(simple_dtree, x="x", xmin="xmin", xmax="xmax", suppress_duplicates=False)
    assert isinstance(result, GT)


def test_info_columns_default(simple_dtree):
    """Default sentinel: no extra stat cols in this fixture, _plot is the only extra col."""
    result = gt_forest_table(simple_dtree, x="x", xmin="xmin", xmax="xmax")
    assert isinstance(result, GT)


def test_info_columns_none(simple_dtree):
    """None: only hierarchy + _plot column, no stat columns shown."""
    result = gt_forest_table(simple_dtree, x="x", xmin="xmin", xmax="xmax", info_columns=None)
    assert isinstance(result, GT)


def test_info_columns_empty_list(simple_dtree):
    result = gt_forest_table(simple_dtree, x="x", xmin="xmin", xmax="xmax", info_columns=[])
    assert isinstance(result, GT)


def test_invalid_x_col_raises(simple_dtree):
    with pytest.raises(ValueError, match="not found in table"):
        gt_forest_table(simple_dtree, x="nonexistent", xmin="xmin", xmax="xmax")


def test_invalid_xmin_col_raises(simple_dtree):
    with pytest.raises(ValueError, match="not found in table"):
        gt_forest_table(simple_dtree, x="x", xmin="nonexistent", xmax="xmax")


def test_invalid_xmax_col_raises(simple_dtree):
    with pytest.raises(ValueError, match="not found in table"):
        gt_forest_table(simple_dtree, x="x", xmin="xmin", xmax="nonexistent")


def test_invalid_info_column_raises(simple_dtree):
    with pytest.raises(ValueError, match="not found in table"):
        gt_forest_table(
            simple_dtree, x="x", xmin="xmin", xmax="xmax",
            info_columns=["nonexistent_col"],
        )


def test_cascade_structural_rows_no_error(simple_dtree):
    """cascade=True produces structural rows with NaN CI values; should not error."""
    result = gt_forest_table(
        simple_dtree, x="x", xmin="xmin", xmax="xmax", cascade=True
    )
    assert isinstance(result, GT)


def test_mixed_labels_no_error(mixed_label_dtree):
    """Rows lacking x/xmin/xmax (NaN) produce blank _plot cells, not errors."""
    result = gt_forest_table(mixed_label_dtree, x="x", xmin="xmin", xmax="xmax")
    assert isinstance(result, GT)

