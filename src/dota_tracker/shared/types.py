"""Common type aliases and newtypes for the application."""

from __future__ import annotations

from typing import NewType

PlayerId = NewType("PlayerId", int)
MatchId = NewType("MatchId", int)
HeroId = NewType("HeroId", int)
ItemId = NewType("ItemId", int)
AccountId = NewType("AccountId", int)

Timestamp = int
DurationSeconds = int

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
