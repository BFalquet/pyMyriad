"""Utility functions module.

This module provides helper functions for expression evaluation, string conversion,
and environment management used throughout pyMyriad.

Key functions:
- scope_eval(): Evaluate string expressions or call functions with DataFrame context
- scope_cross_eval(): Evaluate expressions with two DataFrames (for comparisons)
- analysis_to_string(): Convert lambda functions or expressions to readable strings
- count_or_length(): Count unique values or return length
- get_top_globals(): Get the caller's global namespace for auto-imports
- get_caller_globals(): Get caller's globals (alternative method)

These utilities enable pyMyriad's flexible expression evaluation system that supports
both string expressions and lambda functions.
"""

import pandas as pd
import inspect
import ast
import warnings
from typing import Callable, Union, Any


# Module-level default imports for expression evaluation
_DEFAULT_IMPORTS = {}
_default_imports_warned = False


def _get_default_imports():
    """Get default imports (numpy as np, pandas as pd) if available.
    
    Returns a dict with 'np' and 'pd' keys if those modules are importable.
    Prints a one-time warning when defaults are used.
    """
    global _default_imports_warned
    
    if _DEFAULT_IMPORTS:
        return _DEFAULT_IMPORTS
    
    try:
        import numpy as np
        _DEFAULT_IMPORTS['np'] = np
    except ImportError:
        pass
    
    _DEFAULT_IMPORTS['pd'] = pd  # pandas is already imported
    
    return _DEFAULT_IMPORTS


def _inject_default_imports(ctx: dict, warn: bool = True) -> dict:
    """Inject default imports into context if not already present.
    
    Args:
        ctx: The context dictionary to update
        warn: Whether to warn about injecting defaults
    
    Returns:
        Updated context dictionary with defaults injected
    """
    global _default_imports_warned
    
    defaults = _get_default_imports()
    injected = []
    
    for name, module in defaults.items():
        if name not in ctx:
            ctx[name] = module
            injected.append(name)
    
    if warn and injected and not _default_imports_warned:
        _default_imports_warned = True
        warnings.warn(
            f"Auto-injected default imports ({', '.join(injected)}) for expression evaluation. "
            "To silence this warning, pass explicit environ={'np': np, ...} to run() or use lambda functions.",
            UserWarning,
            stacklevel=6
        )
    
    return ctx


def scope_eval(df: pd.DataFrame = None, extra_context: dict = None, **kwargs):
    """
    Evaluate expressions or execute functions in the context of a DataFrame and optional additional context.
    This function allows you to evaluate multiple expressions or execute functions where the variables can be
    columns of the DataFrame, variables from the caller's scope, and any additional context provided.
    Args:
        df (pd.DataFrame, optional): The DataFrame whose columns will be available as variables. Defaults to None.
        extra_context (dict, optional): Additional context to include in the evaluation. Defaults to None.
        **kwargs: Expressions to evaluate or functions to execute, where keys are variable names and values are either:
                 - strings (expressions to evaluate)
                 - callable functions that take a DataFrame as first argument
    Returns:
        dict: A dictionary with keys as the names of the evaluated expressions/functions and values as the results.
    Examples:
        # String expressions (original behavior)
        scope_eval(df=df, mean_a="np.mean(df.A)", std_b="np.std(df.B)")
        
        # Function expressions (new behavior)  
        scope_eval(df=df, mean_a=lambda df: np.mean(df.A), std_b=lambda df: np.std(df.B))
        
        # Mixed usage
        scope_eval(df=df, mean_a=lambda df: np.mean(df.A), count="len(df)")

    Notes:
        - For string expressions, ensure they are valid Python expressions.
        - For functions, they should accept the DataFrame as the first argument.
        - The function uses `eval` for strings, so be cautious about evaluating untrusted input.
    """

    assert len(kwargs) > 0, "At least one expression or function must be provided."

    ctx = {}
    if extra_context is not None:
        ctx.update(extra_context)
    
    # Inject default imports (np, pd) if not already in context
    _inject_default_imports(ctx, warn=False)  # Warning handled at higher level

    # Evaluate each expression/function
    results = {}
    for name, expr_or_func in kwargs.items():
        if callable(expr_or_func):
            # Execute function with DataFrame as argument
            results[name] = expr_or_func(df)
        else:
            # Treat as string expression (original behavior)
            results[name] = eval(expr_or_func, ctx, {"df": df})

    return results

    
def get_caller_globals():
    """Get the globals dictionary from the caller's frame (outside pyMyriad modules).
    
    This function walks up the call stack and returns the globals from the first
    frame that is not part of the pyMyriad package. This allows expressions like
    'np.mean(df.A)' to work when numpy is imported in the user's code.
    
    Returns:
        dict: The globals dictionary from the caller's frame, with default imports
              (numpy as np, pandas as pd) injected if not already present.
    """
    frame = inspect.currentframe()
    pymyriad_path = __file__.rsplit('/', 1)[0]  # Directory containing this module
    
    # Walk up the stack to find the first frame outside pyMyriad
    while frame is not None:
        frame_file = frame.f_code.co_filename
        
        # Check if this frame is outside the pyMyriad package
        if not frame_file.startswith(pymyriad_path):
            caller_globals = frame.f_globals.copy()
            # Inject default imports if not present
            _inject_default_imports(caller_globals, warn=True)
            return caller_globals
        
        frame = frame.f_back
    
    # Fallback: return empty dict with default imports
    ctx = {}
    _inject_default_imports(ctx, warn=True)
    return ctx


def get_top_globals():
    """Get the globals dictionary from the caller's frame.
    
    Note: This function is kept for backward compatibility but now uses
    get_caller_globals() which finds the caller's frame instead of the
    absolute top of the stack.
    
    Returns:
        dict: The globals dictionary from the caller's frame.
    """
    return get_caller_globals()


def analysis_to_string(analysis):
    """Convert an analysis expression to a string representation.
    
    Args:
        analysis (str or function): The analysis expression, either as a string or a function.
    Returns:
        str: The string representation of the analysis expression.
    Examples:
        mfun = lambda df: np.mean(df.Income)
        analysis_to_string(mfun)  # Returns: "lambda df: np.mean(df.Income)"
    """
    if callable(analysis):
        try:
            source = inspect.getsourcelines(analysis)[0][0].strip()
            # Parse and extract just the lambda expression
            tree = ast.parse(source)
            return ast.get_source_segment(source, tree.body[0]).strip()
        except Exception as e:
            return(f"<function>")
    return str(analysis)

def count_or_length(data: pd.DataFrame, id: str) -> int:
    """Count the number of unique entities in the DataFrame based on the specified id column.
    
    Args:
        data (pd.DataFrame): The DataFrame to analyze.
        id (str): The name of the column whose unique counts identifies the number of entities.
    Returns:
        int: The number of unique entities in the DataFrame.
    Examples:
        df = pd.DataFrame({
            "id": [1, 2, 1, 3],
            "value": [10, 20, 10, 30]
        })
        count_or_length(df, "id")  # Returns: 3
    """
    if id is None:
        return len(data)
    else:
        return data[id].nunique()

def scope_cross_eval(df: pd.DataFrame = None, ref_df:pd.DataFrame = None, extra_context: dict = None, **kwargs):
    """
    Evaluate expressions or execute functions comparing two DataFrames (df and ref_df).
    This function allows you to evaluate expressions or execute functions for cross-analysis,
    where both `df` and `ref_df` are available as variables.
    Args:
        df (pd.DataFrame, optional): The primary DataFrame to analyze. Defaults to None.
        ref_df (pd.DataFrame, optional): The reference DataFrame for comparison. Defaults to None.
        extra_context (dict, optional): Additional context to include in the evaluation. Defaults to None.
        **kwargs: Expressions to evaluate or functions to execute, where keys are variable names and values are either:
                 - strings (expressions to evaluate, with `df` and `ref_df` available)
                 - callable functions that take two arguments: (df, ref_df)
    Returns:
        dict: A dictionary with keys as the names of the evaluated expressions/functions and values as the results.
    Examples:
        # String expressions comparing two DataFrames
        scope_cross_eval(df=df, ref_df=ref_df, mean_diff="np.mean(df.A) - np.mean(ref_df.A)")
        
        # Function expressions (must accept two arguments: df and ref_df)
        scope_cross_eval(df=df, ref_df=ref_df, mean_diff=lambda df, ref_df: np.mean(df.A) - np.mean(ref_df.A))
        
        # Mixed usage
        scope_cross_eval(df=df, ref_df=ref_df, mean_diff=lambda df, ref_df: df.A.mean() - ref_df.A.mean(), count="len(df)")

    Notes:
        - For string expressions, both `df` and `ref_df` are available as variables.
        - For functions, they must accept two arguments: (df, ref_df).
        - The function uses `eval` for strings, so be cautious about evaluating untrusted input.
    """

    assert len(kwargs) > 0, "At least one expression or function must be provided."

    ctx = {}
    if extra_context is not None:
        ctx.update(extra_context)
    
    # Inject default imports (np, pd) if not already in context
    _inject_default_imports(ctx, warn=False)  # Warning handled at higher level

    # Evaluate each expression/function
    results = {}
    for name, expr_or_func in kwargs.items():
        if callable(expr_or_func):
            # Execute function with DataFrame as argument
            results[name] = expr_or_func(df, ref_df)
        else:
            # Treat as string expression (original behavior)
            results[name] = eval(expr_or_func, ctx, {"df": df, "ref_df": ref_df})

    return results