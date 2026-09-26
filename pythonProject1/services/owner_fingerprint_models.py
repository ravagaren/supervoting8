"""Domain models for owner fingerprint checking."""
from dataclasses import dataclass
from enum import StrEnum


class OwnerStatus(StrEnum):
    """Possible states of owner identification."""

    FOUND = "owner_found"
    """Owner was successfully identified through digital fingerprint."""

    NOT_FOUND = "owner_not_found"
    """Owner could not be identified or no fingerprint data available."""


@dataclass(frozen=True)
class OwnerCheckResult:
    """Result of checking content owner through digital fingerprint.

    This is the output from OwnerFingerprintService. It indicates whether the owner
    was identified and what their reputation score is.
    """

    status: OwnerStatus
    """Status of owner identification: FOUND or NOT_FOUND."""

    owner_rating: int
    """Reputation score of the identified owner.

    When status=FOUND: typically 50 (default high reputation).
    When status=NOT_FOUND: typically 1 (minimal reputation).
    """

    owner_id: str | None = None
    """Unique identifier of the owner if identified.

    This could be a Telegram user ID, wallet address, or any other unique identifier
    returned by the fingerprint service. For MVP stub, this is always None.
    """
