"""Service for checking content owner through digital fingerprint.

This module provides an interface to check if a Telegram message content belongs
to an identified owner. The MVP implementation uses a random stub that simulates
the behavior of checking against a fingerprint database.

Future implementations can replace the stub with real fingerprint analysis:
- Cryptographic signatures
- Machine learning models
- Blockchain verification
- Third-party identity services
"""
import logging
import random
from typing import Callable, Optional

from aiogram.types import Message

from services.owner_fingerprint_models import OwnerCheckResult, OwnerStatus

logger = logging.getLogger(__name__)


class OwnerFingerprintService:
    """Interface for checking Telegram message owner through digital fingerprint.

    This service abstracts the logic of determining whether a message content
    belongs to a known owner. In MVP, it uses randomized behavior to test the flow.
    """

    async def check(self, message: Message) -> OwnerCheckResult:
        """Check if the Telegram message content belongs to an identified owner.

        Args:
            message: Telegram message to analyze.

        Returns:
            OwnerCheckResult with status and owner_rating.
            For MVP stub:
            - 50% chance of FOUND status with owner_rating=50
            - 50% chance of NOT_FOUND status with owner_rating=1
        """
        raise NotImplementedError("Subclasses must implement check()")


class RandomOwnerFingerprintService(OwnerFingerprintService):
    """MVP implementation using random stub for testing.

    This service simulates two possible outcomes with equal probability:
    1. Owner found: owner_rating = 50 (good reputation)
    2. Owner not found: owner_rating = 1 (minimal reputation)

    The randomization is controlled by an optional callable for testing purposes.
    """

    def __init__(self, random_source: Optional[Callable[[], bool]] = None):
        """Initialize the service with optional custom random source.

        Args:
            random_source: Optional callable that returns True/False for owner found status.
                          If None, uses random.choice() with 50/50 probability.
                          Useful for deterministic testing.
        """
        self._random_source = random_source

    async def check(self, message: Message) -> OwnerCheckResult:
        """Check owner status randomly.

        Args:
            message: Telegram message (not used in stub, kept for interface compatibility).

        Returns:
            OwnerCheckResult with random status and appropriate owner_rating.
        """
        # Use custom random source for tests, otherwise random.choice()
        if self._random_source is not None:
            owner_found = self._random_source()
        else:
            owner_found = random.choice([True, False])

        if owner_found:
            logger.debug(
                "Owner fingerprint check: FOUND for message_id=%d from user_id=%s",
                message.message_id,
                message.from_user.id,
            )
            return OwnerCheckResult(
                status=OwnerStatus.FOUND,
                owner_rating=50,
                owner_id=None,
            )
        else:
            logger.debug(
                "Owner fingerprint check: NOT_FOUND for message_id=%d from user_id=%s",
                message.message_id,
                message.from_user.id,
            )
            return OwnerCheckResult(
                status=OwnerStatus.NOT_FOUND,
                owner_rating=1,
                owner_id=None,
            )
