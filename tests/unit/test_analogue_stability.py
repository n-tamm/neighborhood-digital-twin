"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.analogue_stability import validate_stability_settings


def test_stability_settings_require_a_valid_top_k_and_larger_shortlist() -> None:
    validate_stability_settings(top_k=10, shortlist_k=1000)
    with pytest.raises(ValueError, match="at least three"):
        validate_stability_settings(top_k=2, shortlist_k=1000)
    with pytest.raises(ValueError, match="shortlist_k"):
        validate_stability_settings(top_k=10, shortlist_k=9)
