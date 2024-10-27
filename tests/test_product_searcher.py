import os
import json
import pytest
from bot.tg_bot import ProductSearcher

@pytest.fixture
def sample_data(tmpdir):
    """
    Фикстура для создания примера данных для тестирования класса ProductSearcher.
    """
    # Пример данных для тестирования
    data = [
        {
            "Название": "Тестовый продукт 1",
            "Описание": "Описание 1",
            "Артикул": "TP1",
            "Поставщик": "Поставщик A",
            "Ссылка": "http://example.com/1",
            "Цена Each": "10",
            "Цена Case": "100"
        },
        {
            "Название": "Тестовый продукт 2",
            "Описание": "Описание 2",
            "Артикул": "TP2",
            "Поставщик": "Поставщик B",
            "Ссылка": "http://example.com/2",
            "Цена Each": "20",
            "Цена Case": "200"
        }
    ]
    # Сохраняем данные во временный файл
    data_file = tmpdir.join("prepared_data.json")
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    # Возвращаем путь к файлу с данными
    return str(data_file)

def test_load_data(sample_data):
    """
    Тестируем загрузку данных в класс ProductSearcher.
    """
    searcher = ProductSearcher(sample_data)
    # Проверяем, что данные загружены корректно
    assert len(searcher.data) == 2

def test_search_by_name(sample_data):
    """
    Тестируем поиск продукта по названию.
    """
    searcher = ProductSearcher(sample_data)
    results = searcher.search_products("Тестовый продукт 1")
    # Проверяем, что найден один продукт с указанным артикулом
    assert len(results) == 1
    assert results[0]["Артикул"] == "TP1"

def test_search_by_sku(sample_data):
    """
    Тестируем поиск продукта по артикулу (SKU).
    """
    searcher = ProductSearcher(sample_data)
    results = searcher.search_products("TP2")
    # Проверяем, что найден один продукт с указанным названием
    assert len(results) == 1
    assert results[0]["Название"] == "Тестовый продукт 2"

def test_search_no_results(sample_data):
    """
    Тестируем поведение при отсутствии результатов поиска.
    """
    searcher = ProductSearcher(sample_data)
    results = searcher.search_products("Несуществующий продукт")
    # Проверяем, что результаты пусты
    assert len(results) == 0

def test_file_not_found():
    """
    Тестируем обработку ошибки при отсутствии файла с данными.
    """
    with pytest.raises(FileNotFoundError):
        ProductSearcher("non_existent_file.json")
