import numpy as np
import pandas as pd
import pytest

from pyMyriad.clinical import lab_summary_table, summary_table


@pytest.fixture
def lab_df():
    """4 subjects x 2 visits x 2 arms, hand-computable statistics."""
    visits = pd.Categorical(
        ["Baseline", "Week 4"] * 4, categories=["Baseline", "Week 4"], ordered=True
    )
    arms = pd.Categorical(
        [
            "Placebo",
            "Placebo",
            "Placebo",
            "Placebo",
            "Active",
            "Active",
            "Active",
            "Active",
        ],
        categories=["Placebo", "Active"],
        ordered=True,
    )
    return pd.DataFrame(
        {
            "USUBJID": ["S1", "S1", "S2", "S2", "S3", "S3", "S4", "S4"],
            "AVISIT": visits,
            "ARM": arms,
            "AVAL": [10.0, 12.0, 20.0, 18.0, 30.0, 24.0, 40.0, 34.0],
        }
    )


def _call(df, **kwargs):
    kwargs.setdefault("baseline_level", "Baseline")
    return lab_summary_table(
        df,
        value_col="AVAL",
        visit_col="AVISIT",
        arm_col="ARM",
        subject_col="USUBJID",
        **kwargs,
    )


def test_returns_dataframe_by_default(lab_df):
    """Regression test for #65: default call returns a DataFrame, not a GT."""
    table = _call(lab_df)
    assert isinstance(table, pd.DataFrame)


def test_row_shape_visit_x_statistic(lab_df):
    """2 visits x 4 default stats = 8 rows, in the documented stat order per visit."""
    table = _call(lab_df)
    assert len(table) == 8
    assert list(table.loc[table.Visit == "Baseline", "Statistic"]) == [
        "n",
        "Mean (SD)",
        "Median (Q1, Q3)",
        "Min, Max",
    ]


def test_column_shape_arm_x_value_change(lab_df):
    """Columns are Visit, Statistic, then Value/Change per arm in category order."""
    table = _call(lab_df)
    assert list(table.columns) == [
        "Visit",
        "Statistic",
        "Placebo||Value",
        "Placebo||Change",
        "Active||Value",
        "Active||Change",
    ]


def test_n_stat_value(lab_df):
    """Regression test for #65: n counts subjects per (visit, arm) group."""
    table = _call(lab_df)
    row = table[(table.Visit == "Week 4") & (table.Statistic == "n")].iloc[0]
    assert row["Placebo||Value"] == "2"
    assert row["Active||Value"] == "2"


def test_mean_sd_stat_value(lab_df):
    """Placebo Baseline values are [10, 20] -> mean 15.0, sd(ddof=1) ~= 7.1."""
    table = _call(lab_df)
    row = table[(table.Visit == "Baseline") & (table.Statistic == "Mean (SD)")].iloc[0]
    expected = f"{np.mean([10, 20]):.1f} ({np.std([10, 20], ddof=1):.1f})"
    assert row["Placebo||Value"] == expected


def test_median_iqr_stat_value(lab_df):
    """Active Baseline values are [30, 40] -> hand-verified against np.percentile."""
    table = _call(lab_df)
    row = table[
        (table.Visit == "Baseline") & (table.Statistic == "Median (Q1, Q3)")
    ].iloc[0]
    q1, med, q3 = np.percentile([30, 40], [25, 50, 75])
    assert row["Active||Value"] == f"{med:.1f} ({q1:.1f}, {q3:.1f})"


def test_min_max_stat_value(lab_df):
    """Placebo Baseline values are [10, 20] -> Min, Max is '10.0, 20.0'."""
    table = _call(lab_df)
    row = table[(table.Visit == "Baseline") & (table.Statistic == "Min, Max")].iloc[0]
    assert row["Placebo||Value"] == "10.0, 20.0"


def test_change_from_baseline_values(lab_df):
    """Regression test for #65: Change uses paired per-subject change, not group means.

    Placebo Week 4: S1 12-10=2, S2 18-20=-2 -> mean change 0.0.
    """
    table = _call(lab_df)
    row = table[(table.Visit == "Week 4") & (table.Statistic == "Mean (SD)")].iloc[0]
    expected = f"{np.mean([2, -2]):.1f} ({np.std([2, -2], ddof=1):.1f})"
    assert row["Placebo||Change"] == expected


def test_baseline_row_change_is_zero(lab_df):
    """Baseline rows have CHG == 0 for every subject (per change_from_baseline)."""
    table = _call(lab_df)
    row = table[(table.Visit == "Baseline") & (table.Statistic == "Mean (SD)")].iloc[0]
    assert row["Placebo||Change"] == "0.0 (0.0)"
    assert row["Active||Change"] == "0.0 (0.0)"


def test_stats_subset_selection(lab_df):
    """Only the requested statistics appear as rows."""
    table = _call(lab_df, stats=("n", "mean_sd"))
    assert len(table) == 4
    assert set(table["Statistic"]) == {"n", "Mean (SD)"}


def test_stats_order_respected(lab_df):
    """Row order within each visit follows the `stats` tuple order."""
    table = _call(lab_df, stats=("min_max", "n"))
    assert list(table.loc[table.Visit == "Baseline", "Statistic"]) == [
        "Min, Max",
        "n",
    ]


def test_empty_stats_raises(lab_df):
    """Regression test for #65: empty `stats` is rejected up front."""
    with pytest.raises(ValueError):
        _call(lab_df, stats=())


def test_unknown_stat_raises(lab_df):
    """Regression test for #65: an invalid stat name raises with a clear message."""
    with pytest.raises(ValueError, match="mean"):
        _call(lab_df, stats=("mean",))


def test_visit_ordering_preserved_via_categorical():
    """Regression test for #65 (relies on #61): visit order follows categories, not alphabetical."""
    df = pd.DataFrame(
        {
            "USUBJID": ["S1", "S1", "S2", "S2"],
            "AVISIT": pd.Categorical(
                ["Week 4", "Baseline", "Week 4", "Baseline"],
                categories=["Week 4", "Baseline"],
                ordered=True,
            ),
            "ARM": ["A", "A", "A", "A"],
            "AVAL": [12.0, 10.0, 18.0, 20.0],
        }
    )
    table = lab_summary_table(
        df,
        value_col="AVAL",
        visit_col="AVISIT",
        arm_col="ARM",
        subject_col="USUBJID",
        baseline_level="Baseline",
    )
    assert list(pd.unique(table["Visit"])) == ["Week 4", "Baseline"]


def test_arm_ordering_preserved_via_categorical():
    """Regression test for #65 (relies on #61): arm column order follows categories."""
    df = pd.DataFrame(
        {
            "USUBJID": ["S1", "S1", "S2", "S2"],
            "AVISIT": ["Baseline", "Week 4", "Baseline", "Week 4"],
            "ARM": pd.Categorical(
                ["Active", "Active", "Placebo", "Placebo"],
                categories=["Active", "Placebo"],
                ordered=True,
            ),
            "AVAL": [10.0, 12.0, 20.0, 18.0],
        }
    )
    table = lab_summary_table(
        df,
        value_col="AVAL",
        visit_col="AVISIT",
        arm_col="ARM",
        subject_col="USUBJID",
        baseline_level="Baseline",
    )
    assert list(table.columns) == [
        "Visit",
        "Statistic",
        "Active||Value",
        "Active||Change",
        "Placebo||Value",
        "Placebo||Change",
    ]


def test_missing_baseline_level_raises(lab_df):
    """Regression test for #65: a nonexistent baseline_level fails fast."""
    with pytest.raises(ValueError):
        _call(lab_df, baseline_level="Nonexistent")


def test_existing_change_col_is_used(lab_df):
    """Regression test for #65: a pre-existing change_col is used as-is, not recomputed."""
    # A constant 5.0 — deliberately not the paired change change_from_baseline
    # would compute — proves the supplied column is used verbatim. subject_col /
    # baseline_level are not required when change_col already exists.
    lab_df["CHG"] = 5.0
    table = lab_summary_table(
        lab_df,
        value_col="AVAL",
        visit_col="AVISIT",
        arm_col="ARM",
    )
    row = table[(table.Visit == "Baseline") & (table.Statistic == "Mean (SD)")].iloc[0]
    assert row["Placebo||Change"] == "5.0 (0.0)"


def test_missing_change_col_requires_subject_and_baseline(lab_df):
    """Regression test for #65: computing change_col needs subject_col and baseline_level."""
    with pytest.raises(ValueError):
        lab_summary_table(
            lab_df,
            value_col="AVAL",
            visit_col="AVISIT",
            arm_col="ARM",
        )


def test_custom_change_col_name(lab_df):
    """A custom change_col that must be computed is threaded through correctly."""
    table = _call(lab_df, change_col="MY_CHG")
    row = table[(table.Visit == "Baseline") & (table.Statistic == "Mean (SD)")].iloc[0]
    assert row["Placebo||Change"] == "0.0 (0.0)"


def test_nan_values_produce_na_string():
    """An entirely-missing (visit, arm) group renders 'NA' cells instead of crashing."""
    df = pd.DataFrame(
        {
            "USUBJID": ["S1", "S1"],
            "AVISIT": ["Baseline", "Week 4"],
            "ARM": ["A", "A"],
            "AVAL": [10.0, np.nan],
        }
    )
    table = lab_summary_table(
        df,
        value_col="AVAL",
        visit_col="AVISIT",
        arm_col="ARM",
        subject_col="USUBJID",
        baseline_level="Baseline",
    )
    row = table[(table.Visit == "Week 4") & (table.Statistic == "Mean (SD)")].iloc[0]
    assert row["A||Value"] == "NA"


def test_single_subject_group_no_crash():
    """A single-subject group renders '(NA)' for sd instead of NaN/crashing."""
    df = pd.DataFrame(
        {
            "USUBJID": ["S1", "S1"],
            "AVISIT": ["Baseline", "Week 4"],
            "ARM": ["A", "A"],
            "AVAL": [10.0, 12.0],
        }
    )
    table = lab_summary_table(
        df,
        value_col="AVAL",
        visit_col="AVISIT",
        arm_col="ARM",
        subject_col="USUBJID",
        baseline_level="Baseline",
    )
    row = table[(table.Visit == "Baseline") & (table.Statistic == "Mean (SD)")].iloc[0]
    assert row["A||Value"] == "10.0 (NA)"


def test_single_arm_supported():
    """A DataFrame with only one arm level still builds a valid table."""
    df = pd.DataFrame(
        {
            "USUBJID": ["S1", "S1", "S2", "S2"],
            "AVISIT": ["Baseline", "Week 4", "Baseline", "Week 4"],
            "ARM": ["Placebo", "Placebo", "Placebo", "Placebo"],
            "AVAL": [10.0, 12.0, 20.0, 18.0],
        }
    )
    table = lab_summary_table(
        df,
        value_col="AVAL",
        visit_col="AVISIT",
        arm_col="ARM",
        subject_col="USUBJID",
        baseline_level="Baseline",
    )
    assert list(table.columns) == [
        "Visit",
        "Statistic",
        "Placebo||Value",
        "Placebo||Change",
    ]


def test_as_gt_returns_gt(lab_df):
    """Regression test for #65: as_gt=True returns a great_tables.GT instance."""
    from great_tables import GT

    result = _call(lab_df, as_gt=True)
    assert isinstance(result, GT)


def test_as_gt_title_subtitle(lab_df):
    """as_gt=True with a title builds without error."""
    from great_tables import GT

    result = _call(lab_df, as_gt=True, title="My Title")
    assert isinstance(result, GT)


def test_result_col_not_leaked_into_output(lab_df):
    """The internal change_col is never a literal column name in the returned table."""
    table = _call(lab_df)
    assert "CHG" not in table.columns


# --- summary_table() ---------------------------------------------------


@pytest.fixture
def demo_df():
    """12 subjects x 2 arms x 2 sexes, hand-computable demographics."""
    return pd.DataFrame(
        {
            "USUBJID": [f"S{i}" for i in range(1, 13)],
            "ARM": pd.Categorical(
                ["Placebo"] * 6 + ["Active"] * 6,
                categories=["Placebo", "Active"],
                ordered=True,
            ),
            "SEX": ["Male", "Male", "Male", "Female", "Female", "Female"] * 2,
            "AGE": [40, 45, 50, 42, 47, 52, 41, 46, 51, 43, 48, 53],
            "ETHNIC": [
                "White",
                "White",
                "Black",
                "White",
                "Black",
                "Other",
                "White",
                "White",
                "Other",
                "White",
                "Black",
                "Black",
            ],
        }
    )


def test_summary_continuous_only_returns_dataframe(demo_df):
    """Regression test for #76: continuous-only call returns a DataFrame."""
    table = summary_table(
        demo_df, variables={"AGE": "continuous"}, arm_col="ARM", subject_col="USUBJID"
    )
    assert isinstance(table, pd.DataFrame)
    assert list(table.columns) == [
        "Variable",
        "Level",
        "Statistic",
        "Placebo",
        "Active",
    ]
    assert len(table) == 4
    assert (table["Variable"] == "AGE").all()
    assert (table["Level"] == "").all()


def test_summary_categorical_only_row_per_level(demo_df):
    """Regression test for #76: categorical variables get one row per observed level."""
    table = summary_table(
        demo_df,
        variables={"ETHNIC": "categorical"},
        arm_col="ARM",
        subject_col="USUBJID",
    )
    assert len(table) == 3
    assert set(table["Level"]) == {"White", "Black", "Other"}
    assert (table["Statistic"] == "n (pct)").all()


def test_summary_percentage_denominator_is_arm_total(demo_df):
    """Regression test for #76: % denominator is the arm total, not the level's own count.

    Placebo arm (S1-S6): ETHNIC = White, White, Black, White, Black, Other
    -> White 3/6=50%, Black 2/6=33%, Other 1/6=17%.
    """
    table = summary_table(
        demo_df,
        variables={"ETHNIC": "categorical"},
        arm_col="ARM",
        subject_col="USUBJID",
    )
    row = table[table["Level"] == "White"].iloc[0]
    assert row["Placebo"] == "3 (50%)"
    row = table[table["Level"] == "Black"].iloc[0]
    assert row["Placebo"] == "2 (33%)"


def test_summary_percentage_uses_unique_subject_count(demo_df):
    """Regression test for #76: denominator counts unique subject_col, not raw rows.

    Duplicating S1's row (already White/Placebo) must not change the
    denominator or numerator, since S1 is still the same one subject.
    """
    dup_df = pd.concat([demo_df, demo_df.iloc[[0]]], ignore_index=True)
    table = summary_table(
        dup_df,
        variables={"ETHNIC": "categorical"},
        arm_col="ARM",
        subject_col="USUBJID",
    )
    row = table[table["Level"] == "White"].iloc[0]
    assert row["Placebo"] == "3 (50%)"


def test_summary_mixed_continuous_and_categorical(demo_df):
    """Regression test for #76: mixed variables dict produces blocks in dict order."""
    table = summary_table(
        demo_df,
        variables={"AGE": "continuous", "ETHNIC": "categorical"},
        arm_col="ARM",
        subject_col="USUBJID",
    )
    assert len(table) == 7  # 4 AGE stat rows + 3 ETHNIC level rows
    assert list(table["Variable"]) == ["AGE"] * 4 + ["ETHNIC"] * 3


def test_summary_variable_order_follows_dict_order(demo_df):
    """Reversing the `variables` dict order reverses the block order."""
    table = summary_table(
        demo_df,
        variables={"ETHNIC": "categorical", "AGE": "continuous"},
        arm_col="ARM",
        subject_col="USUBJID",
    )
    assert list(pd.unique(table["Variable"])) == ["ETHNIC", "AGE"]


def test_summary_by_none_has_no_by_column(demo_df):
    """Regression test for #76: by=None (default) produces no "By" column."""
    table = summary_table(
        demo_df, variables={"AGE": "continuous"}, arm_col="ARM", subject_col="USUBJID"
    )
    assert "By" not in table.columns


def test_summary_by_given_adds_by_column(demo_df):
    """Regression test for #76: by=<col> adds a "By" column stratifying the blocks."""
    table = summary_table(
        demo_df,
        variables={"AGE": "continuous"},
        arm_col="ARM",
        subject_col="USUBJID",
        by="SEX",
    )
    assert list(table.columns) == [
        "By",
        "Variable",
        "Level",
        "Statistic",
        "Placebo",
        "Active",
    ]
    assert list(pd.unique(table["By"])) == ["Male", "Female"]


def test_summary_by_percentage_denominator_is_by_arm_total(demo_df):
    """Regression test for #76: with by=, % denominator is the (by, arm) subgroup total.

    Male Placebo (S1-S3): ETHNIC = White, White, Black -> White 2/3=67%, Black 1/3=33%.
    """
    table = summary_table(
        demo_df,
        variables={"ETHNIC": "categorical"},
        arm_col="ARM",
        subject_col="USUBJID",
        by="SEX",
    )
    row = table[(table["By"] == "Male") & (table["Level"] == "White")].iloc[0]
    assert row["Placebo"] == "2 (67%)"
    row = table[(table["By"] == "Male") & (table["Level"] == "Black")].iloc[0]
    assert row["Placebo"] == "1 (33%)"


def test_summary_missing_level_in_arm_is_nan(demo_df):
    """A category level absent from one arm renders NaN, not '0 (0%)'."""
    table = summary_table(
        demo_df,
        variables={"ETHNIC": "categorical"},
        arm_col="ARM",
        subject_col="USUBJID",
        by="SEX",
    )
    row = table[(table["By"] == "Male") & (table["Level"] == "Other")].iloc[0]
    assert pd.isna(row["Placebo"])
    assert row["Active"] == "1 (33%)"


def test_summary_by_ordering_follows_categorical():
    """Regression test for #76 (relies on #61): By order follows categories, not alphabetical."""
    df = pd.DataFrame(
        {
            "USUBJID": ["S1", "S2", "S3", "S4"],
            "ARM": ["A", "A", "A", "A"],
            "SEX": pd.Categorical(
                ["Female", "Male", "Female", "Male"],
                categories=["Female", "Male"],
                ordered=True,
            ),
            "AGE": [10.0, 20.0, 30.0, 40.0],
        }
    )
    table = summary_table(
        df,
        variables={"AGE": "continuous"},
        arm_col="ARM",
        subject_col="USUBJID",
        by="SEX",
    )
    assert list(pd.unique(table["By"])) == ["Female", "Male"]


def test_summary_arm_ordering_follows_categorical():
    """Regression test for #76 (relies on #61): Arm column order follows categories."""
    df = pd.DataFrame(
        {
            "USUBJID": ["S1", "S2", "S3", "S4"],
            "ARM": pd.Categorical(
                ["Active", "Active", "Placebo", "Placebo"],
                categories=["Active", "Placebo"],
                ordered=True,
            ),
            "AGE": [10.0, 20.0, 30.0, 40.0],
        }
    )
    table = summary_table(
        df, variables={"AGE": "continuous"}, arm_col="ARM", subject_col="USUBJID"
    )
    assert list(table.columns) == [
        "Variable",
        "Level",
        "Statistic",
        "Active",
        "Placebo",
    ]


def test_summary_categorical_level_ordering_follows_categorical():
    """Regression test for #76 (relies on #61): categorical level order follows categories."""
    df = pd.DataFrame(
        {
            "USUBJID": ["S1", "S2", "S3", "S4"],
            "ARM": ["A", "A", "A", "A"],
            "ETHNIC": pd.Categorical(
                ["White", "Black", "White", "Other"],
                categories=["Other", "White", "Black"],
                ordered=True,
            ),
        }
    )
    table = summary_table(
        df, variables={"ETHNIC": "categorical"}, arm_col="ARM", subject_col="USUBJID"
    )
    assert list(table["Level"]) == ["Other", "White", "Black"]


def test_summary_stats_subset_and_order(demo_df):
    """`stats=` selects and orders the continuous-variable statistic rows."""
    table = summary_table(
        demo_df,
        variables={"AGE": "continuous"},
        arm_col="ARM",
        subject_col="USUBJID",
        stats=("min_max", "n"),
    )
    assert list(table["Statistic"]) == ["Min, Max", "n"]


def test_summary_single_observed_level():
    """A categorical variable with only one observed level renders '(100%)'."""
    df = pd.DataFrame(
        {
            "USUBJID": ["S1", "S2", "S3"],
            "ARM": ["A", "A", "A"],
            "SEX": ["Male", "Male", "Male"],
        }
    )
    table = summary_table(
        df, variables={"SEX": "categorical"}, arm_col="ARM", subject_col="USUBJID"
    )
    assert len(table) == 1
    assert table.iloc[0]["A"] == "3 (100%)"


def test_summary_continuous_all_nan_in_one_group():
    """A continuous variable entirely NaN in one arm renders 'NA' cells, no crash."""
    df = pd.DataFrame(
        {
            "USUBJID": ["S1", "S2", "S3"],
            "ARM": ["A", "A", "B"],
            "AGE": [10.0, 20.0, np.nan],
        }
    )
    table = summary_table(
        df, variables={"AGE": "continuous"}, arm_col="ARM", subject_col="USUBJID"
    )
    row = table[table["Statistic"] == "Mean (SD)"].iloc[0]
    assert row["B"] == "NA"


def test_summary_as_gt_returns_gt(demo_df):
    """Regression test for #76: as_gt=True returns a great_tables.GT instance."""
    from great_tables import GT

    result = summary_table(
        demo_df,
        variables={"AGE": "continuous", "ETHNIC": "categorical"},
        arm_col="ARM",
        subject_col="USUBJID",
        as_gt=True,
    )
    assert isinstance(result, GT)


def test_summary_as_gt_with_by_builds(demo_df):
    """as_gt=True with by= builds without error (row-group smoke test)."""
    from great_tables import GT

    result = summary_table(
        demo_df,
        variables={"AGE": "continuous", "ETHNIC": "categorical"},
        arm_col="ARM",
        subject_col="USUBJID",
        by="SEX",
        as_gt=True,
        title="Baseline Characteristics",
    )
    assert isinstance(result, GT)


def test_summary_empty_variables_raises(demo_df):
    """Regression test for #76: empty `variables` is rejected up front."""
    with pytest.raises(ValueError):
        summary_table(demo_df, variables={}, arm_col="ARM", subject_col="USUBJID")


def test_summary_unknown_variable_type_raises(demo_df):
    """Regression test for #76: an invalid variable type raises with a clear message."""
    with pytest.raises(ValueError, match="numeric"):
        summary_table(
            demo_df,
            variables={"AGE": "numeric"},
            arm_col="ARM",
            subject_col="USUBJID",
        )


def test_summary_variable_collides_with_arm_col_raises(demo_df):
    """A variable name that collides with arm_col is rejected."""
    with pytest.raises(ValueError):
        summary_table(
            demo_df,
            variables={"ARM": "categorical"},
            arm_col="ARM",
            subject_col="USUBJID",
        )


def test_summary_by_not_in_df_raises(demo_df):
    """Regression test for #76: a nonexistent `by` column fails fast."""
    with pytest.raises(ValueError):
        summary_table(
            demo_df,
            variables={"AGE": "continuous"},
            arm_col="ARM",
            subject_col="USUBJID",
            by="NOPE",
        )


def test_summary_variable_not_in_df_raises(demo_df):
    """A variable name not present in `df` fails fast."""
    with pytest.raises(ValueError):
        summary_table(
            demo_df,
            variables={"NOPE": "continuous"},
            arm_col="ARM",
            subject_col="USUBJID",
        )


def test_summary_subject_col_not_in_df_raises(demo_df):
    """Regression test for #76: a nonexistent `subject_col` fails fast."""
    with pytest.raises(ValueError):
        summary_table(
            demo_df,
            variables={"AGE": "continuous"},
            arm_col="ARM",
            subject_col="NOPE",
        )


def test_summary_unknown_stat_raises(demo_df):
    """Regression test for #76: an invalid stat name raises with a clear message."""
    with pytest.raises(ValueError, match="average"):
        summary_table(
            demo_df,
            variables={"AGE": "continuous"},
            arm_col="ARM",
            subject_col="USUBJID",
            stats=("average",),
        )


def test_summary_raw_continuous_stat(demo_df):
    """Regression test for #76: raw (non-combo) continuous stats are supported directly.

    "mean" is a predefined raw statistic (via multi_simple_analysis's
    CONTINUOUS_SIMPLE_FUNCTIONS), not a formatted "Mean (SD)" combo string.
    """
    table = summary_table(
        demo_df,
        variables={"AGE": "continuous"},
        arm_col="ARM",
        subject_col="USUBJID",
        stats=("mean",),
    )
    assert len(table) == 1
    assert table.iloc[0]["Statistic"] == "mean"


def test_summary_empty_stats_raises(demo_df):
    """Regression test for #76: empty `stats` is rejected up front."""
    with pytest.raises(ValueError):
        summary_table(
            demo_df,
            variables={"AGE": "continuous"},
            arm_col="ARM",
            subject_col="USUBJID",
            stats=(),
        )
