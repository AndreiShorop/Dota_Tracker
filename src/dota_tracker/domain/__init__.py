"""Domain layer: core business entities, value objects, and repository ports.

Pure Python, framework-agnostic. No I/O, no SQLAlchemy models, no HTTP calls,
no Qt dependencies.
"""

from dota_tracker.domain.entities import (
    Hero,
    Item,
    Match,
    Player,
    PlayerMatch,
)
from dota_tracker.domain.exceptions import (
    HeroNotFoundError,
    ItemNotFoundError,
    MatchNotFoundError,
    PlayerNotFoundError,
)
from dota_tracker.domain.repositories import (
    HeroRepository,
    ItemRepository,
    MatchRepository,
    PlayerMatchRepository,
    PlayerRepository,
    Repository,
)
from dota_tracker.domain.value_objects import MatchOutcome

__all__ = [
    "Hero",
    "HeroNotFoundError",
    "HeroRepository",
    "Item",
    "ItemNotFoundError",
    "ItemRepository",
    "Match",
    "MatchNotFoundError",
    "MatchOutcome",
    "MatchRepository",
    "Player",
    "PlayerMatch",
    "PlayerMatchRepository",
    "PlayerNotFoundError",
    "PlayerRepository",
    "Repository",
]
