import time
from selenium import webdriver
from bs4 import BeautifulSoup
from math import ceil
import json
import csv
import os
"""
На сайте VWR подключена защита claudflare, нужно сначала запустить основной браузер и открыть порт,
с помощью данной команды в терминале "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\my-chrome-profile"
перейти на страницу - https://us.vwr.com/store/search?label=EMSURE&terms=EMSURE&view=list&pageNo=10 и пройти верификацию
дальше запускать код
"""
# "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\my-chrome-profile"

links = [
    # Solvents
    [
        "https://us.vwr.com/store/search?label=EMSURE&terms=EMSURE&view=list",  # EMSURE (ACS, ISO, Red. Ph Eur)
        "https://us.vwr.com/store/search?label=EMPARTA+ACS&terms=EMPARTA&view=list",  # EMPARTA (ACS)
        "https://us.vwr.com/store/search?label=HPLC+LiChroSolv&terms=LichroSolv&view=list",  # HPLC LiChroSolv
        "https://us.vwr.com/store/search?label=HPLC+OmniSolv&terms=OmniSolv+HPLC&view=list",  # HPLC OmniSolv
        "https://us.vwr.com/store/search?label=Dried+Solvents+SeccoSolv&terms=SeccoSolv&view=list",  # Dried Solvents: SeccoSolv
        "https://us.vwr.com/store/search?label=Dried+Solvents+DriSolv&terms=DriSolv&view=list",  # Dried Solvents: DriSolv
        "https://us.vwr.com/store/search?label=NMR+Spectroscopy&terms=MagniSolv&view=list",  # NMR Spectroscopy
        "https://us.vwr.com/store/search?label=Gas+Chromatography+SupraSolv&terms=SupraSolv&view=list",  # Gas Chromatography: SupraSolv
        "https://us.vwr.com/store/search?label=Gas+Chromatography+OmniSolv&terms=OmniSolv+for+GC&view=list",  # Gas Chromatography: OmniSolv
        "https://us.vwr.com/store/search?label=Spectroscopy&terms=Uvasol&view=list"  # Spectroscopy
    ],
    # Inorganic Reagents
    [
        "https://us.vwr.com/store/search?label=Acids&supplierName=MilliporeSigma&terms=Acid%20ACS&view=list",  # Acids
        "https://us.vwr.com/store/search?label=Caustics%20and%20Bases&supplierName=MilliporeSigma&terms=Caustic&view=list",  # Caustics and Bases
        "https://us.vwr.com/store/search?label=Salts&supplierName=MilliporeSigma&terms=Salt&view=list",  # Salts
        "https://us.vwr.com/store/search?label=Karl%20Fischer&supplierName=MilliporeSigma&terms=Karl%20Fischer&view=list",  # Karl Fischer
        "https://us.vwr.com/store/search?label=Certipur%20Standards%20and%20Reference%20Materials&pimId=3617136&terms=Certipur&view=list",  # Certipur Standards and Reference Materials
        "https://us.vwr.com/store/search?label=XRF%20Analysis&terms=Spectromelt&view=list",  # XRF Analysis
        "https://us.vwr.com/store/search?label=High%20Purity%20Acids%20Bases%20Salts&terms=Suprapur&view=list",  # High Purity Acids, Bases, Salts
        "https://us.vwr.com/store/search?label=Volumetric%20Solutions&terms=Titripur&view=list"  # Volumetric Solutions
    ],
    # Organic Synthesis Portfolio
    [
        "https://us.vwr.com/store/search?label=Msynth%20Plus&terms=Pharma%20Synthesis&view=list"  # Msynth Plus
    ],
    # Cleaning Lab Equipment
    [
        "https://us.vwr.com/store/search?label=Extran%20Cleaning%20Agents&supplierName=MilliporeSigma&terms=Extran&view=list"  # Extran Cleaning Agents
    ]
]

links_category_names = ["Solvents", "Inorganic Reagents", "Organic Synthesis Portfolio", "Cleaning Lab Equipment"] # Названия категорий, соответствующие списку ссылок

pagination_quantity = 16 # Количество товаров на одной странице

output_directory = 'scraper VWR all info' # Директория для сохранения объединенных данных

input_file = 'combined_data.json' # Имя входного файла для подготовки данных

# Названия каждой категории
links_products_names = [
    # Solvents
    [
        "EMSURE (ACS, ISO, Red. Ph Eur)",  # EMSURE (ACS, ISO, Red. Ph Eur)
        "EMPARTA (ACS)",  # EMPARTA (ACS)
        "HPLC LiChroSolv",  # HPLC LiChroSolv
        "HPLC OmniSolv",  # HPLC OmniSolv
        "Dried Solvents SeccoSolv",  # Dried Solvents: SeccoSolv
        "Dried Solvents DriSolv",  # Dried Solvents: DriSolv
        "NMR Spectroscopy",  # NMR Spectroscopy
        "Gas Chromatography SupraSolv",  # Gas Chromatography: SupraSolv
        "Gas Chromatography OmniSolv",  # Gas Chromatography: OmniSolv
        "Spectroscopy"  # Spectroscopy
    ],
    # Inorganic Reagents
    [
        "Acids",  # Acids
        "Caustics and Bases",  # Caustics and Bases
        "Salts",  # Salts
        "Karl Fischer",  # Karl Fischer
        "Certipur Standards and Reference Materials",  # Certipur Standards and Reference Materials
        "XRF Analysis",  # XRF Analysis
        "High Purity Acids, Bases, Salts",  # High Purity Acids, Bases, Salts
        "Volumetric Solutions"  # Volumetric Solutions
    ],
    # Organic Synthesis Portfolio
    [
        "Msynth Plus"  # Msynth Plus
    ],
    # Cleaning Lab Equipment
    [
        "Extran Cleaning Agents"
    ]
]

# Пути для сохранения данных
directory_path = "scraper VWR" # Html файлы
directory_path_for_price = "scraper VWR data base price" # Цены для товаров
directory_path_for_info = "scraper VWR data base" # Полная информация о товарах

# Функция для загрузки первой страницы для каждой категории продуктов для парсинга количества товаров
def get_first_page(base_urls, directory_path, category_name, product_names):
    try:
        options = webdriver.ChromeOptions()
        options.debugger_address = "127.0.0.1:9222"  # Подключаемся к открытому браузеру
        driver = webdriver.Chrome(options=options)
        for j in range(len(product_names)):
            current_url = base_urls[j]
            driver.get(current_url)
            time.sleep(1) # Ждем, чтобы страница полностью загрузилась
            category_dir = os.path.join(directory_path, category_name)
            if not os.path.exists(category_dir):
                os.makedirs(category_dir)
            # Получаем исходный код страницы
            page_source = driver.page_source
            # Сохраняем исходный код страницы в файл
            with open(f"{category_dir}/{product_names[j]}_page1.html", "w", encoding="utf-8") as file:
                file.write(page_source)
            print(f"Сохранена страница {product_names[j]} - page 1")
        print("Все страницы сохранены")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


# Получение количества товаров по категориям
def get_quantity(directory_path, category_name, product_names):
    num_of_product = []  # Список для хранения количества товаров
    category_dir = os.path.join(directory_path, category_name)
    for j in range(len(product_names)):
        try:
            with open(f"{category_dir}/{product_names[j]}_page1.html", "r", encoding="utf-8") as file:
                page = file.read()

            soup = BeautifulSoup(page, "lxml")

            # Поиск количества продуктов
            quantity_elem = soup.find("p", class_="pull-left")
            if not quantity_elem:
                print(f"Страница {product_names[j]}: не найден элемент <p> с классом 'pull-left'.")
                num_of_product.append(0)
                continue

            cleaned_item = quantity_elem.text.split(' ')[0]  # Извлекаем только первую часть текста
            num_of_product.append(int(cleaned_item.strip()))  # Сохраняем очищенный текст

        except FileNotFoundError:
            print(f"Файл {product_names[j]}_page1.html не найден в категории {category_name}.")
            num_of_product.append(0)
            continue

    print(f"Данные количества продуктов для категории {category_name} успешно сохранены")
    print(num_of_product)
    return num_of_product  # Возвращаем список с данными


# Функция для загрузки всех страниц товаров
def get_pages(base_urls, directory_path, category_name, product_names, num_of_product):
    try:
        options = webdriver.ChromeOptions()
        options.debugger_address = "127.0.0.1:9222"  # Подключаемся к открытому браузеру
        driver = webdriver.Chrome(options=options)

        category_dir = os.path.join(directory_path, category_name)
        for j in range(len(product_names)):
            total_pages = ceil(num_of_product[j] / pagination_quantity)
            for page_number in range(1, total_pages + 1):
                current_url = f"{base_urls[j]}&pageNo={page_number}" if page_number > 1 else base_urls[j]
                driver.get(current_url)
                time.sleep(1) # Ждем, чтобы страница полностью загрузилась
                page_source = driver.page_source
                # Сохраняем исходный код страницы в файл
                with open(f"{category_dir}/{product_names[j]}_page{page_number}.html", "w", encoding="utf-8") as file:
                    file.write(page_source)
                print(f"Сохранена страница {product_names[j]} - page {page_number}")
        print("Все страницы сохранены")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


# Функция для извлечения и сохранения информации о ценах
def get_prices(num_of_product, pagination_quantity, directory_path_for_price, category_name, product_names):
    all_prices = {}  # Словарь для хранения всех цен
    category_dir = os.path.join(directory_path, category_name)
    for j in range(len(product_names)):
        product_prices = {}
        total_pages = ceil(num_of_product[j] / pagination_quantity)
        for page_number in range(1, total_pages + 1):
            file_path = f"{category_dir}/{product_names[j]}_page{page_number}.html"
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    page = file.read()
                soup = BeautifulSoup(page, "lxml")
                # Ищем все элементы div с классом "search-item row"
                search_items = soup.find_all("div", class_="search-item row")
                if not search_items:
                    print(f"Страница {product_names[j]} page {page_number}: не найдены элементы <div> с классом 'search-item row'.")
                    continue
                # Извлекаем цены для каждого элемента
                for item in search_items:
                    # Ищем артикул
                    catalog_number = None
                    info_blocks = item.find_all("div", class_="search-item__info")
                    for block in info_blocks:
                        if "Catalog Number:" in block.text:
                            catalog_number = block.text.split("Catalog Number:")[-1].strip()
                            break
                    if not catalog_number:
                        print(f"Страница {product_names[j]} page {page_number}: не найден каталожный номер.")
                        continue
                    # Ищем цены
                    select_element = item.find("select", class_="uomSelect")
                    if not select_element:
                        print(f"Страница {product_names[j]} page {page_number}: не найден элемент <select> с классом 'uomSelect' для товара {catalog_number}.")
                        continue
                    # Извлекаем все <option> внутри <select> и записываем цены
                    prices = {}
                    for option in select_element.find_all("option"):
                        option_text = option.text.strip()
                        if "Each" in option_text:
                            prices["Each"] = option_text.split("-")[-1].strip()
                        elif "Case" in option_text:
                            prices["Case"] = option_text.split("-")[-1].strip()
                    # Сохраняем найденные цены для текущего артикула товара
                    if prices:
                        product_prices[catalog_number] = prices
                    else:
                        print(f"Страница {product_names[j]} page {page_number}: не найдены цены для товара {catalog_number}.")
            except FileNotFoundError:
                print(f"Файл {file_path} не найден.")
            except Exception as e:
                print(f"Ошибка при обработке страницы {product_names[j]} page {page_number}: {e}")
        # Сохраняем цены для продукта
        all_prices[product_names[j]] = product_prices
    # Сохранение всех данных в JSON файл
    output_dir = os.path.join(directory_path_for_price, category_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_file = os.path.join(output_dir, f"{category_name}_prices.json")
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(all_prices, json_file, ensure_ascii=False, indent=4)
    print(f"Все данные сохранены в файле {output_file}")


# Функция для получения полной информации о товарах
def get_info(num_of_product, pagination_quantity, directory_path, directory_path_for_info, directory_path_for_price, category_name, product_names):
    # Загрузка цен из файла
    prices_file = os.path.join(directory_path_for_price, category_name, f"{category_name}_prices.json")
    with open(prices_file, "r", encoding="utf-8") as price_file:
        price_data = json.load(price_file)

    all_products = []  # Список для хранения всех товаров
    category_dir = os.path.join(directory_path, category_name)
    for j in range(len(product_names)):
        total_pages = ceil(num_of_product[j] / pagination_quantity)
        for page_number in range(1, total_pages + 1):
            file_path = f"{category_dir}/{product_names[j]}_page{page_number}.html"
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    page = file.read()
                soup = BeautifulSoup(page, "lxml")
                # Поиск всех товаров на странице
                items = soup.find_all("div", class_="search-item row")
                if not items:
                    print(f"Страница {product_names[j]} page {page_number}: не найдены элементы <div> с классом 'search-item row'.")
                    continue
                # Обработка каждого товара
                for item in items:
                    # Поиск названия товара
                    title_elem = item.find("h2", class_="search-item__title")
                    title = title_elem.get_text(strip=True) if title_elem else "Название не найдено"

                    # Поиск описания
                    description = "Описание не найдено"
                    for info_elem in item.find_all("div", class_="search-item__info"):
                        if "Description:" in info_elem.get_text():
                            description = info_elem.get_text(strip=True).split("Description:")[-1]
                            break

                    # Поиск артикула
                    catalog_number = "Артикул не найден"
                    for info_elem in item.find_all("div", class_="search-item__info"):
                        if "Catalog Number:" in info_elem.get_text():
                            catalog_number = info_elem.get_text(strip=True).split("Catalog Number:")[-1]
                            break

                    # Поиск поставщика
                    supplier = "Поставщик не найден"
                    for info_elem in item.find_all("div", class_="search-item__info"):
                        if "Supplier:" in info_elem.get_text():
                            supplier = info_elem.get_text(strip=True).split("Supplier:")[-1]
                            break

                    # Поиск ссылки на товар
                    link_elem = item.find("a", href=True)
                    link = f"https://us.vwr.com{link_elem['href']}" if link_elem else "Ссылка не найдена"

                    # Поиск цен
                    prices = price_data.get(product_names[j], {}).get(catalog_number, {})
                    each_price = prices.get("Each", "Цена для Each не найдена")
                    case_price = prices.get("Case", "Цена для Case не найдена")

                    # Добавление информации о товаре в список
                    product_info = {
                        "Название": title,
                        "Описание": description,
                        "Артикул": catalog_number,
                        "Поставщик": supplier,
                        "Ссылка": link,
                        "Цена Each": each_price,
                        "Цена Case": case_price
                    }
                    all_products.append(product_info)
            except FileNotFoundError:
                print(f"Файл {file_path} не найден.")
            except Exception as e:
                print(f"Ошибка при обработке страницы {product_names[j]} page {page_number}: {e}")

    output_dir = os.path.join(directory_path_for_info, category_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # Сохранение данных в JSON-файл
    json_output_file = os.path.join(output_dir, f"{category_name}_info.json")
    with open(json_output_file, "w", encoding="utf-8") as json_file:
        json.dump(all_products, json_file, ensure_ascii=False, indent=4)
    # Сохранение данных в CSV-файл
    csv_output_file = os.path.join(output_dir, f"{category_name}_info.csv")
    with open(csv_output_file, "w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["Название", "Описание", "Артикул", "Поставщик", "Ссылка", "Цена Each", "Цена Case"], delimiter=';')
        writer.writeheader()
        writer.writerows(all_products)
    print(f"Данные успешно сохранены в файлы {json_output_file} и {csv_output_file}")


# Функция для объединения данных из всех категорий
def combine_json_csv(directory_path_for_info, output_directory):
    # Создание выходной директории, если она не существует
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    combined_json_data = []
    combined_csv_data = []
    csv_headers = None

    # Обход всех поддиректорий и файлов в исходной директории
    for root, dirs, files in os.walk(directory_path_for_info):
        for file in files:
            # Обработка JSON-файлов
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            combined_json_data.extend(data)
                        else:
                            combined_json_data.append(data)
                except Exception as e:
                    print(f"Ошибка при чтении JSON файла {file_path}: {e}")

            # Обработка CSV-файлов
            elif file.endswith('.csv'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
                        reader = csv.DictReader(f, delimiter=';')
                        if csv_headers is None:
                            csv_headers = reader.fieldnames
                        for row in reader:
                            combined_csv_data.append(row)
                except Exception as e:
                    print(f"Ошибка при чтении CSV файла {file_path}: {e}")

    # Сохранение объединенных данных JSON
    combined_json_file = os.path.join(output_directory, 'combined_data.json')
    try:
        with open(combined_json_file, 'w', encoding='utf-8') as f:
            json.dump(combined_json_data, f, ensure_ascii=False, indent=4)
        print(f"Объединенные данные JSON сохранены в {combined_json_file}")
    except Exception as e:
        print(f"Ошибка при сохранении объединенного JSON файла: {e}")

    # Сохранение объединенных данных CSV
    combined_csv_file = os.path.join(output_directory, 'combined_data.csv')
    try:
        if csv_headers:
            with open(combined_csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_headers, delimiter=';')
                writer.writeheader()
                writer.writerows(combined_csv_data)
            print(f"Объединенные данные CSV сохранены в {combined_csv_file}")
        else:
            print("Заголовки CSV не найдены; CSV файл не создан.")
    except Exception as e:
        print(f"Ошибка при сохранении объединенного CSV файла: {e}")


# Функция для подготовки данных (нормализация и сортировка)
def prepare_data(input_file, output_directory):
    # Проверка существования выходной директории, если нет - создаем ее
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Полный путь к входному файлу
    input_file_path = os.path.join(output_directory, input_file)

    # Проверка существования входного файла, если нет - создаем его
    if not os.path.exists(input_file_path):
        with open(input_file_path, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)  # Создаем пустой файл с пустым списком

    # Загрузка данных
    with open(input_file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Ошибка при чтении JSON файла: {e}")
            data = []

    # Проверка, есть ли данные для обработки
    if not data:
        print("Данные пусты. Нечего обрабатывать.")
        return

    # Нормализация названий
    for item in data:
        full_name = item.get('Название', '').strip()
        normalized_name = full_name.lower()
        item['НормализованноеНазвание'] = normalized_name

    # Сортировка данных по нормализованному названию
    data.sort(key=lambda x: x['НормализованноеНазвание'])

    # Формирование путей к файлам
    output_json_file = os.path.join(output_directory, 'prepared_data.json')
    output_csv_file = os.path.join(output_directory, 'prepared_data.csv')

    # Сохранение подготовленных данных в новый JSON файл
    with open(output_json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Данные подготовлены и сохранены в {output_json_file}")

    # Сохранение данных в CSV файл
    try:
        # Определяем заголовки для CSV на основе ключей словаря
        if data:
            csv_headers = data[0].keys()  # Используем ключи первого элемента в качестве заголовков
            with open(output_csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_headers, delimiter=';')
                writer.writeheader()
                writer.writerows(data)
            print(f"Данные также сохранены в {output_csv_file}")
        else:
            print("Данные пусты. CSV файл не создан.")
    except Exception as e:
        print(f"Ошибка при сохранении данных в CSV файл: {e}")

    return data



def main(links_category, directory_path, directory_path_for_price, directory_path_for_info, category_name, product_names, pagination_quantity):
    get_first_page(links_category, directory_path, category_name, product_names)
    num_of_products = get_quantity(directory_path, category_name, product_names)
    get_pages(links_category, directory_path, category_name, product_names, num_of_products)
    get_prices(num_of_products, pagination_quantity, directory_path_for_price, category_name, product_names)
    get_info(num_of_products, pagination_quantity, directory_path, directory_path_for_info, directory_path_for_price, category_name, product_names)


if __name__ == '__main__':
    for i in range(len(links)):
        main(links[i], directory_path, directory_path_for_price, directory_path_for_info, links_category_names[i], links_products_names[i], pagination_quantity)

    combine_json_csv(directory_path_for_info, output_directory)
    prepare_data(input_file, output_directory)