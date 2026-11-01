"""Boundary checks for category benchmarks using synthetic input only."""
import numpy as np
import pandas as pd

from features.category_features import compute_cost_per_category


def test_benchmarks_preserve_nonsequential_index_and_raw_values():
    source = pd.DataFrame({
        "sector": ["Roads", "Health", "Roads"],
        "sanctioned_amount": [100.0, 30.0, 300.0],
    }, index=[42, 7, 99])
    original = source.copy(deep=True)
    result = compute_cost_per_category(source)
    pd.testing.assert_frame_equal(source, original)
    pd.testing.assert_frame_equal(result[source.columns], original)
    assert result["category_mean_cost"].tolist() == [200.0, 30.0, 200.0]
    assert result["category_project_count"].tolist() == [2, 1, 2]
    assert result.loc[7, "cost_category_zscore"] == 0.0


def test_zero_cost_group_produces_finite_benchmarks():
    source = pd.DataFrame({
        "sector": ["Roads", "Roads"],
        "sanctioned_amount": [0.0, 0.0],
    })
    result = compute_cost_per_category(source)
    for name in ["category_mean_cost", "cost_relative_to_category", "cost_category_zscore"]:
        assert np.isfinite(result[name]).all()
        assert (result[name] == 0.0).all()


def test_missing_sanction_uses_recommendation_without_mutating_raw_data():
    source = pd.DataFrame({
        "sector": ["Health", "Health"],
        "sanctioned_amount": [None, 300.0],
        "recommended_amount": [100.0, 500.0],
    })
    result = compute_cost_per_category(source)
    assert result["category_mean_cost"].tolist() == [200.0, 200.0]
    assert pd.isna(result.loc[0, "sanctioned_amount"])
    pd.testing.assert_frame_equal(result[source.columns], source)
