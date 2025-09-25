import pandas as pd
import inspect
from typing import Callable, Union, Any


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

    
def get_top_globals():
    """Get the globals dictionary from the top-level frame"""
    frame = inspect.currentframe()
    
    # Navigate up the frame stack until we reach the top
    while frame.f_back is not None:
        frame = frame.f_back
    
    # Return the globals from the top-level frame
    return frame.f_globals

