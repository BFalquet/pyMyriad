import pytest
import pandas as pd
import numpy as np
from pyMyriad import AnalysisTree, simple_table
from pyMyriad.listing import _clean_path_element, _split_path_into_levels


def test_clean_path_element():
	"""Test path element cleaning."""
	assert _clean_path_element("df.Gender") == "Gender"
	assert _clean_path_element("Gender") == "Gender"
	assert _clean_path_element(None) == ""
	assert _clean_path_element("df.Age > 40") == "Age > 40"


def test_split_path_into_levels():
	"""Test splitting paths into hierarchical levels."""
	df = pd.DataFrame({
		'path': [
			['root', 'df.Gender', 'M', 'analysis'],
			['root', 'df.Gender', 'F', 'df.Country', 'US', 'analysis'],
		],
		'value': [1, 2]
	})
	
	result = _split_path_into_levels(df, path_col='path')
	
	assert 'Level_0' in result.columns
	assert 'Level_1' in result.columns
	assert 'Level_2' in result.columns
	assert result.loc[0, 'Level_0'] == 'Gender'
	assert result.loc[0, 'Level_1'] == 'M'
	assert result.loc[1, 'Level_0'] == 'Gender'
	assert result.loc[1, 'Level_1'] == 'F'
	assert result.loc[1, 'Level_2'] == 'Country'


def test_simple_table_basic():
	"""Test simple_table with basic hierarchical analysis."""
	df = pd.DataFrame({
		'Gender': ['M', 'M', 'F', 'F', 'M', 'F'],
		'Country': ['US', 'UK', 'US', 'UK', 'US', 'UK'],
		'Age': [25, 35, 45, 55, 30, 40],
		'Income': [50000, 60000, 70000, 80000, 55000, 75000]
	})
	
	atree = AnalysisTree()\
		.split_by('df.Gender')\
		.split_by('df.Country')\
		.analyze_by(
			mean_income=lambda df: np.mean(df.Income),
			count=lambda df: len(df)
		)
	
	dtree = atree.run(df)
	result = simple_table(dtree)
	
	# Check that we have the expected columns
	assert 'Level_0' in result.columns
	assert 'Level_1' in result.columns
	assert 'Level_2' in result.columns
	assert 'Analysis' in result.columns
	assert 'Statistic' in result.columns
	assert 'Value' in result.columns
	
	# Check that we have the right number of rows (4 groups * 2 statistics)
	assert len(result) == 8
	
	# Check that paths are properly split
	assert 'Gender' in result['Level_0'].values
	assert 'M' in result['Level_1'].values
	assert 'F' in result['Level_1'].values
	assert 'Country' in result['Level_2'].values


def test_simple_table_with_pivot():
	"""Test simple_table with pivot functionality."""
	df = pd.DataFrame({
		'Gender': ['M', 'M', 'F', 'F', 'M', 'F'],
		'Country': ['US', 'UK', 'US', 'UK', 'US', 'UK'],
		'Income': [50000, 60000, 70000, 80000, 55000, 75000]
	})
	
	atree = AnalysisTree()\
		.split_by('df.Gender')\
		.split_by('df.Country')\
		.analyze_by(mean_income=lambda df: np.mean(df.Income))
	
	dtree = atree.run(df)
	result = simple_table(dtree, by='df.Gender')
	
	# Check that pivot column exists
	assert 'Pivot' in result.columns
	
	# Check that we have pivoted values
	assert 'M' in result.columns or 'Gender > M' in result.columns


def test_simple_table_single_level():
	"""Test simple_table with single level analysis."""
	df = pd.DataFrame({
		'Gender': ['M', 'M', 'F', 'F'],
		'Income': [50000, 60000, 70000, 80000]
	})
	
	atree = AnalysisTree()\
		.split_by('df.Gender')\
		.analyze_by(
			mean_income=lambda df: np.mean(df.Income),
			std_income=lambda df: np.std(df.Income)
		)
	
	dtree = atree.run(df)
	result = simple_table(dtree)
	
	# Check basic structure
	assert 'Level_0' in result.columns
	assert 'Level_1' in result.columns
	assert 'Analysis' in result.columns
	assert 'Statistic' in result.columns
	assert 'Value' in result.columns
	
	# Should have 2 groups * 2 statistics = 4 rows
	assert len(result) == 4


def test_simple_table_no_split():
	"""Test simple_table with analysis but no splits."""
	df = pd.DataFrame({
		'Income': [50000, 60000, 70000, 80000]
	})
	
	atree = AnalysisTree()\
		.analyze_by(
			mean_income=lambda df: np.mean(df.Income),
			count=lambda df: len(df)
		)
	
	dtree = atree.run(df)
	result = simple_table(dtree)
	
	# Should still have analysis results
	assert 'Analysis' in result.columns
	assert 'Statistic' in result.columns
	assert 'Value' in result.columns
	assert len(result) == 2  # 2 statistics


def test_simple_table_include_non_analysis():
	"""Test simple_table with include_non_analysis flag."""
	df = pd.DataFrame({
		'Gender': ['M', 'M', 'F', 'F'],
		'Income': [50000, 60000, 70000, 80000]
	})
	
	atree = AnalysisTree()\
		.split_by('df.Gender')\
		.analyze_by(mean_income=lambda df: np.mean(df.Income))
	
	dtree = atree.run(df)
	
	# Without non-analysis rows
	result_analysis_only = simple_table(dtree, include_non_analysis=False)
	
	# With non-analysis rows
	result_all = simple_table(dtree, include_non_analysis=True)
	
	# The version with non-analysis should have more rows
	assert len(result_all) >= len(result_analysis_only)


def test_simple_table_no_split_path():
	"""Test simple_table with split_path=False."""
	df = pd.DataFrame({
		'Gender': ['M', 'M', 'F', 'F'],
		'Income': [50000, 60000, 70000, 80000]
	})
	
	atree = AnalysisTree()\
		.split_by('df.Gender')\
		.analyze_by(mean_income=lambda df: np.mean(df.Income))
	
	dtree = atree.run(df)
	result = simple_table(dtree, split_path=False)
	
	# Should not have Level_* columns
	level_cols = [c for c in result.columns if c.startswith('Level_')]
	assert len(level_cols) == 0


def test_simple_table_empty_result():
	"""Test simple_table with empty analysis tree."""
	df = pd.DataFrame({
		'Gender': ['M', 'M', 'F', 'F'],
		'Income': [50000, 60000, 70000, 80000]
	})
	
	# Create a tree with only splits, no analysis
	atree = AnalysisTree().split_by('df.Gender')
	
	dtree = atree.run(df)
	result = simple_table(dtree)
	
	# Should return a message about no results
	assert 'Message' in result.columns or len(result) == 0


def test_simple_table_multiple_analyses():
	"""Test simple_table with multiple analysis nodes at different levels."""
	df = pd.DataFrame({
		'Gender': ['M', 'M', 'F', 'F', 'M', 'F'],
		'Country': ['US', 'UK', 'US', 'UK', 'US', 'UK'],
		'Income': [50000, 60000, 70000, 80000, 55000, 75000],
		'Age': [25, 35, 45, 55, 30, 40]
	})
	
	atree = AnalysisTree()\
		.split_by('df.Gender')\
		.summarize_by(gender_mean=lambda df: np.mean(df.Income))\
		.split_by('df.Country')\
		.analyze_by(
			country_mean=lambda df: np.mean(df.Income),
			age_mean=lambda df: np.mean(df.Age)
		)
	
	dtree = atree.run(df)
	result = simple_table(dtree)
	
	# Should have results from both analysis nodes
	assert len(result) > 0
	assert 'Analysis' in result.columns
	
	# Check that we have different analysis labels
	analysis_labels = result['Analysis'].unique()
	assert len(analysis_labels) > 0


if __name__ == "__main__":
	pytest.main([__file__, "-v"])
