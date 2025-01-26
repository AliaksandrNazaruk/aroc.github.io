from http.server import SimpleHTTPRequestHandler, HTTPServer

import os
from urllib.parse import parse_qs

# Класс для обработки запросов
class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    # Обработка POST-запросов
    def do_POST(self):
        # Определяем длину данных
        content_length = int(self.headers['Content-Length'])
        # Получаем данные из тела запроса
        body = self.rfile.read(content_length).decode('utf-8')
        # Разбираем параметры
        parsed_data = parse_qs(body)

        # Преобразуем данные в формат position_1, position_2, ...
        transformed_data = {}
        for i, value in enumerate(parsed_data.get('name', []), start=1):
            if int(value) > 0:
                transformed_data[f'position_{i}'] = value

        # Выводим преобразованные данные в консоль
        print("Преобразованные данные:", transformed_data)

        # Ответ клиенту
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Data received and transformed successfully')

    # Обработка GET-запросов для отображения HTML-файлов
    def do_GET(self):
        if self.path == "/":
            # Если запрос к корню, отправляем index.html, если он существует
            self.path = "/index.html"
        
        # Проверяем, существует ли файл
        if os.path.exists(self.path[1:]):  # Убираем "/" в начале пути
            super().do_GET()
        else:
            # Если файл не найден, возвращаем 404
            self.send_error(404, "Файл не найден")
            self.end_headers()

# Запуск сервера
def run(server_class=HTTPServer, handler_class=MyHTTPRequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Сервер запущен на порту {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
