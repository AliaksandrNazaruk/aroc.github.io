import time
from drivers.igus_scripts.igus_motor import IgusMotor  # Импортируй правильно свой класс

MOTOR_IP = "192.168.1.230"  # Поставь реальный IP

def test_connection(motor):
    print("[TEST] Проверка соединения")
    assert motor.is_connected(), "Нет соединения!"

def test_fault_reset(motor):
    print("[TEST] Сброс ошибки")
    result = motor.fault_reset()
    assert motor.is_connected(), "Соединение потеряно после сброса ошибки"
    assert motor.get_error() is None, "Ошибка после fault_reset"

def test_home(motor):
    print("[TEST] Хоминг")
    result = motor.home()
    assert motor.is_homed(), "Homing не завершён"
    assert motor.get_error() is None, "Ошибка после homing"

def test_move(motor, target=12345):
    print(f"[TEST] Перемещение к {target}")
    result = motor.move_to_position(target, velocity=4000, acceleration=1500)
    pos = motor.get_position()
    print(f"[TEST] Ожидалось: {target}, фактическая позиция: {pos}")
    assert abs(pos - target) < 500, f"Позиция не достигнута: {pos} (target {target})"
    assert motor.get_error() is None, "Ошибка после движения"

def test_reconnect(motor):
    print("[TEST] Тест reconnect (искусственный разрыв)")
    motor.shutdown()
    print("[TEST] Ждём 5 секунд перед reconnect...")
    time.sleep(5)
    motor2 = IgusMotor(MOTOR_IP)
    assert motor2.is_connected(), "Reconnect не удался"
    assert motor2.get_error() is None, "Ошибка после reconnect"
    # Вернуть мотор для дальнейших тестов
    return motor2

def test_status(motor):
    print("[TEST] Проверка get_status")
    status = motor.get_status()
    print(f"[TEST] Текущее состояние: {status}")
    for key in ["position", "homed", "active", "last_error", "connected"]:
        assert key in status, f"Нет ключа {key} в статусе!"

def test_repeatable_movement(motor, cycles=10, pos1=2000, pos2=4000, tolerance=500):
    print(f"[TEST] Стресс на {cycles} циклов движения")
    for i in range(cycles):
        print(f"[TEST] Цикл {i+1}/{cycles}: {pos1} -> {pos2}")
        motor.move_to_position(pos1, velocity=5000, acceleration=1000)
        real_pos1 = motor.get_position()
        statusword1 = motor.get_statusword()
        print(f"  Ожидалось: {pos1}, реально: {real_pos1}, statusword=0x{statusword1:x}")
        assert abs(real_pos1 - pos1) < tolerance, f"[FAIL] Цикл {i+1}: Мотор не дошёл до {pos1}, фактическая позиция: {real_pos1}"

        time.sleep(0.3)

        motor.move_to_position(pos2, velocity=5000, acceleration=1000)
        real_pos2 = motor.get_position()
        statusword2 = motor.get_statusword()
        print(f"  Ожидалось: {pos2}, реально: {real_pos2}, statusword=0x{statusword2:x}")
        assert abs(real_pos2 - pos2) < tolerance, f"[FAIL] Цикл {i+1}: Мотор не дошёл до {pos2}, фактическая позиция: {real_pos2}"

        time.sleep(0.3)
    print("[TEST] Стресс-тест движения завершён")

def test_self_diagnostics(motor):
    print("[TEST] Самодиагностика после работы")
    assert motor.is_connected(), "Нет соединения!"
    assert motor.is_homed(), "Нет homing!"
    for tgt in [1000, 3000, 6000]:
        print(f"[TEST] Перемещаемся на {tgt}")
        motor.move_to_position(tgt)
        pos = motor.get_position()
        print(f"[TEST] Ожидалось {tgt}, реально {pos}")
        assert abs(pos - tgt) < 500, f"Позиция не совпала: {pos}"

def main():
    print("=" * 60)
    print("== СТАРТ АВТОМАТИЧЕСКОГО ТЕСТА IGUS MOTOR ==")
    print("=" * 60)

    # 1. Подключение и инициализация
    motor = IgusMotor(MOTOR_IP)
    test_connection(motor)

    # 2. Сброс ошибки
    test_fault_reset(motor)

    # 3. Хоминг
    test_home(motor)

    # 4. Перемещение
    test_move(motor, target=12345)

    # 5. Проверка статуса
    test_status(motor)

    # 6. Стресс: 10 циклов движения (можешь увеличить cycles)
    test_repeatable_movement(motor, cycles=10, pos1=20000, pos2=40000)

    # 7. Самодиагностика
    test_self_diagnostics(motor)

    # 8. Проверка reconnect (и продолжаем тестировать с новым объектом)
    motor = test_reconnect(motor)

    # 9. Финальный fault_reset + home (проверка стабильности после reconnect)
    test_fault_reset(motor)
    test_home(motor)

    print("=" * 60)
    print("== ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! ==")
    print("=" * 60)
    motor.shutdown()

if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print("\n[TEST] FAIL:", e)
        print("== Тест остановлен из-за критической ошибки ==")
        exit(1)
    except Exception as e:
        print("\n[TEST] EXCEPTION:", e)
        print("== Тест остановлен по исключению ==")
        exit(2)
