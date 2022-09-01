"""Enums."""

from __future__ import annotations

from enum import Enum


class Method(str, Enum):
    """Method enum"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class Version(Enum):
    """Version enum"""

    V1 = 1
    V2 = 2


class ActionType(str, Enum):
    """ActionType enum"""

    DEFAULT = "default"
    SCENE = "scene"
    DEVICE = "device"


class EffectCategory(str, Enum):
    """EffectCategory enum"""

    NONE = "none"
    DEFAULT = "default_presets"
    CUSTOM = "custom_presets"
