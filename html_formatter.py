from bs4 import BeautifulSoup
import os

# Папка, где находятся HTML файлы
folder_path = './'  # Укажите путь к вашей папке с HTML файлами

# Перебираем все файлы в указанной папке
for filename in os.listdir(folder_path):
    if filename.endswith('.html'):
        file_path = os.path.join(folder_path, filename)

        # Открываем исходный HTML файл
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Форматируем HTML с отступами
        formatted_html = soup.prettify()

        # Сохраняем отформатированный HTML в новый файл с "_formatted" в названии
        formatted_file_path = os.path.join(folder_path, f"{filename}")
        with open(formatted_file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_html)

        print(f"HTML файл {filename} был успешно отформатирован и сохранен как {formatted_file_path}")
