"""Сервис для создания и управления анкетами (полная и сокращённая версии)."""
import logging
import random
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from aiogram import Bot

logger = logging.getLogger(__name__)


class QuestionnaireType(Enum):
    """Тип анкеты."""
    FULL = "full"
    SHORT = "short"


@dataclass
class QuestionnaireData:
    """Структура данных анкеты."""
    user_id: int  # ID пользователя Telegram, создавшего анкету
    gender: str
    age: str
    address: str
    positioning: str
    questionnaire_type: QuestionnaireType
    created_at: datetime
    chat_id: int  # ID чата, где была создана анкета
    message_id: Optional[int] = None  # ID сообщения с анкетою


class QuestionnaireDataGenerator:
    """Генератор тестовых данных для MVP."""

    GENDERS = ["Мужчина", "Женщина", "Не указано", "Другое"]

    AGES = [
        "18-25", "26-35", "36-45", "46-55", "56-65", "65+"
    ]

    ADDRESSES = [
        "Москва", "Санкт-Петербург", "Казань", "Новосибирск", "Екатеринбург",
        "Воронеж", "Сочи", "Краснодар", "Киев", "Минск",
        "Онлайн", "Не указано"
    ]

    POSITIONINGS = [
        "Специалист", "Менеджер", "Разработчик", "Дизайнер", "Маркетолог",
        "Аналитик", "Консультант", "Предприниматель", "Фрилансер", "Студент"
    ]

    @staticmethod
    def generate_gender() -> str:
        """Генерировать случайный пол."""
        return random.choice(QuestionnaireDataGenerator.GENDERS)

    @staticmethod
    def generate_age() -> str:
        """Генерировать случайный возраст."""
        return random.choice(QuestionnaireDataGenerator.AGES)

    @staticmethod
    def generate_address() -> str:
        """Генерировать случайный адрес."""
        return random.choice(QuestionnaireDataGenerator.ADDRESSES)

    @staticmethod
    def generate_positioning() -> str:
        """Генерировать случайное позиционирование."""
        return random.choice(QuestionnaireDataGenerator.POSITIONINGS)

    @staticmethod
    def generate_user_id() -> int:
        """Генерировать случайный user ID для тестирования."""
        return random.randint(100_000_000, 999_999_999)


class QuestionnaireService:
    """Сервис для работы с анкетами."""

    def __init__(self):
        self.generator = QuestionnaireDataGenerator()
        # Временное in-memory хранилище для тестовых анкет, которые напарник
        # может передавать вручную для проверки цифрового слепка автора.
        self._manual_questionnaire_storage: dict[str, dict] = {}

    def create_short_questionnaire(
        self,
        user_id: int,
        chat_id: int,
        gender: Optional[str] = None,
        age: Optional[str] = None,
        address: Optional[str] = None,
        positioning: Optional[str] = None,
    ) -> QuestionnaireData:
        """Создать сокращённую анкету с обязательными полями.

        Параметры:
            user_id: ID пользователя Telegram
            chat_id: ID чата
            gender: Пол (если None, будет сгенерирован)
            age: Возраст (если None, будет сгенерирован)
            address: Адрес (если None, будет сгенерирован)
            positioning: Позиционирование (если None, будет сгенерирован)

        Возвращает:
            QuestionnaireData: Структура с данными анкеты
        """
        questionnaire = QuestionnaireData(
            user_id=user_id,
            gender=gender or self.generator.generate_gender(),
            age=age or self.generator.generate_age(),
            address=address or self.generator.generate_address(),
            positioning=positioning or self.generator.generate_positioning(),
            questionnaire_type=QuestionnaireType.SHORT,
            created_at=datetime.now(),
            chat_id=chat_id,
        )

        logger.info(
            "Created short questionnaire for user %d in chat %d: %s",
            user_id,
            chat_id,
            questionnaire,
        )

        return questionnaire

    def create_full_questionnaire(
        self,
        user_id: int,
        chat_id: int,
        gender: Optional[str] = None,
        age: Optional[str] = None,
        address: Optional[str] = None,
        positioning: Optional[str] = None,
    ) -> QuestionnaireData:
        """Создать полную анкету (расширенная версия).

        Параметры:
            user_id: ID пользователя Telegram
            chat_id: ID чата
            gender: Пол (если None, будет сгенерирован)
            age: Возраст (если None, будет сгенерирован)
            address: Адрес (если None, будет сгенерирован)
            positioning: Позиционирование (если None, будет сгенерирован)

        Возвращает:
            QuestionnaireData: Структура с данными анкеты
        """
        questionnaire = QuestionnaireData(
            user_id=user_id,
            gender=gender or self.generator.generate_gender(),
            age=age or self.generator.generate_age(),
            address=address or self.generator.generate_address(),
            positioning=positioning or self.generator.generate_positioning(),
            questionnaire_type=QuestionnaireType.FULL,
            created_at=datetime.now(),
            chat_id=chat_id,
        )

        logger.info(
            "Created full questionnaire for user %d in chat %d: %s",
            user_id,
            chat_id,
            questionnaire,
        )

        return questionnaire

    async def save_questionnaire_text_directly(
        self,
        questionnaire_text: str,
        user_id: Optional[int] = None,
        bot: Optional[Bot] = None,
        chat_id: Optional[int] = None,
        thread_id: Optional[int] = None,
    ) -> bool:
        """Сохранить заранее сформированный текст анкеты в локальное хранилище.

        Метод предназначен для сценария, когда текст анкеты формирует внешняя
        часть проекта, а не сам Telegram-бот. Это удобно для проверки
        цифрового слепка автора и других компонентов, работающих с заранее
        подготовленными данными.
        """
        if not questionnaire_text or not questionnaire_text.strip():
            logger.warning("Attempt to save empty questionnaire text")
            return False

        question_id = str(uuid.uuid4())
        payload = {
            "id": question_id,
            "text": questionnaire_text,
            "user_id": user_id,
            "created_at": datetime.now(),
            "saved_to_telegram": False,
        }

        self._manual_questionnaire_storage[question_id] = payload
        logger.info(
            "Saved questionnaire text manually (id=%s, user_id=%s)",
            question_id,
            user_id,
        )

        if bot is not None and chat_id is not None:
            try:
                message_kwargs = {
                    "chat_id": chat_id,
                    "text": questionnaire_text,
                    "parse_mode": "HTML",
                }
                if thread_id is not None:
                    message_kwargs["message_thread_id"] = thread_id

                message = await bot.send_message(**message_kwargs)
                payload["saved_to_telegram"] = True
                payload["telegram_chat_id"] = chat_id
                payload["telegram_message_id"] = message.message_id
                self._manual_questionnaire_storage[question_id] = payload
                logger.info(
                    "Questionnaire text saved to Telegram chat %s (message_id=%s)",
                    chat_id,
                    message.message_id,
                )
            except Exception:
                logger.exception(
                    "Failed to save questionnaire text to Telegram chat %s",
                    chat_id,
                )
                return False

        return True

    def get_manual_questionnaire(self, question_id: str) -> Optional[dict]:
        """Получить сохранённую анкету из временного in-memory хранилища."""
        return self._manual_questionnaire_storage.get(question_id)

    def list_manual_questionnaires(self) -> dict[str, dict]:
        """Вернуть все сохранённые вручную анкеты (для отладки и тестов)."""
        return dict(self._manual_questionnaire_storage)

    def clear_manual_questionnaires(self) -> None:
        """Очистить заглушечное хранилище вручную созданных анкет."""
        self._manual_questionnaire_storage.clear()
        logger.info("Cleared manual questionnaire storage")

    def format_questionnaire_text(self, questionnaire: QuestionnaireData) -> str:
        """Отформатировать анкету в текст для сохранения в чат.

        Параметры:
            questionnaire: Данные анкеты

        Возвращает:
            str: Отформатированный текст анкеты с информацией о пользователе
        """
        questionnaire_type = "Полная" if questionnaire.questionnaire_type == QuestionnaireType.FULL else "Сокращённая"

        text = f"""<b>Анкета ({questionnaire_type})</b>
 <b>Пол:</b> {questionnaire.gender}
 <b>Возраст:</b> {questionnaire.age}
 <b>Адрес:</b> {questionnaire.address}
 <b>Позиционирование:</b> {questionnaire.positioning}

 <i>Создана пользователем: {questionnaire.user_id}</i>
 <i>Время: {questionnaire.created_at.strftime('%Y-%m-%d %H:%M:%S')}</i>"""

        return text

    def extract_user_id_from_text(self, text: str) -> Optional[int]:
        """Извлечь user_id из отформатированного текста анкеты.

        Параметры:
            text: Текст анкеты

        Возвращает:
            int: ID пользователя или None, если не найден
        """
        import re
        match = re.search(r"Создана пользователем: (\d+)", text)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                logger.warning("Failed to extract user_id from text: %s", text[:100])
                return None
        return None


# Глобальный экземпляр сервиса
questionnaire_service = QuestionnaireService()
