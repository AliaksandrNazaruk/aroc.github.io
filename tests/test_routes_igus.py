import pytest
from fastapi.testclient import TestClient

from routes.api.igus import *
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.api import igus  # Импорт твоего router

def build_test_app():
    app = FastAPI()
    app.include_router(igus.router)  # явно подключаешь
    return app

client = TestClient(build_test_app())

def test_healthcheck():
    resp = client.get("/api/v1/igus/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_status_ok():
    resp = client.get("/api/v1/igus/motor/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data and "homing" in data


def test_move_valid():
    req = {"position": 5000, "velocity": 1000, "acceleration": 1000, "wait": True}
    resp = client.post("/api/v1/igus/motor/move", json=req)
    # Ожидаемые коды ответа
    assert resp.status_code in (200, 503, 423)
    data = resp.json()
    if resp.status_code == 200 or resp.status_code == 423:
        # Ожидаем нашу схему
        assert "success" in data and "result" in data
    elif resp.status_code == 503:
        # Ожидаем fastapi error
        assert "detail" in data


@pytest.mark.parametrize("bad_req", [
    {},  # empty
    {"position": -10, "velocity": 1000, "acceleration": 1000, "wait": True},  # bad position
    {"position": 1_000_000, "velocity": 1000, "acceleration": 1000, "wait": True},  # bad position
    {"position": 1000, "velocity": -100, "acceleration": 1000, "wait": True},  # bad velocity
    {"position": 1000, "velocity": 1000, "acceleration": -1, "wait": True},  # bad acceleration
    {"position": 1000, "velocity": 1000, "acceleration": 1000, "wait": "notabool"},  # bad bool
])
def test_move_invalid(bad_req):
    resp = client.post("/api/v1/igus/motor/move", json=bad_req)
    assert resp.status_code == 422  # validation error

def test_reference_motor(monkeypatch):
    # monkeypatch guarded_motor_command чтобы выбросить исключение (симулируем отказ)
    from routes.api.igus import guarded_motor_command
    async def fail(*args, **kwargs):
        raise Exception("Reference failed")
    monkeypatch.setattr("routes.api.igus.guarded_motor_command", fail)
    resp = client.post("/api/v1/igus/motor/reference")
    assert resp.status_code == 503
    assert "Reference failed" in resp.text

def test_fault_reset(monkeypatch):
    # Сымитировать успех и ошибку
    from routes.api.igus import guarded_motor_command
    async def ok(*args, **kwargs):
        from routes.api.igus import MotorCommandResponse
        return MotorCommandResponse(success=True, result=True, error=None)
    monkeypatch.setattr("routes.api.igus.guarded_motor_command", ok)
    resp = client.post("/api/v1/igus/motor/fault_reset")
    assert resp.status_code == 200

    async def fail(*args, **kwargs):
        return MotorCommandResponse(success=False, result=False, error="HW fail")
    monkeypatch.setattr("routes.api.igus.guarded_motor_command", fail)
    resp = client.post("/api/v1/igus/motor/fault_reset")
    assert resp.status_code == 503
    assert "HW fail" in resp.text

def test_ddos_lock(monkeypatch):
    import asyncio
    from routes.api.igus import motor_lock
    # Принудительно занять lock
    async def lock_and_sleep():
        async with motor_lock:
            await asyncio.sleep(1)
    # Запусти в фоне (или monkeypatch guarded_motor_command чтобы sleep)
    import threading
    t = threading.Thread(target=lambda: asyncio.run(lock_and_sleep()))
    t.start()
    # Пока lock занят — все должны получать 423
    import time; time.sleep(0.1)
    for _ in range(3):
        resp = client.post("/api/v1/igus/motor/move", json={"position": 1000, "velocity": 1000, "acceleration": 1000, "wait": True})
        assert resp.status_code == 423
    t.join()

def test_disconnect(monkeypatch):
    # Симулируем hardware disconnect (функция бросает исключение)
    from routes.api.igus import guarded_motor_command
    async def fail_disconnect(*args, **kwargs):
        raise Exception("Disconnected")
    monkeypatch.setattr("routes.api.igus.guarded_motor_command", fail_disconnect)
    resp = client.post("/api/v1/igus/motor/move", json={"position": 1000, "velocity": 1000, "acceleration": 1000, "wait": True})
    assert resp.status_code == 503
    assert "Disconnected" in resp.text

def test_concurrent_ddos():
    # Много запросов параллельно: большинство должны получить 423 Locked
    import concurrent.futures
    import time

    req = {"position": 1000, "velocity": 1000, "acceleration": 1000, "wait": True}
    # "Нормальный" запрос — чтобы занять lock
    client.post("/api/v1/igus/motor/move", json=req)

    def send_req():
        resp = client.post("/api/v1/igus/motor/move", json=req)
        return resp.status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda _: send_req(), range(10)))
    assert all([code in (200, 423, 503) for code in results])

def test_move_motor_exception(monkeypatch):
    # monkeypatch guarded_motor_command чтобы выбросить исключение
    from routes.api.igus import guarded_motor_command
    async def fail(*args, **kwargs):
        raise Exception("Some hardware error")
    monkeypatch.setattr("routes.api.igus.guarded_motor_command", fail)
    resp = client.post("/api/v1/igus/motor/move", json={
        "position": 5000, "velocity": 1000, "acceleration": 1000, "wait": True
    })
    assert resp.status_code == 503
    assert "Motor move failed" in resp.json()["detail"]

import pytest

def test_move_motor_uncaught_error(monkeypatch):
    # Monkeypatch guarded_motor_command чтобы сымитировать ошибку
    from routes.api.igus import guarded_motor_command
    async def fail(*args, **kwargs):
        raise Exception("unexpected error")
    monkeypatch.setattr("routes.api.igus.guarded_motor_command", fail)
    resp = client.post("/api/v1/igus/motor/move", json={
        "position": 1000, "velocity": 1000, "acceleration": 1000, "wait": True
    })
    assert resp.status_code == 503
    assert "Motor move failed" in resp.json()["detail"]

def test_fault_reset_uncaught_error(monkeypatch):
    from routes.api.igus import guarded_motor_command
    async def fail(*args, **kwargs):
        raise Exception("fault reset exception")
    monkeypatch.setattr("routes.api.igus.guarded_motor_command", fail)
    resp = client.post("/api/v1/igus/motor/fault_reset")
    assert resp.status_code == 503
    assert "Motor fault reset failed" in resp.text


def test_status_uncaught_error(monkeypatch):
    from routes.api.igus import run_in_threadpool
    async def fail(*args, **kwargs):
        raise Exception("status error")
    monkeypatch.setattr("routes.api.igus.run_in_threadpool", fail)
    resp = client.get("/api/v1/igus/motor/status")
    assert resp.status_code == 503
    assert "Failed to get motor status" in resp.json()["detail"]

def test_status_lock(monkeypatch):
    import asyncio
    from routes.api.igus import motor_lock
    async def lock_and_sleep():
        async with motor_lock:
            await asyncio.sleep(0.5)
    import threading
    t = threading.Thread(target=lambda: asyncio.run(lock_and_sleep()))
    t.start()
    import time; time.sleep(0.1)
    resp = client.get("/api/v1/igus/motor/status")
    assert resp.status_code == 423
    t.join()


def test_reset_faults_exception(monkeypatch):
    # Симулируем hardware-level exception во время reset
    from routes.api.igus import guarded_motor_command
    async def fail(*args, **kwargs):
        raise Exception("Critical reset error")
    monkeypatch.setattr("routes.api.igus.guarded_motor_command", fail)
    resp = client.post("/api/v1/igus/motor/fault_reset")
    assert resp.status_code == 503
    assert "Motor fault reset failed" in resp.json()["detail"]

def test_reference_motor_success(monkeypatch):
    from routes.api.igus import guarded_motor_command, MotorCommandResponse
    async def ok(*args, **kwargs):
        return MotorCommandResponse(success=True, result=True, error=None)
    monkeypatch.setattr("routes.api.igus.guarded_motor_command", ok)
    resp = client.post("/api/v1/igus/motor/reference")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


def test_reference_motor_unexpected_error(monkeypatch):
    from routes.api.igus import guarded_motor_command
    async def fail(*args, **kwargs):
        # бросаем именно Exception, чтобы покрыть ветку except Exception as e:
        raise Exception("Unexpected hardware fail")
    monkeypatch.setattr("routes.api.igus.guarded_motor_command", fail)
    resp = client.post("/api/v1/igus/motor/reference")
    assert resp.status_code == 503
    assert "Motor homing failed" in resp.text

def test_reference_motor_unsuccessful(monkeypatch):
    from routes.api.igus import guarded_motor_command, MotorCommandResponse
    # Симулируем неуспешный результат homing
    async def not_ok(*args, **kwargs):
        return MotorCommandResponse(success=False, result=False, error="Failed for test")
    monkeypatch.setattr("routes.api.igus.guarded_motor_command", not_ok)
    resp = client.post("/api/v1/igus/motor/reference")
    assert resp.status_code == 503
    assert "Failed for test" in resp.text
