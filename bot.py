import json
import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
import html
import csv
from aiogram.types import FSInputFile

class ProductSearcher:
    # Класс для поиска товаров по базе данных
    def __init__(self, data_file):
        self.data_file = data_file
        self.data = self.load_data()  # Загружаем данные из файла при инициализации

    def load_data(self):
        # Проверяем, существует ли файл с подготовленными данными
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f: # Загрузка данных из файла JSON
                data = json.load(f)
            return data
        else:
            # Если файл не найден, выбрасывается исключение
            raise FileNotFoundError(f"Файл {self.data_file} не найден. Сначала запустите скрипт data_preparation.py для подготовки данных.")

    def search_products(self, query):
        # Поиск товаров по имени или артикулу
        query_normalized = query.lower().strip() # Нормализация запроса

        # Фильтрация данных по названию или артикулу
        results = [
            item for item in self.data
            if
            query_normalized in item.get('Название', '').lower() or query_normalized in item.get('Артикул', '').lower()
        ]

        return results # Возвращаем список найденных товаров


class Form(StatesGroup):
    # Класс для управления состояниями FSM
    waiting_for_product_name = State() # Состояние ожидания ввода названия товара


class TelegramBot:
    # Класс для создания и управления Telegram-ботом
    def __init__(self, token, product_searcher):
        self.token = token
        self.product_searcher = product_searcher
        self.bot = Bot(token=self.token)
        self.storage = MemoryStorage() # Временное хранилище для состояний пользователей
        self.dp = Dispatcher(storage=self.storage)
        self.keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='Найти товары')],
            ],
            resize_keyboard=True # Автоматически подгоняет размер клавиатуры
        )
        self.register_handlers() # Регистрация обработчиков

    def register_handlers(self):
        # Регистрация обработчиков команд и сообщений
        self.dp.message.register(self.cmd_start, Command(commands=['start']))
        self.dp.message.register(self.process_find_products, F.text == 'Найти товары')
        self.dp.message.register(self.process_product_name, Form.waiting_for_product_name)

    async def cmd_start(self, message: Message):
        # Обработчик команды /start. Приветствует пользователя и показывает основное меню
        await message.answer("Привет! Я бот для поиска товаров. Нажмите кнопку 'Найти товары', чтобы начать поиск.",
                             reply_markup=self.keyboard, parse_mode='HTML')

    async def process_find_products(self, message: Message, state: FSMContext):
        # Обработчик начала поиска товаров. Переводит пользователя в состояние ожидания ввода
        await message.answer("Введите название товара для поиска:", parse_mode='HTML')
        await state.set_state(Form.waiting_for_product_name)

    async def process_product_name(self, message: types.Message, state: FSMContext):
        # Обработчик поиска товаров по введенному пользователем запросу
        user_query = message.text
        results = self.product_searcher.search_products(user_query) # Выполнение поиска

        if not results:
            # Если результаты не найдены, сообщаем пользователю
            await message.answer("Товары не найдены.", reply_markup=self.keyboard, parse_mode='HTML')
            await state.clear() #Очищаем состояние
            return

        # Сообщаем количество найденных товаров
        total_count = len(results)
        await message.answer(f"Найдено {total_count} товаров:", parse_mode='HTML')

        # Разбиваем результаты на части, чтобы не превысить лимит Telegram в 4096 символов
        response = ""
        for index, item in enumerate(results, start=1):
            # Форматируем информацию о каждом товаре
            product_info = (
                f"\n\n<b>{index}. Название:</b> {html.escape(item.get('Название', 'Нет данных'))}"
                f"\n<b>Описание:</b> {html.escape(item.get('Описание', 'Нет данных'))}"
                f"\n<b>Артикул:</b> {html.escape(item.get('Артикул', 'Нет данных'))}"
                f"\n<b>Поставщик:</b> {html.escape(item.get('Поставщик', 'Нет данных'))}"
                f"\n<b>Ссылка:</b> {html.escape(item.get('Ссылка', 'Нет данных'))}"
                f"\n<b>Цена Each:</b> {html.escape(item.get('Цена Each', 'Нет данных'))}"
                f"\n<b>Цена Case:</b> {html.escape(item.get('Цена Case', 'Нет данных'))}"
            )

            # Проверка, не превысит ли добавление нового товара лимит символов
            if len(response) + len(product_info) > 4000:
                #Отправляем текущее накопленное сообщение
                await message.answer(response, parse_mode='HTML')
                # Начинаем новое сообщение с текущим товаром
                response = product_info
            else:
                # Добавляем информацию о товаре к текущему сообщению
                response += product_info

        # Отправляем оставшуюся часть сообщения, если она есть
        if response:
            await message.answer(response, reply_markup=self.keyboard, parse_mode='HTML')

        # Генерируем имя файла CSV на основе пользовательского ввода
        sanitized_user_query = "".join(c for c in user_query if c.isalnum() or c in (" ", "_")).rstrip()
        file_name = f"results {sanitized_user_query}.csv"

        # Создаем временный CSV-файл
        with open(file_name, mode='w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(
                ['Название', 'Описание', 'Артикул', 'Поставщик', 'Ссылка', 'Цена Each', 'Цена Case'])  # Заголовки
            for item in results:
                writer.writerow([
                    item.get('Название', 'Нет данных'),
                    item.get('Описание', 'Нет данных'),
                    item.get('Артикул', 'Нет данных'),
                    item.get('Поставщик', 'Нет данных'),
                    item.get('Ссылка', 'Нет данных'),
                    item.get('Цена Each', 'Нет данных'),
                    item.get('Цена Case', 'Нет данных')
                ])

        # Отправляем CSV-файл пользователю
        file_to_send = FSInputFile(file_name)
        await message.answer_document(
            file_to_send,
            caption=f"Результаты поиска в формате CSV для запроса: {user_query}"
        )

        # Удаляем временный файл после отправки
        os.remove(file_name)

        # Очищаем состояние
        await state.clear()

    async def start(self):
        # Запускаем бота и удаляем предыдущие обновления
        await self.bot.delete_webhook(drop_pending_updates=True)
        print("Бот запущен")
        await self.dp.start_polling(self.bot)


if __name__ == '__main__':
    # Путь к файлу с подготовленными данными
    data_file = os.path.join('scraper VWR all info', 'prepared_data.json')

    # Проверка наличия директории
    if not os.path.exists('scraper VWR all info'):
        os.makedirs('scraper VWR all info')

    # Инициализация класса поиска товаров
    searcher = ProductSearcher(data_file)


    # Загрузка токена из файла token.txt
    with open('token.txt', 'r') as token_file:
        TOKEN = token_file.read().strip()

    # Инициализация и запуск Telegram-бота
    bot = TelegramBot(TOKEN, searcher)

    # Запуск бота
    asyncio.run(bot.start())