import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any

# from  import config
import config

from handlers.control_commands import router, options_4

from refine_form_text import refine_form_text

from like_counter import like_counter

# новый импорт
from aiogram import F

from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from aiogram.utils.formatting import (Pre)
from aiogram.utils.formatting import Text, as_line, Bold

from my_types import AnalysisResult
from utils.usefull_utils import generate_test_content_message, analysis_message_and_rating_calculation
from handlers import control_commands

# ============ Константы ============
SEPARATOR = '_________________'
INITIAL_RATING_TEXT = 'Рейтинг анкеты(0.0)'
CALLBACK_LIKE_ACTION = '✅like'
CALLBACK_SUPER_LIKE_ACTION = '✅super_like'
ERROR_SUPER_LIKE_UNAVAILABLE = 'Супер симпатия пока недоступна'
INITIAL_FORM_NAME = 'Анкета'
# ===================================

summaru: List[str] = [INITIAL_FORM_NAME]

# questionnaire_eval: dict = {'like': 0,
#                             'super_like': 0,
#                             # 'Wish': 0
#                             }

dictionary_storing_message_ratings: Dict[str, Dict[str, int]] = {}

# Здесь хранятся пользовательские данные.
# Т.к. это словарь в памяти, то при перезапуске он очистится
dictionary_storing_user_ratings: Dict[int, Dict[str, Dict[str, int]]] = {}

like_maximum: int = 93
super_like_maximum: int = 33

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Объект бота
bot: Bot = Bot(
    token=config.token,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,
    )
)
# Диспетчер


def setup_dispatcher(bot: Bot, dispatcher: Dispatcher) -> None:
    """Configure dispatcher with handlers and middlewares."""
    dispatcher.include_router(router)


def get_message_rating(message_id: str) -> Dict[str, int]:
    """Get or initialize message rating dictionary."""
    if message_id not in dictionary_storing_message_ratings:
        dictionary_storing_message_ratings[message_id] = {
            'like': 0,
            'super_like': 0
        }
    return dictionary_storing_message_ratings[message_id]


def get_user_rating(user_id: int, message_id: str) -> Dict[str, int]:
    """Get or initialize user rating for specific message."""
    if user_id not in dictionary_storing_user_ratings:
        dictionary_storing_user_ratings[user_id] = {}
    
    if message_id not in dictionary_storing_user_ratings[user_id]:
        dictionary_storing_user_ratings[user_id][message_id] = {
            'like': 0,
            'super_like': 0,
            'Wish': 0
        }
    
    return dictionary_storing_user_ratings[user_id][message_id]


async def add_bottom_bar_encourages_clicking_buttons(
    mesage_id_value: str,
    like_value: int,
    super_like_value: int,
    message_text_value: str = 'test_text',
    info_line_value: str = '',
    from_user_first_name_value: str = '',
    user_reputation: int = 50
) -> str:

    # global questionnaire_eval
    global dictionary_storing_message_ratings
    global like_maximum

    try:
        integral_grade: float = round(like_value * 0.0003 * 10 +
                                      super_like_value * 0.7 * 10
                                        , 4)

        logger.info(f'integral_grade is {integral_grade}')

        if (integral_grade > 259
                or integral_grade > 50
                or integral_grade > 100
                or integral_grade > 150
                or integral_grade > 15):
            if (integral_grade > 50
                or integral_grade > 100
                or integral_grade > 150):

                info_line_value = ('Поздравляем пользователя '+ from_user_first_name_value +
                                   'с репутацией = ' + str(user_reputation) +
                               ' Его голос увеличил популярность анкеты и ввел его в список претендентов на общение! '
                                   + info_line_value
                               )
            else:
                info_line_value = ('Поздравляем пользователя ' + from_user_first_name_value +
                                   ' с репутацией = ' + str(user_reputation) +
                                   ' Благодаря нему увеличена популярность анкеты! ' + info_line_value
                                   )

        content: Text = Text(
            as_line(SEPARATOR),
            as_line(Pre(Bold(info_line_value))),
            as_line('Популярность',
                    # f"({integral_grade:.19}"
                    f"({integral_grade}"
                    f")"
                    ),
            # as_line
            # (
            #     as_list
            #         (
            #         as_marked_section
            #             (
            #             # Bold(" Оцени анкету"),
            #             #print(f"{r2} ({r2:.2%})")
            #
            #             # as_key_value("Красота 💟",
            #             #         f"({dict_of_questionnaire_evaluation[mesage_id_value]["like"/\
            #             #                     like_maximum:.2%}"
            #             #               f")"
            #             #              ),
            #             as_key_value(" Интегральная оценка 💟",
            #                          f"({dict_of_questionnaire_evaluation[mesage_id_value]["like"] /
            #                              like_maximum:.2%}"
            #                          f")"
            #                          ),
            #             # as_key_value("Нужность практик 👩",
            #             #       f"({dict_of_questionnaire_evaluation[mesage_id_value]["super_like"] /
            #             #           super_like_maximum:.2%}"
            #             #       f")"
            #             #       ),
            #             # as_key_value("Хочу быть рядом 🔥",
            #             #              str(dict_of_questionnaire_evaluation[mesage_id_value]["Wish"])
            #             #              ),
            #             marker=" ",
            #         ),
            #     ),
            # ),
            as_line(' Отдай симпатию ❣', like_value),
            as_line(' ⁸¹²⁰⁹⁷⁹'),
            as_line(' Отдай супер симпатию ❤', super_like_value),
            as_line(' ¹²⁹⁰⁹⁸⁷'),
        )
        return_value: str = message_text_value + content.as_html()

        return return_value
    
    except Exception as e:
        logger.error(f"Error in add_bottom_bar_encourages_clicking_buttons: {e}", exc_info=True)
        return message_text_value


async def process_questionnaire_message(
    message: types.Message,
    content: Text,
    origin_message_id: str,
    like_value: int,
    super_like_value: int,
    from_user_first_name_value: str = '',
    from_user_id_value: Optional[int] = None
) -> None:
    """
    Обработать сообщение анкеты (фото или текст).
    
    Если SEPARATOR не найден в контенте - отправить новое сообщение.
    Если SEPARATOR найден - обновить существующее сообщение.
    """
    global dictionary_storing_message_ratings
    
    try:
        content_html = content.as_html()
        logger.info(f'content - {content_html}')

        if SEPARATOR not in content_html:
            # Сообщение без разделителя - отправить новое сообщение
            content_text: str = await add_bottom_bar_encourages_clicking_buttons(
                origin_message_id,
                like_value,
                super_like_value,
                content_html
            )

            logger.info(f'content_text is {content_text}')

            try:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=content_text,
                    link_preview_options=options_4,
                    reply_markup=None,
                )
            except Exception as send_error:
                logger.error(f"Failed to send message: {send_error}", exc_info=True)
        else:
            # Сообщение с разделителем - обновить существующее
            html_text: str = getattr(message, 'html_text', None) or ""

            if (html_text.find(INITIAL_RATING_TEXT) == -1
                    and like_value == 0
                    and super_like_value == 0):

                logger.info('Нашли готовую интегральную оценку')
                like_value, super_like_value = await like_counter(origin_message_id, html_text)

            # safe slicing even if marker not found
            idx: int = html_text.find(SEPARATOR)
            common_text: str = html_text[0:idx] if idx != -1 else html_text
            logger.info(f'common_text - {common_text}')

            common_text = await add_bottom_bar_encourages_clicking_buttons(
                origin_message_id,
                like_value,
                super_like_value,
                common_text,
                from_user_first_name_value=from_user_first_name_value,
                user_reputation=43
            )

            logger.info(f'common_text - {common_text}')

            try:
                await bot.edit_message_text(
                    text=common_text,
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    link_preview_options=options_4,
                    reply_markup=None,
                )
            except Exception as edit_error:
                logger.error(f"Failed to edit message: {edit_error}", exc_info=True)

        logger.info('Изменяем лайк и суперлайк')
        logger.info(f'like_value - {like_value}')
        logger.info(f'super_like_value - {super_like_value}')

        dictionary_storing_message_ratings[origin_message_id]["like"] = like_value
        dictionary_storing_message_ratings[origin_message_id]["super_like"] = super_like_value

    except Exception as e:
        logger.error(f"Error in process_questionnaire_message: {e}", exc_info=True)


@router.message(F.content_type == ContentType.PHOTO)
async def add_bottom_and_buttons_from_photo(
        message: types.Message,
        from_user_id_value: Optional[int] = None,
        origin_message_id_value: Optional[str] = None,
        from_user_first_name_value: str = '',
        local_dictionary_storing_user_ratings: Optional[Dict] = None
) -> None:
    global dictionary_storing_message_ratings

    try:
        result: AnalysisResult = await analysis_message_and_rating_calculation(
            from_user_id_value,
            message,
            origin_message_id_value,
            local_dictionary_storing_user_ratings,
            dictionary_storing_message_ratings
        )

        if not result.origin_message_id:
            logger.warning("origin_message_id is None in add_bottom_and_buttons_from_photo")
            return

        message_rating = get_message_rating(result.origin_message_id)
        like_value: int = message_rating.get("like", 0)
        super_like_value: int = message_rating.get("super_like", 0)

        logger.info('We are handling photo')

        # Normalize caption to avoid AttributeError when it's None
        caption: str = getattr(message, 'caption', None) or ""
        try:
            logger.info(f'Position _ {caption.find(SEPARATOR)}')
        except Exception as e:
            logger.error(f'Position check failed for caption: {e}')

        image_url: str = 'https://ravagaren.wordpress.com/wp-content/uploads/2023/03/photo_2023-08-19_11-36-11.jpg?w=640'

        content = await generate_test_content_message(image_url, caption)

        logger.info(f'content - {content.as_html()}')

        if SEPARATOR not in content.as_html():
            content_text: str = await add_bottom_bar_encourages_clicking_buttons(
                result.origin_message_id,
                like_value,
                super_like_value,
                content.as_html()
            )

            logger.info(f'content_text is {content_text}')

            # Use bot.send_message instead of message.answer so the handler can be called directly in tests
            try:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=content_text,
                    link_preview_options=options_4,
                    reply_markup=result.builder.as_markup(),
                )
            except Exception as send_error:
                logger.error(f"Failed to send message in add_bottom_and_buttons_from_photo: {send_error}",
                             exc_info=True)

        # Update global state from result
        dictionary_storing_message_ratings.update(result.message_ratings)

    except Exception as e:
        logger.error(f"Error in add_bottom_and_buttons_from_photo: {e}", exc_info=True)


@router.message(F.text)
async def add_bottom_and_buttons_from_text(
    message: types.Message,
    from_user_id_value: Optional[int] = None,
    origin_message_id_value: Optional[str] = None,
    from_user_first_name_value: str = '',
    local_dictionary_storing_user_ratings: Optional[Dict] = None
) -> None:

    global summaru
    global dictionary_storing_user_ratings
    global dictionary_storing_message_ratings

    try:
        logger.info(f'from_user_first_name_value - {from_user_first_name_value}')

        result: AnalysisResult = await analysis_message_and_rating_calculation(
            from_user_id_value,
            message,
            origin_message_id_value,
            local_dictionary_storing_user_ratings,
            dictionary_storing_message_ratings
        )

        if not result.origin_message_id:
            logger.warning("origin_message_id is None in add_bottom_and_buttons_from_text")
            return

        message_rating = get_message_rating(result.origin_message_id)
        like_value: int = message_rating.get("like", 0)
        super_like_value: int = message_rating.get("super_like", 0)

        # Normalize text/html_text to avoid AttributeError when they are None
        text: str = getattr(message, 'text', None) or ""
        html_text: str = getattr(message, 'html_text', None) or ""

        try:
            logger.info(f'Position _ {text.find(SEPARATOR)}')
        except Exception as e:
            logger.error(f'Position check failed for text: {e}')

        summaru.append(text)
        summaru = refine_form_text(summaru)

        if not summaru or len(summaru) == 0:
            logger.warning("summaru is empty after refine_form_text")
            return

        image_anket_url: str = summaru[0]

        logger.info(f'image_anket_url {image_anket_url}')

        content = await generate_test_content_message(image_anket_url, text)

        logger.info(f'content - {content.as_html()}')

        if SEPARATOR not in content.as_html():

            content_text: str = await add_bottom_bar_encourages_clicking_buttons(
                result.origin_message_id,
                like_value,
                super_like_value,
                content.as_html()
            )

            logger.info(f'content_text is {content_text}')

            # Use bot.send_message instead of message.answer so tests can call handler directly
            try:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=content_text,
                    link_preview_options=options_4,
                    reply_markup=result.builder.as_markup(),
                )
            except Exception as send_error:
                logger.error(f"Failed to send message in add_bottom_and_buttons_from_text: {send_error}", exc_info=True)
        else:

            if (html_text.find(INITIAL_RATING_TEXT) == -1
                                                     and like_value == 0
                                                and super_like_value == 0):

                logger.info('Нашли готовую интегральную оценку')
                like_value, super_like_value = await like_counter(result.origin_message_id, html_text)
                # print()

            # safe slicing even if marker not found (html_text.find returns -1 handled above)
            idx: int = html_text.find(SEPARATOR)
            common_text: str = html_text[0:idx] if idx != -1 else html_text
            logger.info(f'common_text - {common_text}')

            common_text = await add_bottom_bar_encourages_clicking_buttons(
                result.origin_message_id,
                like_value,
                super_like_value,
                common_text,
                from_user_first_name_value=from_user_first_name_value,
                user_reputation=43
            )

            logger.info(f'common_text - {common_text}')
            # Use bot.edit_message_text instead of message.edit_text so handler works in tests
            try:
                await bot.edit_message_text(
                    text=common_text,
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    link_preview_options=options_4,
                    reply_markup=result.builder.as_markup(),
                )
            except Exception as edit_error:
                logger.error(f"Failed to edit message in add_bottom_and_buttons_from_text: {edit_error}", exc_info=True)

        logger.info('Изменяем лайк и суперлайк')
        logger.info(f'like_value - {like_value}')
        logger.info(f'super_like_value - {super_like_value}')

        dictionary_storing_message_ratings[result.origin_message_id]["like"] = like_value
        dictionary_storing_message_ratings[result.origin_message_id]["super_like"] = super_like_value

    except Exception as e:
        logger.error(f"Error in add_bottom_and_buttons_from_text: {e}", exc_info=True)


@router.callback_query(F.data.startswith("✅"))
async def callbacks_calculation_of_likes(callback: types.CallbackQuery) -> None:
    global dictionary_storing_user_ratings

    try:
        logger.info(f'callback.from_user.first_name - {callback.from_user.first_name}')
        logger.info(f'callback.data - {callback.data}')
        
        action: str = callback.data.split(":")[0]
        logger.info(f'action - {action}')

        questionnaire_message_id: str = str(callback.data.split(":")[1])
        logger.info(f'questionnaire_message_id - {questionnaire_message_id}')

        # Initialize message rating if not exists
        get_message_rating(questionnaire_message_id)
        
        # Initialize user rating for this message if not exists
        user_rating = get_user_rating(callback.from_user.id, questionnaire_message_id)

        logger.info(f'dict_of_questionnaire_evaluation is {dictionary_storing_message_ratings}')
        logger.info(f'user_ratings_dict - {dictionary_storing_user_ratings}')

        message_rating = get_message_rating(questionnaire_message_id)
        like_value: int = message_rating.get('like', 0)
        super_like_value: int = message_rating.get('super_like', 0)

        # Normalize callback message html_text to avoid AttributeError when it's None
        cb_html: str = getattr(callback.message, 'html_text', None) or ""

        if (cb_html.find(INITIAL_RATING_TEXT) == -1
                and like_value == 0
                and super_like_value == 0):
            logger.info('Нашли готовую интегральную оценку')
            like_value, super_like_value = await like_counter(questionnaire_message_id, cb_html)

            dictionary_storing_message_ratings[questionnaire_message_id]['like'] = like_value
            dictionary_storing_message_ratings[questionnaire_message_id]['super_like'] = super_like_value

        if action == CALLBACK_LIKE_ACTION:

            logger.info(f'dict_of_questionnaire_evaluation is {dictionary_storing_message_ratings}')
            dictionary_storing_message_ratings[questionnaire_message_id]['like'] += 1
            dictionary_storing_user_ratings[callback.from_user.id][questionnaire_message_id]['like'] += 1
            logger.info(f'in callback user_data - {dictionary_storing_user_ratings}')

            try:
                await callback.answer()
            except Exception as answer_error:
                logger.error(f"Failed to send callback answer: {answer_error}", exc_info=True)
            
            await add_bottom_and_buttons_from_text(callback.message,
                                                   callback.from_user.id,
                                                   questionnaire_message_id,
                                                   callback.from_user.first_name,
                                                   dictionary_storing_user_ratings)

        elif action == CALLBACK_SUPER_LIKE_ACTION:
            logger.info(f'dict_of_questionnaire_evaluation is {dictionary_storing_message_ratings}')
            logger.info(f'user_ratings_dict[callback.from_user.id][questionnaire_message_id]["super_like"] is '
                  f'{dictionary_storing_user_ratings[callback.from_user.id][questionnaire_message_id]["super_like"]}'
                  )
            if dictionary_storing_user_ratings[callback.from_user.id][questionnaire_message_id]['super_like'] > 0:
                try:
                    await callback.answer(text=ERROR_SUPER_LIKE_UNAVAILABLE,
                                          show_alert=True
                                          )
                except Exception as answer_error:
                    logger.error(f"Failed to send callback answer (super_like unavailable): {answer_error}", exc_info=True)
            else:
                dictionary_storing_message_ratings[questionnaire_message_id]['super_like'] += 1
                logger.info(f'dict_of_questionnaire_evaluation is {dictionary_storing_message_ratings}')
                dictionary_storing_user_ratings[callback.from_user.id][questionnaire_message_id]['super_like'] += 1
                logger.info(f'in callback user_data - {dictionary_storing_user_ratings}')

                try:
                    await callback.answer()
                except Exception as answer_error:
                    logger.error(f"Failed to send callback answer: {answer_error}", exc_info=True)
                
                await add_bottom_and_buttons_from_text(callback.message,
                                                       callback.from_user.id,
                                                       questionnaire_message_id,
                                                       callback.from_user.first_name,
                                                       dictionary_storing_user_ratings)
    
    except IndexError as e:
        logger.error(f"Invalid callback data format: {e}", exc_info=True)
    
    except Exception as e:
        logger.error(f"Error in callbacks_calculation_of_likes: {e}", exc_info=True)


async def main() -> None:
    """Start the bot and polling for updates."""
    dispatcher: Dispatcher = Dispatcher()
    setup_dispatcher(bot, dispatcher)

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
