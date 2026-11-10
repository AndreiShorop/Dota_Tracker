"""Dota Tracker package.

Clean-architecture desktop analytics for Dota 2.

Layers (dependencies point inward):
  presentation -> application -> domain
  infrastructure -> application/domain via ports and adapters
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
