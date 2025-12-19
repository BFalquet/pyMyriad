from __future__ import annotations

from typing import Optional

import pandas as pd

from .data_tree import DataTree
from .tabular import flatten


def _clean_path_element(element: str) -> str:
	"""Clean up path elements for display."""
	if element is None:
		return ""
	element = str(element)
	# Remove 'df.' prefix from expressions
	if element.startswith("df."):
		element = element[3:]
	return element


def _split_path_into_levels(df: pd.DataFrame, path_col: str = "path") -> pd.DataFrame:
	"""Split the path column into separate hierarchical level columns.
	
	Args:
		df: DataFrame with a path column containing lists
		path_col: Name of the column containing path lists
		
	Returns:
		DataFrame with additional Level_0, Level_1, Level_2, etc. columns
	"""
	if path_col not in df.columns:
		return df
	
	df = df.copy()
	
	# Clean paths: remove 'root' and 'analysis' markers
	def clean_path(path_list):
		if not isinstance(path_list, list):
			return []
		cleaned = []
		for elem in path_list:
			if elem not in ['root', 'analysis', None]:
				cleaned.append(_clean_path_element(elem))
		return cleaned
	
	df['_cleaned_path'] = df[path_col].apply(clean_path)
	
	# Find maximum depth
	max_depth = df['_cleaned_path'].apply(len).max()
	if pd.isna(max_depth) or max_depth == 0:
		df = df.drop(columns=['_cleaned_path'])
		return df
	
	# Create level columns
	for i in range(int(max_depth)):
		df[f'Level_{i}'] = df['_cleaned_path'].apply(
			lambda x: x[i] if i < len(x) else None
		)
	
	df = df.drop(columns=['_cleaned_path'])
	
	return df


def _format_analysis_label(row: pd.Series) -> str:
	"""Create a formatted label for analysis rows."""
	if row.get('type') != 'analysis':
		return ""
	
	label = row.get('label', '')
	if not label or label == '':
		return "Analysis"
	return label


def gt_table(
	dtree: DataTree,
	by: str = "",
	*,
	include_non_analysis: bool = False,
	split_path: bool = True,
	title: Optional[str] = "Analysis Summary",
	subtitle: Optional[str] = None,
	decimals: int = 3,
):
	"""Create a Great Tables (gt) display table from a DataTree.

	This builds on the long-form output of ``flatten`` and returns a nicely
	printable table using the Python Great Tables package.

	Args:
		dtree: The DataTree to tabulate.
		by: Split variable name(s) to pivot across columns. Use a string for a
			single split or an iterable of split labels. If empty, no pivoting
			is applied.
		include_non_analysis: If True, keep split/level rows; otherwise only
			rows of type 'analysis' are shown.
		split_path: If True, split the path into separate hierarchical columns.
		title: Optional table title.
		subtitle: Optional table subtitle.
		decimals: Number of decimals for numeric formatting.

	Returns:
		A great_tables.GT object ready for display/printing.

	Raises:
		ImportError: If the great-tables package is not installed.
	"""

	try:
		from great_tables import GT
	except Exception as e:
		raise ImportError(
			"great-tables is required for gt_table(). Install with `pip install great-tables`."
		) from e

	# Get flattened data with unnested statistics
	df = flatten(dtree, unnest=True, by=by)
	
	# Keep only analysis rows by default
	if not include_non_analysis:
		df = df[df["type"] == "analysis"].copy()
	
	if len(df) == 0:
		# Return empty table if no data
		empty_df = pd.DataFrame({"Message": ["No analysis results to display"]})
		return GT(empty_df).tab_header(title=title or "Analysis Summary")
	
	# Split path into hierarchical levels
	if split_path:
		df = _split_path_into_levels(df, path_col="path")
	
	# Format analysis label
	df['Analysis'] = df.apply(_format_analysis_label, axis=1)
	
	# Rename statistics column for display
	if 'statistics' in df.columns:
		df = df.rename(columns={'statistics': 'Statistic'})
	
	# Handle pivot columns if present
	pivot_col = None
	if by and 'pivot_lvl' in df.columns:
		def format_pivot(x):
			if isinstance(x, list):
				return " > ".join([_clean_path_element(str(v)) for v in x if v is not None])
			return None
		
		df['Pivot'] = df['pivot_lvl'].apply(format_pivot)
		if df['Pivot'].notna().any():
			pivot_col = 'Pivot'
	
	# Select columns for display
	level_cols = [c for c in df.columns if c.startswith('Level_')]
	base_cols = level_cols + ['Analysis', 'Statistic']
	
	if pivot_col:
		base_cols.append(pivot_col)
	
	base_cols.append('values')
	
	# Filter to essential columns
	display_df = df[base_cols].copy()
	display_df = display_df.rename(columns={'values': 'Value'})
	
	# Pivot if we have a pivot column
	if pivot_col:
		# Create a unique index for pivoting
		index_cols = [c for c in display_df.columns if c not in [pivot_col, 'Value']]
		display_df = display_df.pivot_table(
			index=index_cols,
			columns=pivot_col,
			values='Value',
			aggfunc='first'
		).reset_index()
	
	# Remove rows where all level columns are None (shouldn't happen but just in case)
	if level_cols:
		display_df = display_df.dropna(subset=level_cols, how='all')
	
	# Build the GT table
	tbl = GT(display_df)
	
	if title or subtitle:
		tbl = tbl.tab_header(title=title, subtitle=subtitle)
	
	# Format numeric columns
	numeric_cols = []
	for col in display_df.columns:
		if col not in level_cols + ['Analysis', 'Statistic', 'Pivot']:
			# Check if column is numeric
			if pd.api.types.is_numeric_dtype(display_df[col]):
				numeric_cols.append(col)
	
	if numeric_cols:
		tbl = tbl.fmt_number(columns=numeric_cols, decimals=decimals)
	
	# Add spanners for hierarchical levels if we have multiple levels
	if len(level_cols) > 1:
		try:
			tbl = tbl.tab_spanner(label="Hierarchy", columns=level_cols)
		except Exception:
			pass
	
	# Style options
	try:
		tbl = tbl.opt_align_table_header(align="left")
		tbl = tbl.tab_options(
			table_font_size="12px",
			heading_background_color="#f8f9fa",
		)
	except Exception:
		pass
	
	return tbl


def simple_table(
	dtree: DataTree,
	by: str = "",
	*,
	include_non_analysis: bool = False,
	split_path: bool = True,
) -> pd.DataFrame:
	"""Create a simple pandas DataFrame table from a DataTree.
	
	This is a lightweight alternative to gt_table that doesn't require
	the great-tables package.
	
	Args:
		dtree: The DataTree to tabulate.
		by: Split variable name(s) to pivot across columns.
		include_non_analysis: If True, keep split/level rows.
		split_path: If True, split the path into separate hierarchical columns.
		
	Returns:
		A formatted pandas DataFrame.
	"""
	# Get flattened data with unnested statistics
	df = flatten(dtree, unnest=True, by=by)
	
	# Keep only analysis rows by default
	if not include_non_analysis:
		df = df[df["type"] == "analysis"].copy()
	
	if len(df) == 0:
		return pd.DataFrame({"Message": ["No analysis results to display"]})
	
	# Split path into hierarchical levels
	if split_path:
		df = _split_path_into_levels(df, path_col="path")
	
	# Format analysis label
	df['Analysis'] = df.apply(_format_analysis_label, axis=1)
	
	# Rename statistics column for display
	if 'statistics' in df.columns:
		df = df.rename(columns={'statistics': 'Statistic'})
	
	# Handle pivot columns if present
	pivot_col = None
	if by and 'pivot_lvl' in df.columns:
		def format_pivot(x):
			if isinstance(x, list):
				return " > ".join([_clean_path_element(str(v)) for v in x if v is not None])
			return None
		
		df['Pivot'] = df['pivot_lvl'].apply(format_pivot)
		if df['Pivot'].notna().any():
			pivot_col = 'Pivot'
	
	# Select columns for display
	level_cols = [c for c in df.columns if c.startswith('Level_')]
	base_cols = level_cols + ['Analysis', 'Statistic']
	
	if pivot_col:
		base_cols.append(pivot_col)
	
	base_cols.append('values')
	
	# Filter to essential columns
	display_df = df[base_cols].copy()
	display_df = display_df.rename(columns={'values': 'Value'})
	
	# Pivot if we have a pivot column
	if pivot_col:
		index_cols = [c for c in display_df.columns if c not in [pivot_col, 'Value']]
		display_df = display_df.pivot_table(
			index=index_cols,
			columns=pivot_col,
			values='Value',
			aggfunc='first'
		).reset_index()
	
	# Remove rows where all level columns are None
	if level_cols:
		display_df = display_df.dropna(subset=level_cols, how='all')
	
	return display_df
