from typing import List, Optional

def get_statusword(status: List[int]) -> Optional[int]:
    """
    Извлечь statusword из ответа контроллера.
    Обычно statusword это два последних байта Modbus ответа.
    """
    if status and len(status) >= 2:
        return status[-2] | (status[-1] << 8)
    return None

def is_ready_to_switch_on(status: List[int]) -> bool:
    sw = get_statusword(status)
    # Bit 0: Ready to switch on
    return bool(sw and (sw & 0x0001))

def is_switched_on(status: List[int]) -> bool:
    sw = get_statusword(status)
    # Bit 1: Switched on
    return bool(sw and (sw & 0x0002))

def is_operation_enabled(status: List[int]) -> bool:
    sw = get_statusword(status)
    # Bit 2: Operation enabled
    return bool(sw and (sw & 0x0004))

def is_fault(status: List[int]) -> bool:
    sw = get_statusword(status)
    # Bit 3: Fault (1 = есть ошибка)
    return bool(sw and (sw & 0x0008))

def is_voltage_enabled(status: List[int]) -> bool:
    sw = get_statusword(status)
    # Bit 4: Voltage enabled
    return bool(sw and (sw & 0x0010))

def is_quick_stop(status: List[int]) -> bool:
    sw = get_statusword(status)
    # Bit 5: Quick stop
    return bool(sw and (sw & 0x0020))

def is_switch_on_disabled(status: List[int]) -> bool:
    sw = get_statusword(status)
    # Bit 6: Switch on disabled
    return bool(sw and (sw & 0x0040))

def is_warning(status: List[int]) -> bool:
    sw = get_statusword(status)
    # Bit 7: Warning
    return bool(sw and (sw & 0x0080))

def is_target_reached(status: List[int]) -> bool:
    sw = get_statusword(status)
    # Bit 10: Target reached
    return bool(sw and (sw & 0x0400))

def is_internal_limit_active(status: List[int]) -> bool:
    sw = get_statusword(status)
    # Bit 11: Internal limit active
    return bool(sw and (sw & 0x0800))

def is_homing_attained(status: List[int]) -> bool:
    if status and len(status) >= 21:
        status_value = status[-2]
        return bool(status_value & 1)
    return False

def is_homing_error(status: List[int]) -> bool:
    sw = get_statusword(status)
    # Bit 13: Homing error
    return bool(sw and (sw & 0x2000))

def is_shutdown(status: list[int]) -> bool:
    sw = get_statusword(status)
    # Shutdown = ready_to_switch_on + switched_on + НЕ operation_enabled
    # Обычно это 0x0006: (бит 1 и бит 2 = 1, бит 3 = 0)
    # return sw is not None and (sw & 0x006F) == 0x0006
    if len(status) >= 20:
        return status[19] in (6, 33, 2)
    return False

def is_switched_on_state(status: List[int]) -> bool:
    sw = get_statusword(status)
    # Состояние Switched On: ready + switched_on + NOT enabled
    return bool(sw is not None and (sw & 0x006F) == 0x0023)
    # 0x0023 = 0b0010 0011 (ready=1, switched_on=1, operation_enabled=0, voltage_enabled=1, quick_stop=0, switch_on_disabled=0)

def is_enabled_state(status: List[int]) -> bool:
    sw = get_statusword(status)
    # Состояние Enabled Operation: ready + switched_on + operation_enabled
    return bool(sw is not None and (sw & 0x006F) == 0x0027)
    # 0x0027 = 0b0010 0111 (ready=1, switched_on=1, enabled=1, voltage=1, quick_stop=0, switch_on_disabled=0)

def is_moving(status: List[int]) -> bool:
    sw = get_statusword(status)
    # Движение выполняется если target_reached == 0 и ошибок нет
    return bool(sw and not (sw & 0x0400) and not (sw & 0x0008))

def is_moving_done(status: List[int]) -> bool:
    return is_target_reached(status)

def is_no_error(status: List[int]) -> bool:
    return not is_fault(status)

def is_homing_done(status: List[int]) -> bool:
    # Homing завершён: бит 12 установлен (homing attained), ошибки нет
    return is_homing_attained(status) and is_no_error(status)

# Пример использования в твоём драйвере:
# if is_enabled_state(status): ...
# if is_fault(status): ...
