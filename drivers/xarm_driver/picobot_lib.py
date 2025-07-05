#!/usr/bin/env python3
"""
gripper_controller.py

Библиотека для управления гриппером через модбас-интерфейс (tgpio_modbus) из xarm_api.py.
Код написан с высокой степенью надежности и документирован, как если бы его создавали специалисты 
с 25-летним опытом в разработке систем для запуска межпланетных ракет на Марс.

Автор: Ваша команда инженеров
"""

import logging

# Настройка логирования для подробного отслеживания работы
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GripperError(Exception):
    """Исключение, выбрасываемое при ошибках управления гриппером."""
    pass

class GripperController:
    """
    Класс для управления гриппером через модбас-интерфейс tgpio_modbus.

    Конструктор принимает объект xArmAPI и настраивает параметры связи.
    """
    def __init__(self, xarm_api, baudrate=9600, timeout=100):
        """
        Инициализация контроллера гриппера.

        Аргументы:
            xarm_api: экземпляр класса XArmAPI, предоставляющий функции tgpio_modbus 
                     (см. :contentReference[oaicite:2]{index=2}, :contentReference[oaicite:3]{index=3}).
            baudrate: скорость передачи модбас (по умолчанию 9600).
            timeout: таймаут в миллисекундах для модбас-соединения (по умолчанию 100 мс).
        """
        self.api = xarm_api
        self._configure_modbus(baudrate, timeout)

    def _configure_modbus(self, baudrate, timeout):
        """
        Настройка параметров модбас-соединения для tool GPIO.

        Используются функции set_tgpio_modbus_baudrate и set_tgpio_modbus_timeout из xarm_api.py.
        (см. :contentReference[oaicite:4]{index=4} и :contentReference[oaicite:5]{index=5})
        """
        ret = self.api.set_tgpio_modbus_baudrate(baudrate)
        if ret != 0:
            logger.error("Не удалось установить модбас-скорость: %s", baudrate)
            raise GripperError(f"Ошибка установки модбас-скорости, код: {ret}")
        ret = self.api.set_tgpio_modbus_timeout(timeout)
        if ret != 0:
            logger.error("Не удалось установить модбас-таймаут: %s", timeout)
            raise GripperError(f"Ошибка установки модбас-таймаута, код: {ret}")
        logger.info("Параметры модбас-соединения установлены: baudrate=%s, timeout=%s", baudrate, timeout)

    def _send_modbus_command(self, command, min_response_length=10, host_id=9,
                             is_transparent=True, use_503_port=False):
        """
        Отправка команды по протоколу модбас через функцию getset_tgpio_modbus_data.

        Аргументы:
            command: список целых чисел, представляющих байты команды (например, [0x01, 0x07, ...]).
            min_response_length: минимальная ожидаемая длина ответа (по умолчанию 10 байт).
            host_id: идентификатор хоста (по умолчанию 9 – TGPIO_HOST_ID).
            is_transparent: использовать ли прозрачную передачу (по умолчанию False).
            use_503_port: использовать ли порт 503 для передачи (по умолчанию False).

        Возвращает:
            Ответ устройства в виде списка байт.

        Генерирует:
            GripperError – в случае ошибки передачи.
        """
        logger.debug("Отправка модбас-команды: %s", command)
        ret, response = self.api.getset_tgpio_modbus_data(
            command,
            min_res_len=min_response_length,
            host_id=host_id,
            is_transparent_transmission=is_transparent,
            use_503_port=use_503_port
        )
        if ret != 0:
            logger.error("Ошибка отправки модбас-команды, код: %s", ret)
            raise GripperError(f"Модбас-команда завершилась ошибкой, код: {ret}")
        logger.debug("Получен ответ: %s", response)
        return response

    def activate(self):
        """
        Активировать гриппер (включить вакуум).

        Отправляет команду VAC ON по протоколу RS485:
            Команда: 01-07-00-01-00-29-02-01-00-82
            (см. документацию piCOBOTe RS485 Protocol :contentReference[oaicite:6]{index=6})

        Возвращает:
            Ответ устройства (список байт).

        Генерирует:
            GripperError – в случае ошибки.
        """
        cmd_vac_on = [0x01, 0x07, 0x00, 0x01, 0x00, 0x29, 0x02, 0x01, 0x00, 0x82]
        logger.info("Активирую гриппер (VAC ON)...")
        response = self._send_modbus_command(cmd_vac_on)
        logger.info("Гриппер активирован, получен ответ: %s", response)
        return response

    def deactivate(self):
        """
        Деактивировать гриппер (выключить вакуум).

        Отправляет команду VAC OFF по протоколу RS485:
            Команда: 01-07-00-01-00-29-02-00-00-97
            (см. документацию piCOBOTe RS485 Protocol :contentReference[oaicite:7]{index=7})

        Возвращает:
            Ответ устройства (список байт).

        Генерирует:
            GripperError – в случае ошибки.
        """
        cmd_vac_off = [0x01, 0x07, 0x00, 0x01, 0x00, 0x29, 0x02, 0x00, 0x00, 0x97]
        logger.info("Деактивирую гриппер (VAC OFF)...")
        response = self._send_modbus_command(cmd_vac_off)
        logger.info("Гриппер деактивирован, получен ответ: %s", response)
        return response

    def set_custom_command(self, command, min_response_length=10):
        """
        Отправить произвольную модбас-команду на устройство.

        Аргументы:
            command: список байтов команды (например, [0x01, 0xXX, ...]).
            min_response_length: минимальное ожидаемое количество байтов в ответе.

        Возвращает:
            Ответ устройства в виде списка байт.

        Генерирует:
            GripperError – в случае ошибки.
        """
        logger.info("Отправка пользовательской команды: %s", command)
        return self._send_modbus_command(command, min_response_length)

# # Пример использования библиотеки
# if __name__ == '__main__':
#     # Предполагается, что xarm_api уже импортирован и настроен
#     try:
#         from xarm.wrapper import XArmAPI
#     except ImportError:
#         logger.error("Модуль xarm_api не найден. Проверьте установку библиотеки xArm.")
#         exit(1)

#     # Создаем экземпляр API (укажите корректный порт или IP)
#     try:
#         arm = XArmAPI(port="192.168.1.220", is_radian=False)
#         # Подключение производится внутри XArmAPI, если необходимо, можно вызвать arm.connect()
#     except Exception as e:
#         logger.error("Ошибка при инициализации XArmAPI: %s", e)
#         exit(1)

#     # Создаем контроллер гриппера, используя модбас-интерфейс
#     try:
#         gripper = GripperController(arm, baudrate=115200, timeout=100)
#         # Активируем гриппер (включаем вакуум)
#         gripper.activate()
#         # Здесь можно добавить логику ожидания, проверки состояния и т.д.
#         # Например, для деактивации:
#         gripper.deactivate()
#     except GripperError as ge:
#         logger.error("Ошибка управления гриппером: %s", ge)
#     except Exception as ex:
#         logger.error("Неожиданная ошибка: %s", ex)
