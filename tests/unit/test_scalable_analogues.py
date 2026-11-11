"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.scalable_analogues import (
    DEFAULT_LSH_CONFIGURATIONS,
    EXACT_REFERENCE_CONFIG,
    SCALABLE_ANALOGUE_SCHEMA_VERSION,
    LSHConfiguration,
    validate_lsh_configurations,
    validate_scalable_settings,
)


def test_scalable_contract_has_ordered_unique_approximation_configs() -> None:
    assert SCALABLE_ANALOGUE_SCHEMA_VERSION == "1.0.0"
    assert EXACT_REFERENCE_CONFIG == "exact_reference"
    assert len(DEFAULT_LSH_CONFIGURATIONS) == 3
    assert [item.bucket_length for item in DEFAULT_LSH_CONFIGURATIONS] == sorted(
        item.bucket_length for item in DEFAULT_LSH_CONFIGURATIONS
    )
    validate_lsh_configurations(DEFAULT_LSH_CONFIGURATIONS)


def test_lsh_configuration_validation_rejects_ambiguous_or_invalid_settings() -> None:
    with pytest.raises(ValueError, match="unique"):
        validate_lsh_configurations(
            (
                LSHConfiguration("same", 1.0, 4),
                LSHConfiguration("same", 2.0, 8),
            )
        )
    with pytest.raises(ValueError, match="reserved"):
        validate_lsh_configurations((LSHConfiguration(EXACT_REFERENCE_CONFIG, 1.0, 4),))
    with pytest.raises(ValueError, match="bucket lengths"):
        validate_lsh_configurations((LSHConfiguration("bad", 0.0, 4),))
    with pytest.raises(ValueError, match="hash-table"):
        validate_lsh_configurations((LSHConfiguration("bad", 1.0, 0),))


def test_scalable_settings_require_a_real_benchmark() -> None:
    validate_scalable_settings(
        horizons=(1, 3),
        queries_per_group=3,
        top_k=10,
        configurations=DEFAULT_LSH_CONFIGURATIONS,
    )
    with pytest.raises(ValueError, match="positive integers"):
        validate_scalable_settings(
            horizons=(0,),
            queries_per_group=3,
            top_k=10,
            configurations=DEFAULT_LSH_CONFIGURATIONS,
        )
    with pytest.raises(ValueError, match="queries_per_group"):
        validate_scalable_settings(
            horizons=(1,),
            queries_per_group=0,
            top_k=10,
            configurations=DEFAULT_LSH_CONFIGURATIONS,
        )
    with pytest.raises(ValueError, match="at least three"):
        validate_scalable_settings(
            horizons=(1,),
            queries_per_group=3,
            top_k=2,
            configurations=DEFAULT_LSH_CONFIGURATIONS,
        )
