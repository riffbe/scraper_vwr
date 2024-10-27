import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch, mock_open, MagicMock
import json
import os
import csv
import tempfile

# Импортируем функции для тестирования
from scraper.main import (
    get_quantity,
    get_prices,
    get_info,
    combine_json_csv,
    prepare_data
)

@pytest.fixture
def sample_html_page():
    """
    Фикстура, предоставляющая пример HTML-контента для тестирования парсинга.
    """
    html_content = '''
    <html>
    <body>
        <p class="pull-left">25 Items</p>
        <div class="search-item row">
            <h2 class="search-item__title">Product Title</h2>
            <div class="search-item__info">Description: Sample description</div>
            <div class="search-item__info">Catalog Number: ABC123</div>
            <div class="search-item__info">Supplier: Sample Supplier</div>
            <a href="/product/link">Product Link</a>
            <select class="uomSelect">
                <option>Each - $10.00</option>
                <option>Case - $90.00</option>
            </select>
        </div>
    </body>
    </html>
    '''
    return html_content

def test_get_quantity(sample_html_page):
    """
    Тестируем функцию get_quantity на корректность извлечения количества товаров.
    """
    # Задаем тестовые параметры
    directory_path = "test_directory"
    category_name = "Test Category"
    product_names = ["Test Product"]

    # Мокаем функции os.listdir, os.path.exists и open
    with patch('os.listdir', return_value=['page1.html']), \
         patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=sample_html_page)):
        # Вызываем функцию и проверяем результат
        num_of_products = get_quantity(directory_path, category_name, product_names)
        assert num_of_products == [25], "Количество товаров должно быть 25"

def test_get_prices(sample_html_page):
    """
    Тестируем функцию get_prices на корректность извлечения и сохранения цен.
    """
    # Мокаем необходимые функции и методы
    with patch('os.listdir', return_value=['page1.html']), \
         patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=sample_html_page)), \
         patch('os.makedirs'), \
         patch('json.dump') as mock_json_dump:
        # Параметры для функции
        num_of_product = [1]
        pagination_quantity = 16
        directory_path_for_price = "test_price_directory"
        category_name = "Test Category"
        product_names = ["Test Product"]

        # Вызываем функцию
        get_prices(num_of_product, pagination_quantity, directory_path_for_price, category_name, product_names)
        # Проверяем, что данные были сохранены
        assert mock_json_dump.called, "Должен быть вызов json.dump для сохранения данных"

def test_get_info(sample_html_page):
    """
    Тестируе функцию get_info на корректность извлечения информации о продуктах.
    """
    # Мокаем необходимые функции и методы
    with patch('os.listdir', return_value=['page1.html']), \
         patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=sample_html_page)), \
         patch('os.makedirs'), \
         patch('json.load', return_value={
             "Test Product": {
                 "ABC123": {
                     "Each": "$10.00",
                     "Case": "$90.00"
                 }
             }
         }), \
         patch('json.dump') as mock_json_dump, \
         patch('csv.DictWriter') as mock_csv_writer:
        # Настраиваем экземпляр csv.DictWriter
        instance = mock_csv_writer.return_value
        instance.writeheader = MagicMock()
        instance.writerow = MagicMock()
        instance.writerows = MagicMock()

        # Параметры для функции
        num_of_product = [1]
        pagination_quantity = 16
        directory_path = "test_directory"
        directory_path_for_info = "test_info_directory"
        directory_path_for_price = "test_price_directory"
        category_name = "Test Category"
        product_names = ["Test Product"]

        # Вызываем функцию
        get_info(num_of_product, pagination_quantity, directory_path, directory_path_for_info, directory_path_for_price, category_name, product_names)
        # Проверяем, что данные были сохранены
        assert mock_json_dump.called, "Должен быть вызов json.dump для сохранения данных"
        # Проверяем, что данные были записаны в CSV
        assert instance.writerow.called or instance.writerows.called, "Должен быть вызов csv.DictWriter для записи CSV"

def test_combine_json_csv():
    """
    Тестируем функцию combine_json_csv на корректность объединения JSON и CSV файлов.
    """
    # Создаем временную директорию для теста
    with tempfile.TemporaryDirectory() as tmpdir:
        # Создаем поддиректорию и тестовые файлы
        info_dir = os.path.join(tmpdir, "scraper VWR data base")
        os.makedirs(info_dir)
        sample_data = [
            {"Название": "Product A", "Артикул": "A123"},
            {"Название": "Product B", "Артикул": "B456"}
        ]
        # Сохраняем пример JSON файл
        json_file_path = os.path.join(info_dir, "category_info.json")
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=4)
        # Сохраняем пример CSV файл
        csv_file_path = os.path.join(info_dir, "category_info.csv")
        with open(csv_file_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["Название", "Артикул"], delimiter=';')
            writer.writeheader()
            writer.writerows(sample_data)
        # Создаем выходную директорию
        output_directory = os.path.join(tmpdir, "output")
        os.makedirs(output_directory)
        # Вызываем функцию
        combine_json_csv(info_dir, output_directory)
        # Проверяем, что объединенные файлы созданы
        combined_json_file = os.path.join(output_directory, 'combined_data.json')
        combined_csv_file = os.path.join(output_directory, 'combined_data.csv')
        assert os.path.exists(combined_json_file), "Объединенный JSON файл должен быть создан"
        assert os.path.exists(combined_csv_file), "Объединенный CSV файл должен быть создан"

def test_prepare_data():
    """
    Тестируем функцию prepare_data на корректность нормализации и сохранения данных.
    """
    # Создаем временную директорию и входной файл
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = 'combined_data.json'
        input_file_path = os.path.join(tmpdir, input_file)
        data = [
            {"Название": " Product A ", "Артикул": "A123"},
            {"Название": "product B", "Артикул": "B456"}
        ]
        with open(input_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        # Вызываем функцию
        prepare_data(input_file, tmpdir)
        # Проверяем, что подготовленные файлы созданы
        output_json_file = os.path.join(tmpdir, 'prepared_data.json')
        output_csv_file = os.path.join(tmpdir, 'prepared_data.csv')
        assert os.path.exists(output_json_file), "Подготовленный JSON файл должен быть создан"
        assert os.path.exists(output_csv_file), "Подготовленный CSV файл должен быть создан"
        # Проверяем содержимое подготовленного файла
        with open(output_json_file, 'r', encoding='utf-8') as f:
            prepared_data = json.load(f)
            # Проверяем, что названия нормализованы
            assert prepared_data[0]['НормализованноеНазвание'] == 'product a', "Название должно быть нормализовано"
