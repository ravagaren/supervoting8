"""
Updated usefull_utils.py to use StateManager instead of global dictionaries.

This module provides utility functions for message analysis and content generation,
now with centralized state management through StateManager.
"""

from typing import Any, Optional
from aiogram.utils.formatting import (
    Text, as_line, TextLink, Url, HashTag, ExpandableBlockQuote, Bold
)

from keyboards.keyboard_builder import keyborad_builder
from my_types import AnalysisResult
from state_manager import state_manager


async def generate_test_content_message(image_url_value: Optional[str] = None, 
                                       text_form_value: Optional[str] = None) -> Text:
    """
    Generate formatted content message with image and text.
    
    Args:
        image_url_value: URL of the image to display
        text_form_value: Form text to display
        
    Returns:
        Formatted Text object for Telegram message
    """
    image_url: str

    if image_url_value is None:
        image_url = 'https://telegra.ph/file/94a1f3a5a8ec1e9e57597.jpg'
    else:
        image_url = image_url_value

    if text_form_value is None:
        content_form = (Text(
            as_line(TextLink('.', url=image_url)),
            as_line(Url("https://ift.tt/G2vJD1H")),
            as_line(HashTag("ж_верх "), HashTag("знакомства ")),
            as_line("1. Саша"),
            as_line("2. Леди"),
            as_line("3. #Москва"),
            ExpandableBlockQuote(
                as_line(Bold('Раскрыть ⬇⬇⬇')),
                as_line("4. свитч с уклоном вниз"),
                as_line("5.Ищу партнёра для сессионных отношений (цис-женщину, транс-мужчину Возраст: до 45 лет."),
                as_line("Фетиши: атлетизм и мускулистость, tomboy-style, андрогинность. "
                        "Не обязательно быть профи-спортсменом, но хотя бы минимальная физическая "
                        "развитость должна быть. Особая любовь к женщинам, которые занимаются единоборствами"),
                as_line("6А) БДСМ-super_like:"),
                as_line("Общее настроение экшенов: пытки, избиение гопниками, армейская "
                        "дедовщина, любое стихийное желание причинить боль"),
                as_line("Б) Сексуальные super_like: возможно всё, но не сразу, а по мере установления доверия"),
                as_line("Подробнее - https://ift.tt/d1z4Sqs"),
                as_line("id::!12345678"),
                as_line("РАНГ: Серебрянный"),
                as_line("~`!@#$%^&*()_`123456788900-"),
            ),
        ))
    else:
        hash_tag_index: int = text_form_value.find('#не_см_flog_ru')

        print('image_url - ', image_url)
        content_form = (Text(
            as_line(TextLink('.', url=image_url)),
            as_line(text_form_value[0:hash_tag_index + 150]),
            as_line(Bold('Раскрыть ⬇⬇⬇')),
            ExpandableBlockQuote(text_form_value[hash_tag_index + 150:len(text_form_value) - 1]),
            as_line('')
        ))

    return content_form


async def analysis_message_and_rating_calculation(
    from_user_id_value: Optional[int] = None,
    message: Optional[Any] = None,
    origin_message_id_value: Optional[str] = None,
    local_user_ratings_dict: Optional[dict] = None,
    local_dictionary_storing_message_ratings: Optional[dict] = None
) -> AnalysisResult:
    """
    Analyze message and calculate rating using StateManager.
    
    This function now uses StateManager for centralized state management instead of
    relying on global dictionaries. For backward compatibility, it can still accept
    local dictionaries, but the primary state is managed through state_manager.
    
    Args:
        from_user_id_value: User ID (optional, extracted from message if not provided)
        message: Telegram Message object
        origin_message_id_value: Message ID (optional, extracted from message if not provided)
        local_user_ratings_dict: For backward compatibility (deprecated)
        local_dictionary_storing_message_ratings: For backward compatibility (deprecated)
        
    Returns:
        AnalysisResult containing keyboard builder, IDs, and rating data
    """
    from_user_id: int
    origin_message_id: str

    print(' In technical_processing_form')

    # Extract user ID
    if from_user_id_value is None:
        from_user_id = message.from_user.id
    else:
        from_user_id = from_user_id_value
    print('from_user_id -', from_user_id)

    # Extract message ID
    if origin_message_id_value is None:
        origin_message_id = str(message.message_id)
    else:
        origin_message_id = origin_message_id_value
    print('origin_message_id -', origin_message_id)

    # Initialize ratings in StateManager
    message_rating = state_manager.get_message_rating(origin_message_id)
    user_rating = state_manager.get_user_rating(from_user_id, origin_message_id)

    print('message rating (from StateManager) - ', message_rating)
    print('user rating (from StateManager) - ', user_rating)
    print('message -', message)
    print('message.from_user.id -', message.from_user.id)

    # Build keyboard using message rating data
    builder = await keyborad_builder(
        {
            'like': message_rating.like,
            'super_like': message_rating.super_like
        },
        origin_message_id
    )

    # Return result with StateManager's data (backward compatible format)
    return AnalysisResult(
        builder=builder,
        origin_message_id=origin_message_id,
        local_user_ratings=state_manager.get_all_user_ratings(),
        message_ratings=state_manager.get_all_message_ratings(),
    )
