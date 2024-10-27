import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot, Dispatcher
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from bot.tg_bot import TelegramBot, Form, ProductSearcher

@pytest.fixture
def bot_instance():
    """
    Фикстура для создания экземпляра TelegramBot с замоканными зависимостями.
    """
    # Используем тестовый токен
    token = "TEST_TOKEN"
    # Создаем замоканный экземпляр ProductSearcher
    searcher = MagicMock(spec=ProductSearcher)
    # Создаем замоканный экземпляр Bot
    mock_bot = AsyncMock(spec=Bot)
    # Создаем замоканный экземпляр Dispatcher
    mock_dispatcher = MagicMock(spec=Dispatcher)

    # Добавляем атрибут 'message' с необходимыми методами в mock_dispatcher
    mock_dispatcher.message = MagicMock()
    mock_dispatcher.message.register = MagicMock()

    # Инициализируем TelegramBot с замоканными bot и dispatcher
    bot = TelegramBot(token, searcher, bot_instance=mock_bot, dispatcher_instance=mock_dispatcher)
    return bot

@pytest.fixture
def message():
    """
    Фикстура для создания замоканного объекта Message.
    """
    # Создаем замоканный объект Message
    msg = MagicMock(spec=Message)
    # Мокаем атрибуты chat и chat.id
    msg.chat = MagicMock()
    msg.chat.id = 12345
    # Задаем пустой текст сообщения
    msg.text = ""
    # Мокаем методы answer и answer_document
    msg.answer = AsyncMock()
    msg.answer_document = AsyncMock()
    return msg

@pytest.fixture
def state():
    """
    Фикстура для создания замоканного объекта FSMContext.
    """
    # Создаем замоканный объект FSMContext
    state = AsyncMock(spec=FSMContext)
    # Мокаем методы set_state и clear
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state

@pytest.mark.asyncio
async def test_cmd_start(bot_instance, message):
    """
    Тестируем обработчик команды /start.
    """
    # Вызываем обработчик команды /start
    await bot_instance.cmd_start(message)
    # Проверяем, что был вызван метод answer
    message.answer.assert_called_once()
    # Проверяем, что ответ содержит приветственное сообщение
    assert "Привет! Я бот для поиска товаров." in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_process_find_products(bot_instance, message, state):
    """
    Тестируем обработчик начала поиска товаров.
    """
    # Вызываем обработчик процесса поиска товаров
    await bot_instance.process_find_products(message, state)
    # Проверяем, что был отправлен запрос на ввод названия товара
    message.answer.assert_called_once_with("Введите название товара для поиска:", parse_mode='HTML')
    # Проверяем, что состояние было установлено в ожидание ввода названия товара
    state.set_state.assert_called_once_with(Form.waiting_for_product_name)

@pytest.mark.asyncio
async def test_process_product_name_no_results(bot_instance, message, state):
    """
    Тестируем обработчик ввода названия товара, когда результатов нет.
    """
    # Мокаем метод search_products, чтобы он возвращал пустой список
    bot_instance.product_searcher.search_products.return_value = []
    # Задаем текст сообщения с несуществующим товаром
    message.text = "Несуществующий товар"

    # Вызываем обработчик процесса получения товара по названию
    await bot_instance.process_product_name(message, state)

    # Проверяем, что было отправлено сообщение о том, что товары не найдены
    message.answer.assert_called_with("Товары не найдены.", reply_markup=bot_instance.keyboard, parse_mode='HTML')
    # Проверяем, что состояние было очищено
    state.clear.assert_called_once()

@pytest.mark.asyncio
async def test_process_product_name_with_results(bot_instance, message, state):
    """
    Тестируем обработчик ввода названия товара, когда результаты найдены.
    """
    # Мокаем метод search_products, чтобы он возвращал список товаров
    bot_instance.product_searcher.search_products.return_value = [
        {
            "Название": "Тестовый продукт 1",
            "Описание": "Описание 1",
            "Артикул": "TP1",
            "Поставщик": "Поставщик A",
            "Ссылка": "http://example.com/1",
            "Цена Each": "10",
            "Цена Case": "100"
        }
    ]
    # Задаем текст сообщения с названием товара
    message.text = "Тестовый продукт 1"

    # Мокаем os.remove, чтобы предотвратить удаление реальных файлов
    with patch('os.remove') as mock_remove:
        # Мокаем FSInputFile, чтобы предотвратить реальные файловые операции
        with patch('aiogram.types.FSInputFile', return_value=MagicMock(spec=FSInputFile)):
            # Вызываем обработчик процесса получения товара по названию
            await bot_instance.process_product_name(message, state)

    # Проверяем, что были отправлены необходимые сообщения
    assert message.answer.call_count >= 2  # Может быть больше из-за разбивки сообщений
    # Проверяем, что файл был отправлен
    message.answer_document.assert_called_once()
    # Проверяем, что состояние было очищено
    state.clear.assert_called_once()
