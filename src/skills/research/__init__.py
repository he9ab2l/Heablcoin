"""Research skills package.

Provides reusable helpers for search-heavy workflows such as
quantitative research briefings. Modules centralise prompt templates
and downstream persistence hooks (Notion, Markdown exports, etc.).
"""

from .quant_research import generate_quant_prompts, execute_quant_research

__all__ = ["generate_quant_prompts", "execute_quant_research"]
