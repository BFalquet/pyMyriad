import pandas as pd
import inspect


def scope_eval(df: pd.DataFrame = None, extra_context: dict = None, **kwargs):
    """
    Evaluate expressions in the context of a DataFrame and optional additional context.
    This function allows you to evaluate multiple expressions where the variables can be
    columns of the DataFrame, variables from the caller's scope, and any additional context provided.
    Args:
        df (pd.DataFrame, optional): The DataFrame whose columns will be available as variables. Defaults to None.
        extra_context (dict, optional): Additional context to include in the evaluation. Defaults to None.
        **kwargs: Expressions to evaluate, where keys are variable names and values are expressions as strings.
    Returns:
        dict: A dictionary with keys as the names of the evaluated expressions and values as the results.
    Examples:




    Notes:
        - Ensure that the expressions in `kwargs` are valid Python expressions.
        - The function uses `eval`, so be cautious about evaluating untrusted input.
    """

    assert len(kwargs) > 0, "At least one expression must be provided."

    ctx = {}

    if extra_context is not None:
        ctx.update(extra_context)

    # Evaluate each expression in the context
    results = {}
    for name, expr in kwargs.items():
        results.update({name: eval(expr, ctx, {"df": df})})

    return results

    
def get_top_globals():
    """Get the globals dictionary from the top-level frame"""
    frame = inspect.currentframe()
    
    # Navigate up the frame stack until we reach the top
    while frame.f_back is not None:
        frame = frame.f_back
    
    # Return the globals from the top-level frame
    return frame.f_globals

