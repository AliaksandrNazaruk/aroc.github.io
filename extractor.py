import requests
import os

# Ваш токен и ID файла Figma
FIGMA_API_TOKEN = "figd_qV2QjLVEp5bsyzZD-EqKrh_8Muz7zWR1bhaE1ASk"
FILE_ID = "ID_ФАЙЛА"  # Замените на настоящий ID файла из Figma (из URL)

# Заголовки для авторизации
headers = {"X-Figma-Token": FIGMA_API_TOKEN}

# Создаем папку для сохранения изображений
output_dir = "figma_images"
os.makedirs(output_dir, exist_ok=True)

# Шаг 1: Получение информации о файле
file_url = f"https://api.figma.com/v1/files/{FILE_ID}"
file_response = requests.get(file_url, headers=headers)

if file_response.status_code != 200:
    print("Ошибка при получении информации о файле:", file_response.json())
    exit()

file_data = file_response.json()

# Шаг 2: Сбор всех узлов, содержащих изображения
def extract_image_nodes(data, nodes=[]):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "type" and value == "IMAGE":
                nodes.append(data["id"])
            elif isinstance(value, (dict, list)):
                extract_image_nodes(value, nodes)
    elif isinstance(data, list):
        for item in data:
            extract_image_nodes(item, nodes)
    return nodes

image_nodes = extract_image_nodes(file_data["document"])
print(f"Найдено {len(image_nodes)} изображений.")

# Шаг 3: Экспорт изображений через API
for node_id in image_nodes:
    image_url = f"https://api.figma.com/v1/images/{FILE_ID}?ids={node_id}"
    image_response = requests.get(image_url, headers=headers)

    if image_response.status_code == 200:
        image_data = image_response.json()
        image_link = image_data["images"].get(node_id)

        if image_link:
            # Скачиваем изображение
            img = requests.get(image_link)
            file_path = os.path.join(output_dir, f"{node_id}.png")
            with open(file_path, "wb") as f:
                f.write(img.content)
            print(f"Сохранено: {file_path}")
        else:
            print(f"Не удалось получить ссылку на изображение для узла {node_id}.")
    else:
        print(f"Ошибка при запросе изображения для узла {node_id}: {image_response.json()}")

print(f"Изображения сохранены в папке: {output_dir}")
