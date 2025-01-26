import os
from bs4 import BeautifulSoup

# Папка, где находятся HTML файлы
folder_path = './'  # Укажите путь к вашей папке с HTML файлами
css_folder_path = './static/css'  # Укажите путь к вашей папке с HTML файлами
# Перебираем все файлы в указанной папке
for filename in os.listdir(folder_path):
    if filename.endswith('.html'):
        file_path = os.path.join(folder_path, filename)

        # Открываем HTML файл
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        css = ''

        # Ищем все элементы с атрибутом style
        for element in soup.find_all(style=True):
            styles = element['style']
            tag = element.name
            # Создаем селектор CSS (если есть id или class, то добавляем их)
            selector = tag
            if element.get('id'):
                selector += f"#{element['id']}"
            if element.get('class'):
                selector += ''.join(f".{cls}" for cls in element.get('class'))

            # Добавляем стили в CSS строку
            css += f"{selector} {{\n  {styles}\n}}\n\n"

            # Удаляем атрибут style из элемента
            del element['style']

        # Сохраняем измененный HTML файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

        # Сохраняем CSS файл с уникальным именем для каждого HTML файла
        css_filename = f"{filename.replace('.html', '')}_styles.css"
        css_file_path = os.path.join(css_folder_path, css_filename)
        with open(css_file_path, 'w', encoding='utf-8') as f:
            f.write(css)

        # Подключаем CSS файл в HTML
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Создаем тег <link> для подключения CSS
        link_tag = soup.new_tag('link', rel='stylesheet', href=css_file_path)
        
        # Добавляем тег <link> в <head>
        if soup.head:
            soup.head.append(link_tag)
        else:
            head_tag = soup.new_tag('head')
            soup.html.insert(0, head_tag)
            head_tag.append(link_tag)

        # Сохраняем измененный HTML файл с подключенным CSS
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

        print(f'Стили из файла {filename} успешно перенесены в файл {css_filename} и подключены к HTML файлу.')