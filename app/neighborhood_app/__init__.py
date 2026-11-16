"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Application support package for the Neighborhood Digital Twin.
"""

from neighborhood_app.data import AppSettings, NeighborhoodData, create_repository

__all__ = ["AppSettings", "NeighborhoodData", "create_repository"]
