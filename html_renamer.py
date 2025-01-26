import os
import uuid
from bs4 import BeautifulSoup

# Папка с HTML файлами
folder_path = './'  # Укажите путь к вашей папке с HTML файлами

# Функция для генерации уникальных ID и имен
def generate_unique_id():
    return f"unique_{uuid.uuid4().hex}"

# Перебираем все файлы в указанной папке
for filename in os.listdir(folder_path):
    if filename.endswith('.html'):
        file_path = os.path.join(folder_path, filename)

        # Открываем HTML файл
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Проходим по всем элементам
        for element in soup.find_all(True):  # Все теги
            # Присваиваем уникальный ID, если он не существует
            if element.get('id'):
                element['id'] = element['id']+"_"+generate_unique_id()

            # Присваиваем уникальное имя, если оно не существует
            if element.get('name'):
                element['name'] = element['name']+"_"+generate_unique_id()

        # Сохраняем измененный HTML файл с новыми уникальными ID и именами
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

        print(f'Файл {filename} был обновлен с уникальными ID и именами.')
