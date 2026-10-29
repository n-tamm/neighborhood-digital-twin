"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import ast
from pathlib import Path

from neighborhood_twin import __version__


def test_package_has_version() -> None:
    """The installed package exposes a non-empty version string."""
    assert __version__


def test_project_functions_have_docstrings() -> None:
    """Package and orchestration functions retain concise implementation documentation."""

    project_root = Path(__file__).resolve().parents[1]
    source_roots = (
        project_root / "src" / "neighborhood_twin",
        project_root / "notebooks",
    )
    missing: list[str] = []
    for source_root in source_roots:
        for path in sorted(source_root.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if ast.get_docstring(node) is None:
                        relative_path = path.relative_to(project_root)
                        missing.append(f"{relative_path}:{node.lineno}:{node.name}")

    assert not missing, "Functions missing docstrings:\n" + "\n".join(missing)
