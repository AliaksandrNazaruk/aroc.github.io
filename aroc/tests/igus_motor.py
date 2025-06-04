import time
from drivers.igus_scripts.igus_motor import IgusMotor  # Import your class correctly

MOTOR_IP = "192.168.1.230"  # Replace with actual IP

def test_connection(motor):
    print("[TEST] Checking connection")
    assert motor.is_connected(), "No connection!"

def test_fault_reset(motor):
    print("[TEST] Fault reset")
    result = motor.fault_reset()
    assert motor.is_connected(), "Connection lost after fault reset"
    assert motor.get_error() is None, "Error after fault_reset"

def test_home(motor):
    print("[TEST] Homing")
    result = motor.home()
    assert motor.is_homed(), "Homing not finished"
    assert motor.get_error() is None, "Error after homing"

def test_move(motor, target=12345):
    print(f"[TEST] Moving to {target}")
    result = motor.move_to_position(target, velocity=4000, acceleration=1500)
    pos = motor.get_position()
    print(f"[TEST] Expected: {target}, actual position: {pos}")
    assert abs(pos - target) < 500, f"Position not reached: {pos} (target {target})"
    assert motor.get_error() is None, "Error after movement"

def test_reconnect(motor):
    print("[TEST] Reconnect test (artificial disconnect)")
    motor.shutdown()
    print("[TEST] Waiting 5 seconds before reconnect...")
    time.sleep(5)
    motor2 = IgusMotor(MOTOR_IP)
    assert motor2.is_connected(), "Reconnect failed"
    assert motor2.get_error() is None, "Error after reconnect"
    # Return motor for further tests
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
    print("== ALL TESTS PASSED SUCCESSFULLY! ==")
    print("=" * 60)
    motor.shutdown()

if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print("\n[TEST] FAIL:", e)
        print("== Test stopped due to critical error ==")
        exit(1)
    except Exception as e:
        print("\n[TEST] EXCEPTION:", e)
        print("== Test stopped by exception ==")
        exit(2)
