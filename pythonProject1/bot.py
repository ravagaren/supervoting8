import asyncio
import logging
from typing import Dict, List, Optional, Any

import config

from handlers.control_commands import router, options_4
from utils.refine_form_text import refine_form_text
from utils.like_counter import like_counter

# Импорт StateManager для управления состоянием
from state_manager import state_manager

from aiogram import F
from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from aiogram.utils.formatting import Pre
from aiogram.utils.formatting import Text, as_line, Bold

from my_types import AnalysisResult
from utils.usefull_utils import generate_test_content_message, analysis_message_and_rating_calculation

# ============ Константы ============
SEPARATOR = '_________________'
INITIAL_RATING_TEXT = 'Рейтинг анкеты(0.0)'
CALLBACK_LIKE_ACTION = '✅like'
CALLBACK_SUPER_LIKE_ACTION = '✅super_like'
ERROR_SUPER_LIKE_UNAVAILABLE = 'Супер симпатия пока недоступна'
INITIAL_FORM_NAME = 'Анкета'
# ===================================

summaru: List[str] = [INITIAL_FORM_NAME]

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


def setup_dispatcher(bot: Bot, dispatcher: Dispatcher) -> None:
    """Configure dispatcher with handlers and middlewares."""
    dispatcher.include_router(router)


async def add_bottom_bar_encourages_clicking_buttons(
    message_id_value: str,
    like_value: int,
    super_like_value: int,
    message_text_value: str = 'test_text',
    info_line_value: str = '',
    from_user_first_name_value: str = '',
    user_reputation: int = 50
) -> str:
    """
    Добавляет нижнюю панель с информацией о рейтинге и кнопками.
    
    Args:
        message_id_value: ID сообщения/анкеты
        like_value: Количество лайков
        super_like_value: Количество супер-лайков
        message_text_value: Текст сообщения
        info_line_value: Дополнительная информация
        from_user_first_name_value: Имя пользователя
        user_reputation: Репутация пользователя
        
    Returns:
        Строка с формированным HTML сообщением
    """
    try:
        integral_grade: float = round(
            like_value * 0.0003 * 10 + super_like_value * 0.7 * 10, 
            4
        )

        logger.info(f'integral_grade is {integral_grade}')

        if (integral_grade > 259
                or integral_grade > 50
                or integral_grade > 100
                or integral_grade > 150
                or integral_grade > 15):
            if (integral_grade > 50
                or integral_grade > 100
                or integral_grade > 150):

                info_line_value = (
                    'Поздравляем пользователя ' + from_user_first_name_value +
                    ' с репутацией = ' + str(user_reputation) +
                    ' Его голос увеличил популярность анкеты и ввел его в список претендентов на общение! '
                    + info_line_value
                )
            else:
                info_line_value = (
                    'Поздравляем пользователя ' + from_user_first_name_value +
                    ' с репутацией = ' + str(user_reputation) +
                    ' Благодаря нему увеличена популярность анкеты! ' + info_line_value
                )

        content: Text = Text(
            as_line(SEPARATOR),
            as_line(Pre(Bold(info_line_value))),
            as_line('Популярность', f"({integral_grade})"),
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
    
    Args:
        message: Объект сообщения Telegram
        content: Отформатированный контент
        origin_message_id: ID исходного сообщения
        like_value: Количес��во лайков
        super_like_value: Количество супер-лайков
        from_user_first_name_value: Имя пользователя
        from_user_id_value: ID пользователя
    """
    try:
        content_html: str = content.as_html()
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

        # Использование StateManager вместо глобального словаря
        state_manager.set_message_rating(origin_message_id, like_value, super_like_value)

    except Exception as e:
        logger.error(f"Error in process_questionnaire_message: {e}", exc_info=True)


@router.message(F.content_type == ContentType.PHOTO)
async def add_bottom_and_buttons_from_photo(
        message: types.Message,
        from_user_id_value: Optional[int] = None,
        origin_message_id_value: Optional[str] = None,
        from_user_first_name_value: str = '',
        local_dictionary_storing_user_ratings: Optional[Dict[int, Dict[str, int]]] = None
) -> None:
    """
    Обработчик сообщений с фото.
    
    Извлекает рейтинг из state_manager вместо глобального словаря.
    Использует URL отправленной фотографии через reverse proxy вместо Telegraph.
    """
    try:
        result: AnalysisResult = await analysis_message_and_rating_calculation(
            from_user_id_value,
            message,
            origin_message_id_value,
            local_dictionary_storing_user_ratings,
            state_manager.get_all_message_ratings()
        )

        if not result.origin_message_id:
            logger.warning("origin_message_id is None in add_bottom_and_buttons_from_photo")
            return

        # Получение рейтинга через StateManager
        message_rating = state_manager.get_message_rating(result.origin_message_id)
        like_value: int = message_rating.like
        super_like_value: int = message_rating.super_like

        logger.info('We are handling photo')

        # Normalize caption to avoid AttributeError when it's None
        caption: str = getattr(message, 'caption', None) or ""
        try:
            logger.info(f'Position _ {caption.find(SEPARATOR)}')
        except Exception as e:
            logger.error(f'Position check failed for caption: {e}')

        # Получаем фото наибольшего размера
        photo = message.photo[-1]

        # Используем file_id напрямую
        photo_file_id = photo.file_id

        # Получаем информацию о файле для логирования
        file_info = await bot.get_file(photo.file_id)
        logger.info(f'Photo file_id: {photo_file_id}')
        logger.info(f'Photo file_path: {file_info.file_path}')

        # Получаем URL через reverse proxy (вариант 2 - безопаснее)
        image_url: str = await get_photo_url_via_proxy(file_info.file_path, config.token)
        if not image_url:
            # Fallback на прямую Telegram CDN ссылку без проксирования
            image_url = await get_telegram_photo_url_direct(file_info.file_path, config.token)
        
        if not image_url:
            image_url = photo.file_id  # Последний fallback

        content: Text = await generate_test_content_message(image_url, caption)

        logger.info(f'content - {content.as_html()}')

        if SEPARATOR not in content.as_html():
            content_text: str = await add_bottom_bar_encourages_clicking_buttons(
                result.origin_message_id,
                like_value,
                super_like_value,
                content.as_html()
            )

            logger.info(f'content_text is {content_text}')

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

    except Exception as e:
        logger.error(f"Error in add_bottom_and_buttons_from_photo: {e}", exc_info=True)


@router.message(F.text)
async def add_bottom_and_buttons_from_text(
    message: types.Message,
    from_user_id_value: Optional[int] = None,
    origin_message_id_value: Optional[str] = None,
    from_user_first_name_value: str = '',
    local_dictionary_storing_user_ratings: Optional[Dict[int, Dict[str, int]]] = None
) -> None:
    """
    Обработчик сообщений с текстом.
    
    Использует StateManager для управления рейтингом.
    """
    global summaru

    try:
        logger.info(f'from_user_first_name_value - {from_user_first_name_value}')

        result: AnalysisResult = await analysis_message_and_rating_calculation(
            from_user_id_value,
            message,
            origin_message_id_value,
            local_dictionary_storing_user_ratings,
            state_manager.get_all_message_ratings()
        )

        if not result.origin_message_id:
            logger.warning("origin_message_id is None in add_bottom_and_buttons_from_text")
            return

        # Получение рейтинга через StateManager
        message_rating = state_manager.get_message_rating(result.origin_message_id)
        like_value: int = message_rating.like
        super_like_value: int = message_rating.super_like

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

        content: Text = await generate_test_content_message(image_anket_url, text)

        logger.info(f'content - {content.as_html()}')

        if SEPARATOR not in content.as_html():

            content_text: str = await add_bottom_bar_encourages_clicking_buttons(
                result.origin_message_id,
                like_value,
                super_like_value,
                content.as_html()
            )

            logger.info(f'content_text is {content_text}')

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

        # Использование StateManager вместо глобального словаря
        state_manager.set_message_rating(result.origin_message_id, like_value, super_like_value)

    except Exception as e:
        logger.error(f"Error in add_bottom_and_buttons_from_text: {e}", exc_info=True)


import aiohttp
import json


async def get_telegram_photo_url_direct(file_path: str, bot_token: str) -> Optional[str]:
    """
    Получить прямую ссылку на фотографию через Telegram CDN (Вариант 1).
    
    Фотография будет доступна по ссылке в браузере напрямую.
    
    Args:
        file_path: Путь файла (из bot.get_file())
        bot_token: Токен бота
    
    Returns:
        Прямая ссылка на файл или None
    """
    try:
        # Прямая ссылка на Telegram CDN
        url = f'https://api.telegram.org/file/bot{bot_token}/{file_path}'
        
        # Проверяем, что файл существует
        async with aiohttp.ClientSession() as session:
            async with session.head(url) as resp:
                if resp.status == 200:
                    logger.info(f'Photo direct CDN URL: {url}')
                    return url
                    
    except Exception as e:
        logger.error(f"Error getting direct photo URL: {e}", exc_info=True)
    
    return None


async def get_photo_url_via_proxy(file_path: str, bot_token: str) -> Optional[str]:
    """
    Получить ссылку на фотографию через reverse proxy (Вариант 2 - РЕКОМЕНДУЕТСЯ).
    
    Скрывает токен бота в ссылке - безопаснее для публичного использования.
    
    Требует настройк�� на сервере:
    - Создать endpoint: GET /api/photo/<file_path>
    - Backend перенаправляет запрос на Telegram CDN со своим токеном в headers
    
    Args:
        file_path: Путь файла (из bot.get_file())
        bot_token: Токен бота (используется для прямого доступа, если прокси недоступен)
    
    Returns:
        Ссылка через proxy или None
    """
    try:
        # Используем прокси-endpoint вашего сервера
        # Пример: https://yourdomain.com/api/photo/documents/file.jpg
        proxy_url = f'{config.host_url}/api/photo/{file_path}'
        
        logger.info(f'Trying proxy URL: {proxy_url}')
        
        # Проверяем, что эндпоинт доступен
        async with aiohttp.ClientSession() as session:
            async with session.head(proxy_url) as resp:
                if resp.status == 200:
                    logger.info(f'Photo proxy URL successful: {proxy_url}')
                    return proxy_url
                else:
                    logger.warning(f'Proxy endpoint returned status {resp.status}')
                    
    except Exception as e:
        logger.error(f"Error getting photo via proxy: {e}", exc_info=True)
    
    return None


async def upload_photo_to_telegraph(file_path: str, bot_token: str) -> Optional[str]:
    """
    DEPRECATED: Загрузить фото на Telegraph и получить постоянный URL.
    
    Telegraph отключил возможность загрузки анонимных фото.
    Используйте вместо этого:
    - get_telegram_photo_url_direct() - прямая CDN ссылка
    - get_photo_url_via_proxy() - ссылка через reverse proxy (рекомендуется)
    
    Returns:
        URL фото или None (функция оставлена для обратной совместимости)
    """
    logger.warning("upload_photo_to_telegraph is deprecated. Use get_photo_url_via_proxy instead.")
    
    try:
        file_url = f'https://api.telegram.org/file/bot{bot_token}/{file_path}'

        async with aiohttp.ClientSession() as session:
            # Загружаем файл с Telegram
            async with session.get(file_url) as resp:
                if resp.status == 200:
                    photo_data = await resp.read()

                    # Пытаемся загрузить на Telegraph (может не работать)
                    async with session.post(
                            'https://telegra.ph/upload',
                            data={'file': photo_data}
                    ) as telegraph_resp:
                        if telegraph_resp.status == 200:
                            result = await telegraph_resp.json()
                            if result and isinstance(result, list) and len(result) > 0:
                                telegraph_url = 'https://telegra.ph' + result[0]['src']
                                logger.info(f'Uploaded to Telegraph: {telegraph_url}')
                                return telegraph_url

    except Exception as e:
        logger.error(f"Error uploading to Telegraph: {e}", exc_info=True)
        return None


@router.callback_query(F.data.startswith("✅"))
async def callbacks_calculation_of_likes(callback: types.CallbackQuery) -> None:
    """
    Обработчик нажатия на кнопки лайков и супер-лайков.
    
    Использует StateManager для управления рейтингом пользователей.
    """
    try:
        logger.info(f'callback.from_user.first_name - {callback.from_user.first_name}')
        logger.info(f'callback.data - {callback.data}')
        
        action: str = callback.data.split(":")[0]
        logger.info(f'action - {action}')

        questionnaire_message_id: str = str(callback.data.split(":")[1])
        logger.info(f'questionnaire_message_id - {questionnaire_message_id}')

        # Инициализация рейтинга сообщения через StateManager
        message_rating = state_manager.get_message_rating(questionnaire_message_id)
        
        # Инициализация рейтинга пользователя для этого сообщения
        user_rating = state_manager.get_user_rating(callback.from_user.id, questionnaire_message_id)

        logger.info(f'message_ratings is {state_manager.get_all_message_ratings()}')
        logger.info(f'user_ratings_dict - {state_manager.get_all_user_ratings()}')

        like_value: int = message_rating.like
        super_like_value: int = message_rating.super_like

        # Normalize callback message html_text to avoid AttributeError when it's None
        cb_html: str = getattr(callback.message, 'html_text', None) or ""

        if (cb_html.find(INITIAL_RATING_TEXT) == -1
                and like_value == 0
                and super_like_value == 0):
            logger.info('Нашли готовую интегральную оценку')
            like_value, super_like_value = await like_counter(questionnaire_message_id, cb_html)

            # Обновление рейтинга через StateManager
            state_manager.set_message_rating(questionnaire_message_id, like_value, super_like_value)

        if action == CALLBACK_LIKE_ACTION:

            logger.info(f'message_ratings is {state_manager.get_all_message_ratings()}')
            
            # Использование методов StateManager для инкремента
            state_manager.increment_message_like(questionnaire_message_id)
            state_manager.increment_user_like(callback.from_user.id, questionnaire_message_id)
            
            logger.info(f'in callback user_data - {state_manager.get_all_user_ratings()}')

            try:
                await callback.answer()
            except Exception as answer_error:
                logger.error(f"Failed to send callback answer: {answer_error}", exc_info=True)
            
            await add_bottom_and_buttons_from_text(
                callback.message,
                callback.from_user.id,
                questionnaire_message_id,
                callback.from_user.first_name,
                state_manager.get_all_user_ratings()
            )

        elif action == CALLBACK_SUPER_LIKE_ACTION:
            logger.info(f'message_ratings is {state_manager.get_all_message_ratings()}')
            
            # Проверка, что пользователь не голосовал за супер-лайк
            if state_manager.has_user_voted_super_like(callback.from_user.id, questionnaire_message_id):
                logger.info(f'User {callback.from_user.id} already voted super_like for {questionnaire_message_id}')
                try:
                    await callback.answer(
                        text=ERROR_SUPER_LIKE_UNAVAILABLE,
                        show_alert=True
                    )
                except Exception as answer_error:
                    logger.error(f"Failed to send callback answer (super_like unavailable): {answer_error}", exc_info=True)
            else:
                # Использование методов StateManager для инкремента
                state_manager.increment_message_super_like(questionnaire_message_id)
                state_manager.increment_user_super_like(callback.from_user.id, questionnaire_message_id)
                
                logger.info(f'message_ratings is {state_manager.get_all_message_ratings()}')
                logger.info(f'in callback user_data - {state_manager.get_all_user_ratings()}')

                try:
                    await callback.answer()
                except Exception as answer_error:
                    logger.error(f"Failed to send callback answer: {answer_error}", exc_info=True)
                
                await add_bottom_and_buttons_from_text(
                    callback.message,
                    callback.from_user.id,
                    questionnaire_message_id,
                    callback.from_user.first_name,
                    state_manager.get_all_user_ratings()
                )
    
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
