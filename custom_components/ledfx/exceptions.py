"""LedFx API client exceptions."""


class LedFxError(BaseException):
    """LedFx error"""


class LedFxConnectionError(LedFxError):
    """LedFx connection error"""


class LedFxRequestError(LedFxError):
    """LedFx request error"""
