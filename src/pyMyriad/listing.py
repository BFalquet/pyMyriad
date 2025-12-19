from __future__ import annotations

from typing import Iterable, Optional, Union

import pandas as pd

from .data_tree import DataTree
from .tabular import flatten


def _format_path(path_list: list) -> str:
	"""Turn a path list from flatten() into a readable breadcrumb string.

	Removes the artificial "root" and trailing "analysis" elements when present.
	"""
	if not isinstance(path_list, list):
		return ""

	core = [x for x in path_list if x is not None]
	if core and core[0] == "root":
		core = core[1:]
	if core and core[-1] == "analysis":
		core = core[:-1]
	return " > ".join(core) if core else "root"


def gt_table(
	dtree: DataTree,
	by: str = "",
	*,
	unnest = True,
	include_non_analysis: bool = False,
	title: Optional[str] = "Analysis Summary",
	subtitle: Optional[str] = None,
	decimals: int = 3,
):
	"""Create a Great Tables (gt) display table from a DataTree.

	This builds on the long-form output of `flatten` and returns a nicely
	printable table using the Python Great Tables package.

	Args:
		dtree: The DataTree to tabulate.
		by: Split variable name(s) to pivot across columns. Use a string for a
			single split or an iterable of split labels. If empty, no pivoting
			is applied.
		unnest: If True, the statisttics are represented in separate rows; if False,
			only the summary value is shown.
		include_non_analysis: If True, keep split/level rows; otherwise only
			rows of type 'analysis' are shown.
		title: Optional table title.
		subtitle: Optional table subtitle.
		decimals: Number of decimals for numeric formatting.

	Returns:
		A great_tables.GT object ready for display/printing.

	Raises:
		ImportError: If the great-tables package is not installed.
	"""

	try:
		# Import lazily so the package is only required when this function is used
		from great_tables import GT
	except Exception as e:
		raise ImportError(
			"great-tables is required for gt_table(). Install with `pip install great-tables`."
		) from e


	res = flatten(dtree, unnest=False, by=by)

	# Get the analysis result with the paths to merge later
	# Question: what if there are multiple analysis with same path but different labels?
	inline_analysis = res.loc[res["type"] == "analysis", ["path", "summary", "label"]].copy()

	# For now take the first label only
	inline_analysis = inline_analysis.drop_duplicates(subset=['path'])

	# apply some sort of formatting on the summary to return a string
	# TODO: create a `format` argument to allow user-defined formatting
	inline_analysis['summary'] = inline_analysis['summary'].apply(lambda x: str(x) if x is not None else "")

	# Get the unnested data frame ----
	res_unnested = flatten(dtree, unnest=True, by=by)

	# Remove the last element from path_pivot for y_label
	res_unnested['y_label'] = res_unnested.apply(lambda row: str(row['path_pivot'][-2]) if row['type'] == "analysis" else row['lvl'] or row['split'] or "root", axis=1)

	# remove the last element from path for merging
	inline_analysis['path'] = inline_analysis['path'].apply(lambda x: x[:-1] if isinstance(x, list) and len(x) > 0 else x)
	inline_analysis['path_str'] = inline_analysis['path'].apply(lambda x: str(x) if isinstance(x, list) else x)
	res_unnested['path_str'] = res_unnested['path'].apply(lambda x: str(x) if isinstance(x, list) else x)
	
	# Merge the analysis summary back to the main table
	res_unnested = res_unnested.merge(inline_analysis[['path_str', 'summary', 'label']], on=["path_str"], suffixes=("", "_inline"), how="left")

	# Assign to df for downstream processing
	df = res_unnested.copy()
	# unnest = True  # We already unnested the data
	
	# Update the label column to include inline analysis if present
	df['label'] = df['label'].fillna(df['label_inline'])
	
	# Drop the inline columns we don't need anymore
	df = df.drop(columns=[col for col in df.columns if col.endswith('_inline') or col == 'path_str'], errors='ignore')

	# Keep only analysis rows by default (those have actual values)
	if not include_non_analysis and "type" in df.columns:
		df = df[df["type"] == "analysis"].copy()

	# Human-friendly path column
	if "path_pivot" in df.columns:
		df["Path"] = df["path_pivot"].apply(_format_path)
	elif "path" in df.columns:
		df["Path"] = df["path"].apply(_format_path)
	else:
		df["Path"] = ""

	# Ensure consistent columns for downstream pivot/formatting
	if unnest:
		# statistics/values are present when unnest=True
		if "statistics" not in df.columns or "values" not in df.columns:
			raise ValueError("Expected 'statistics' and 'values' columns when unnest=True.")
		df["Statistic"] = df["statistics"].astype(str)
	else:
		# Keep a single 'Value' column pointing to 'summary'
		df["Statistic"] = "summary"
		df = df.rename(columns={"summary": "values"})

	# Compose a pivot label if we have pivot levels
	def _pivot_label(x):
		if isinstance(x, list) and len(x) > 0:
			return " > ".join([str(v) for v in x])
		return None

	pivot_col = None
	if "pivot_lvl" in df.columns:
		df[".pivot_lbl"] = df["pivot_lvl"].apply(_pivot_label)
		if df[".pivot_lbl"].notna().any():
			pivot_col = ".pivot_lbl"

	# Narrow to the essential columns before going wide
	base_cols = [c for c in ["Path", "label", "Statistic", pivot_col, "values"] if c is not None]
	dfw = df.loc[:, base_cols].copy()
	dfw = dfw.rename(columns={"label": "Analysis", "values": "Value"})

	# Pivot wide on the pivot label when present
	if pivot_col is not None:
		wide = (
			dfw.pivot(index=["Path", "Analysis", "Statistic"], columns=pivot_col, values="Value")
			.reset_index()
		)
	else:
		wide = dfw

	# Build the GT table and apply some light formatting
	tbl = GT(wide)
	if title:
		tbl = tbl.tab_header(title=title, subtitle=subtitle or "")

	# Format numeric columns
	num_cols = [c for c in wide.columns if c not in ("Path", "Analysis", "Statistic")]
	if num_cols:
		tbl = tbl.fmt_number(columns=num_cols, decimals=decimals)

	# Slightly emphasize the row identifiers
	# (Safe if methods aren't present; GT methods are chainable.)
	try:
		tbl = tbl.opt_align_table_header(align="left")
	except Exception:
		pass

	return tbl

