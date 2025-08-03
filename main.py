import argparse
import csv
import requests
import re
import json
from bs4 import BeautifulSoup
from datetime import datetime
from db import save_to_sqlite

BASE_URL = "https://www.b2b-center.ru"
MARKET_URL = f"{BASE_URL}/market/"

def parse_tenders(max_tenders=100):
    tenders = []
    try:
        response = requests.get(MARKET_URL, timeout=10)
        response.raise_for_status()
        listSoup = BeautifulSoup(response.text, 'html.parser')

        links = listSoup.find_all('a', class_='search-results-title')
        count = 0

        for link in links:
            if count >= max_tenders:
                break

            #номер тендера
            match = re.search(r'/tender-(\d+)/', link['href'])
            if match:
                tenderNumber = match.group(1)

            #ссылка
            url = BASE_URL + link['href']

            response = requests.get(url, timeout=10)
            tenderSoup = BeautifulSoup(response.text, 'html.parser')
            
            #категории
            td = tenderSoup.find('td', class_='fname', string='Категория ОКПД2:')
            if td:
                categoryTD = td.find_next_sibling('td')
                fullDiv = categoryTD.find('div', class_='expandable-text full')
                if not fullDiv:
                    fullDiv = categoryTD.find('div', class_='expandable-text short')
                categories = []
                items = []
                if fullDiv:
                    items = fullDiv.find_all('div')
                else:
                    items = categoryTD.find_all('div')
                for item in items:
                    b = item.find('b')
                    if b:
                        code = b.get_text(strip=True)
                        description = item.get_text(strip=True).replace(code, '', 1).strip(" \u00a0")
                        categories.append({
                            'code': code,
                            'description': description
                        })
            else:
                categories = None
            
            #тендер
            title = tenderSoup.find('div', class_='s2').get_text(strip=True)

            #организатор
            td = tenderSoup.find('td', class_='fname', string='Организатор:')
            orgTD = td.find_next_sibling('td')
            span = orgTD.find('span')
            if span:
                organizer = span.get_text(strip=True)
            else:
                organizer = orgTD.get_text(strip=True)

            #Дата окончания подачи заявок
            end_date_labels =   ['Дата окончания подачи заявок',
                                    'Актуально до'
                                ]
            td = tenderSoup.find('td', class_='fname', string=lambda x: x and any(label in x for label in end_date_labels))
            endDateTD = td.find_next_sibling('td')
            endDate = endDateTD.get_text(strip=True)

            #Закупочные позиции
            positionsLink = tenderSoup.find('a', string=lambda text: text and 'Закупочные позиции' in text)
            if positionsLink:
                listUrl = BASE_URL + positionsLink['href']

                response = requests.get(listUrl, timeout=10)
                positionsSoup = BeautifulSoup(response.text, 'html.parser')

                rows = positionsSoup.find_all('tr', class_='c2')
                positions = []
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 5:
                        number = tds[0].get_text(strip=True)        # №
                        name = tds[1].get_text(strip=True)          # Наименование
                        quantity = tds[2].get_text(strip=True)      # Количество
                        price = tds[4].get_text(strip=True)         # Цена за единицу
                        positions.append({
                            'number': number,
                            'name': name,
                            'quantity': quantity,
                            'price': price
                        })
            else:
                positions = None

            tenders.append({
                "number": tenderNumber,
                "categories": json.dumps(categories),
                "title": title,
                "organizer": organizer,
                "end_date": endDate,
                "positions": json.dumps(positions),
                "url": url
            })
            count += 1

    except Exception as e:
        print(f"Ошибка при парсинге: {e}")

    return tenders

def save_to_csv(tenders, file_path):
    keys = tenders[0].keys() if tenders else []
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(tenders)

def main(max_tenders, output, format_type):
    print(f"Парсинг первых {max_tenders} тендеров с {BASE_URL}...")
    tenders = parse_tenders(max_tenders)

    if not tenders:
        print("Тендеры не найдены.")
        return

    if format_type == "sqlite":
        db_path = output if output.endswith('.db') else output + '.db'
        save_to_sqlite(tenders, db_path)
        print(f"Данные сохранены в SQLite: {db_path}")
    else:
        csv_path = output if output.endswith('.csv') else output + '.csv'
        save_to_csv(tenders, csv_path)
        print(f"Данные сохранены в CSV: {csv_path}")

    print(f"Обработано тендеров: {len(tenders)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Парсер тендеров с b2b-center.ru")
    parser.add_argument("--max", type=int, default=100, help="Максимальное количество тендеров (по умолчанию 100)")
    parser.add_argument("--output", type=str, default="tenders.csv", help="Путь к файлу вывода")
    parser.add_argument("--format", choices=["csv", "sqlite"], default="csv", help="Формат вывода")

    args = parser.parse_args()
    main(args.max, args.output, args.format)