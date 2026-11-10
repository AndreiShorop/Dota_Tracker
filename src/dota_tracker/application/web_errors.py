"""Safe application-level failures for interactive web operations."""


class StorageUnavailableError(Exception):
    """The persistent store could not complete the request."""


class SyncUnavailableError(Exception):
    """The external sync service could not complete the request."""


class MatchDetailUnavailableError(Exception):
    """The external match detail service could not complete the request."""
