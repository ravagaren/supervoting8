import logging
from aiogram import F, Router
from aiogram.types import CallbackQuery

from services.vote_service import VoteService

logger = logging.getLogger(__name__)
router = Router()
_vote_service = None


def configure(service) -> None:
    global _vote_service
    _vote_service = VoteService(service)


@router.callback_query(F.data.startswith("✅"))
async def handle_vote(callback: CallbackQuery) -> None:
    if _vote_service is None:
        return
    try:
        await _vote_service.process(callback)
    except (ValueError, IndexError) as exc:
        logger.warning("Invalid vote callback: %s", exc)
    except Exception:
        logger.exception("Error processing vote")
