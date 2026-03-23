"""
Performance tests for AnalysisTree.run() with varying tree complexity and dataset sizes.

These tests are marked with @pytest.mark.performance and are SKIPPED BY DEFAULT.

Usage:
    # Skip performance tests (default behavior)
    pytest tests/

    # Run performance tests explicitly
    pytest tests/test_performance.py -m performance -v -s

    # Run all tests including performance tests
    pytest tests/ -m ""

    # See detailed timing output
    pytest tests/test_performance.py -m performance -v -s
"""

import pytest
import pandas as pd
import numpy as np
import time
import tracemalloc
from pyMyriad import AnalysisTree


# Fixtures for generating synthetic datasets

@pytest.fixture
def small_dataset():
    """1K rows for quick baseline testing."""
    np.random.seed(42)
    return pd.DataFrame({
        'Gender': np.random.choice(['M', 'F'], 1_000),
        'Country': np.random.choice(['US', 'UK', 'FR', 'DE'], 1_000),
        'AgeGroup': np.random.choice(['18-30', '31-50', '51-70', '70+'], 1_000),
        'Income': np.random.normal(50000, 15000, 1_000),
        'Expenses': np.random.normal(30000, 10000, 1_000),
        'Savings': np.random.normal(10000, 5000, 1_000),
    })


@pytest.fixture
def medium_dataset():
    """10K rows for moderate load testing."""
    np.random.seed(42)
    return pd.DataFrame({
        'Gender': np.random.choice(['M', 'F'], 10_000),
        'Country': np.random.choice(['US', 'UK', 'FR', 'DE'], 10_000),
        'AgeGroup': np.random.choice(['18-30', '31-50', '51-70', '70+'], 10_000),
        'Income': np.random.normal(50000, 15000, 10_000),
        'Expenses': np.random.normal(30000, 10000, 10_000),
        'Savings': np.random.normal(10000, 5000, 10_000),
    })


@pytest.fixture
def large_dataset():
    """100K rows for stress testing."""
    np.random.seed(42)
    return pd.DataFrame({
        'Gender': np.random.choice(['M', 'F'], 100_000),
        'Country': np.random.choice(['US', 'UK', 'FR', 'DE'], 100_000),
        'AgeGroup': np.random.choice(['18-30', '31-50', '51-70', '70+'], 100_000),
        'Income': np.random.normal(50000, 15000, 100_000),
        'Expenses': np.random.normal(30000, 10000, 100_000),
        'Savings': np.random.normal(10000, 5000, 100_000),
    })


def format_duration(seconds):
    """Format duration in human-readable format."""
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.2f} μs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f} ms"
    else:
        return f"{seconds:.2f} s"


def format_memory(bytes_value):
    """Format memory in human-readable format."""
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024**2:
        return f"{bytes_value / 1024:.2f} KB"
    elif bytes_value < 1024**3:
        return f"{bytes_value / 1024**2:.2f} MB"
    else:
        return f"{bytes_value / 1024**3:.2f} GB"


def benchmark(func, *args, **kwargs):
    """
    Benchmark a function with timing and optional memory profiling.
    
    Returns:
        tuple: (result, duration_seconds, peak_memory_bytes)
    """
    # Start memory tracking
    tracemalloc.start()
    
    # Measure execution time
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    
    # Get peak memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    duration = end_time - start_time
    
    return result, duration, peak


# Performance Tests

@pytest.mark.performance
def test_simple_tree_small_dataset(small_dataset):
    """
    Benchmark: Simple tree (no splits) on 1K rows.
    
    Tests basic analysis performance without data partitioning overhead.
    """
    tree = AnalysisTree().analyze_by(
        mean_income=lambda df: np.mean(df.Income),
        std_income=lambda df: np.std(df.Income),
        count=lambda df: len(df),
        min_income=lambda df: np.min(df.Income),
        max_income=lambda df: np.max(df.Income),
        median_expenses=lambda df: np.median(df.Expenses),
        total_savings=lambda df: np.sum(df.Savings),
    )
    
    result, duration, peak_memory = benchmark(tree.run, small_dataset)
    
    print(f"\n{'='*60}")
    print("Simple Tree + Small Dataset (1K rows)")
    print(f"{'='*60}")
    print(f"Duration: {format_duration(duration)}")
    print(f"Peak Memory: {format_memory(peak_memory)}")
    print(f"Result nodes: {len(result)}")
    
    assert result is not None
    assert duration < 1.0  # Should complete in under 1 second


@pytest.mark.performance
def test_simple_tree_large_dataset(large_dataset):
    """
    Benchmark: Simple tree (no splits) on 100K rows.
    
    Tests how analysis scales with dataset size.
    """
    tree = AnalysisTree().analyze_by(
        mean_income=lambda df: np.mean(df.Income),
        std_income=lambda df: np.std(df.Income),
        count=lambda df: len(df),
        min_income=lambda df: np.min(df.Income),
        max_income=lambda df: np.max(df.Income),
        median_expenses=lambda df: np.median(df.Expenses),
        total_savings=lambda df: np.sum(df.Savings),
    )
    
    result, duration, peak_memory = benchmark(tree.run, large_dataset)
    
    print(f"\n{'='*60}")
    print("Simple Tree + Large Dataset (100K rows)")
    print(f"{'='*60}")
    print(f"Duration: {format_duration(duration)}")
    print(f"Peak Memory: {format_memory(peak_memory)}")
    print(f"Result nodes: {len(result)}")
    
    assert result is not None
    assert duration < 5.0  # Should complete in under 5 seconds


@pytest.mark.performance
def test_complex_tree_small_dataset(small_dataset):
    """
    Benchmark: Complex tree (2 split levels) on 1K rows.
    
    Tests overhead of data partitioning and nested analysis.
    """
    tree = (AnalysisTree()
        .split_by("df.Gender", label="Gender")
        .split_by("df.Country", label="Country")
        .analyze_by(
            mean_income=lambda df: np.mean(df.Income),
            std_income=lambda df: np.std(df.Income),
            count=lambda df: len(df),
            savings_rate=lambda df: np.mean(df.Savings / df.Income) if len(df) > 0 else 0,
        ))
    
    result, duration, peak_memory = benchmark(tree.run, small_dataset)
    
    print(f"\n{'='*60}")
    print("Complex Tree (2 levels) + Small Dataset (1K rows)")
    print(f"{'='*60}")
    print(f"Duration: {format_duration(duration)}")
    print(f"Peak Memory: {format_memory(peak_memory)}")
    print(f"Result structure: {list(result.keys())}")
    
    assert result is not None
    assert duration < 2.0  # Should complete in under 2 seconds


@pytest.mark.performance
def test_complex_tree_large_dataset(large_dataset):
    """
    Benchmark: Complex tree (2 split levels) on 100K rows.
    
    Tests how complex analysis scales with large datasets.
    """
    tree = (AnalysisTree()
        .split_by("df.Gender", label="Gender")
        .split_by("df.Country", label="Country")
        .analyze_by(
            mean_income=lambda df: np.mean(df.Income),
            std_income=lambda df: np.std(df.Income),
            count=lambda df: len(df),
            savings_rate=lambda df: np.mean(df.Savings / df.Income) if len(df) > 0 else 0,
        ))
    
    result, duration, peak_memory = benchmark(tree.run, large_dataset)
    
    print(f"\n{'='*60}")
    print("Complex Tree (2 levels) + Large Dataset (100K rows)")
    print(f"{'='*60}")
    print(f"Duration: {format_duration(duration)}")
    print(f"Peak Memory: {format_memory(peak_memory)}")
    print(f"Result structure: {list(result.keys())}")
    
    assert result is not None
    assert duration < 10.0  # Should complete in under 10 seconds


@pytest.mark.performance
def test_very_complex_tree_medium_dataset(medium_dataset):
    """
    Benchmark: Very complex tree (3 split levels) on 10K rows.
    
    Tests deeply nested analysis with multiple stratification levels.
    """
    tree = (AnalysisTree()
        .split_by("df.Gender", label="Gender")
        .split_by("df.Country", label="Country")
        .split_by("df.AgeGroup", label="AgeGroup")
        .analyze_by(
            mean_income=lambda df: np.mean(df.Income),
            std_income=lambda df: np.std(df.Income),
            count=lambda df: len(df),
            total_expenses=lambda df: np.sum(df.Expenses),
            savings_rate=lambda df: np.mean(df.Savings / df.Income) if len(df) > 0 else 0,
        ))
    
    result, duration, peak_memory = benchmark(tree.run, medium_dataset)
    
    print(f"\n{'='*60}")
    print("Very Complex Tree (3 levels) + Medium Dataset (10K rows)")
    print(f"{'='*60}")
    print(f"Duration: {format_duration(duration)}")
    print(f"Peak Memory: {format_memory(peak_memory)}")
    print(f"Result structure: {list(result.keys())}")
    
    assert result is not None
    assert duration < 5.0  # Should complete in under 5 seconds


# Summary comparisons (optional utility)

@pytest.mark.performance
def test_performance_summary(small_dataset, medium_dataset, large_dataset):
    """
    Comparative benchmark: Run multiple configurations and print summary table.
    
    This test provides an overview of performance characteristics across
    different tree complexity and dataset size combinations.
    """
    results = []
    
    # Configuration 1: Simple + Small
    tree_simple = AnalysisTree().analyze_by(
        mean_income=lambda df: np.mean(df.Income),
        count=lambda df: len(df),
    )
    _, dur, mem = benchmark(tree_simple.run, small_dataset)
    results.append(("Simple", "1K", dur, mem))
    
    # Configuration 2: Simple + Medium
    _, dur, mem = benchmark(tree_simple.run, medium_dataset)
    results.append(("Simple", "10K", dur, mem))
    
    # Configuration 3: Simple + Large
    _, dur, mem = benchmark(tree_simple.run, large_dataset)
    results.append(("Simple", "100K", dur, mem))
    
    # Configuration 4: Complex + Small
    tree_complex = (AnalysisTree()
        .split_by("df.Gender")
        .split_by("df.Country")
        .analyze_by(
            mean_income=lambda df: np.mean(df.Income),
            count=lambda df: len(df),
        ))
    _, dur, mem = benchmark(tree_complex.run, small_dataset)
    results.append(("Complex (2 levels)", "1K", dur, mem))
    
    # Configuration 5: Complex + Medium
    _, dur, mem = benchmark(tree_complex.run, medium_dataset)
    results.append(("Complex (2 levels)", "10K", dur, mem))
    
    # Configuration 6: Complex + Large
    _, dur, mem = benchmark(tree_complex.run, large_dataset)
    results.append(("Complex (2 levels)", "100K", dur, mem))
    
    # Print summary table
    print(f"\n{'='*80}")
    print("PERFORMANCE SUMMARY")
    print(f"{'='*80}")
    print(f"{'Tree Type':<25} {'Dataset':<10} {'Duration':<15} {'Peak Memory':<15}")
    print(f"{'-'*80}")
    
    for tree_type, dataset_size, duration, memory in results:
        print(f"{tree_type:<25} {dataset_size:<10} {format_duration(duration):<15} {format_memory(memory):<15}")
    
    print(f"{'='*80}\n")
    
    # Basic assertions
    assert all(dur < 30.0 for _, _, dur, _ in results), "All tests should complete in reasonable time"
