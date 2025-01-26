import os

# Путь к папке с шрифтами и CSS
fonts_folder = 'fonts'
css_folder = 'static/css'

# Функция для генерации CSS @font-face
def generate_font_face_rule(font_name, font_path):
    # Получаем расширение файла (например, .woff2, .woff)
    font_extension = os.path.splitext(font_path)[1].lower()
    if font_extension in ['.woff2', '.woff', '.ttf', '.eot', '.svg']:
        return f"""
@font-face {{
    font-family: {font_name};
    src: url({font_path}) format('{font_extension[1:]}');
    font-weight: normal;
    font-style: normal;
}}
"""
    return ""

def process_css_files():
    # Получаем список всех шрифтов в папке fonts и её подпапках
    font_files = []
    for root, dirs, files in os.walk(fonts_folder):
        for file in files:
            if file.endswith(('.woff2', '.woff', '.ttf', '.eot', '.svg')):  # Шрифты с нужными расширениями
                font_files.append(os.path.join(root, file))  # Добавляем полный путь к шрифтам
    
    # Генерируем правила @font-face для каждого шрифта
    font_face_rules = ""
    for font_file in font_files:
        font_name = os.path.splitext(os.path.basename(font_file))[0]  # Название шрифта без расширения
        # Получаем относительный путь к шрифту от корня проекта
        font_path = os.path.relpath(font_file, start=fonts_folder)  
        font_face_rules += generate_font_face_rule(font_name, '../fonts/'+font_path)
    
    # Проходим по всем файлам CSS в папке и её подпапках
    for root, dirs, files in os.walk(css_folder):
        for css_file in files:
            if css_file.endswith('fonts.css'):  # Проверяем только файлы с расширением .css
                css_path = os.path.join(root, css_file)
                with open(css_path, 'r+', encoding='utf-8') as file:
                    # Считываем содержимое CSS файла
                    css_content = file.read()
                    
                    # Вставляем правила @font-face в начало файла
                    if font_face_rules:
                        css_content = font_face_rules + css_content
                    
                    # Перезаписываем файл с обновленным содержимым
                    file.seek(0)
                    file.write(css_content)
                    file.truncate()
                print(f"Шрифты подключены в файл: {css_file}")
    
    # Проходим по всем файлам CSS в папке css
    for css_file in os.listdir(css_folder):
        css_path = os.path.join(css_folder, css_file)
        if os.path.isfile(css_path) and css_file.endswith('.css'):
            with open(css_path, 'r+', encoding='utf-8') as file:
                # Считываем содержимое CSS файла
                css_content = file.read()
                
                # Вставляем правила @font-face в начало файла
                if font_face_rules:
                    css_content = font_face_rules + css_content
                
                # Перезаписываем файл с обновленным содержимым
                file.seek(0)
                file.write(css_content)
                file.truncate()
            print(f"Шрифты подключены в файл: {css_file}")

# Запуск обработки файлов
process_css_files()
