from functools import wraps
from fastapi import HTTPException, status
from core.state import task_manager
from typing import Union

def endpoint_with_lock_guard(lock, response_model_cls=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if lock.locked():
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Device is busy"
                )
            try:
                result = await func(*args, **kwargs)
                if response_model_cls and result is not None:
                    if hasattr(response_model_cls, "__origin__") and response_model_cls.__origin__ is Union:
                        # Перебираем варианты из Union
                        for cls in response_model_cls.__args__:
                            # Пробуем распарсить результат, если не вышло — пробуем дальше
                            try:
                                if isinstance(result, dict):
                                    return cls(**result)
                                elif isinstance(result, cls):
                                    return result
                            except Exception:
                                continue
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Could not match response to any model in Union"
                        )
                    else:
                        # Обычный случай
                        if isinstance(result, dict):
                            return response_model_cls(**result)
                        else:
                            return response_model_cls(result)
                return result
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(e)
                )
        return wrapper
    return decorator

def endpoint_guard(response_model_cls=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                if response_model_cls and result is not None:
                    # Обработка Union[...] вручную
                    if hasattr(response_model_cls, "__origin__") and response_model_cls.__origin__ is Union:
                        # Перебираем варианты из Union
                        for cls in response_model_cls.__args__:
                            # Пробуем распарсить результат, если не вышло — пробуем дальше
                            try:
                                if isinstance(result, dict):
                                    return cls(**result)
                                elif isinstance(result, cls):
                                    return result
                            except Exception:
                                continue
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Could not match response to any model in Union"
                        )
                    else:
                        # Обычный случай
                        if isinstance(result, dict):
                            return response_model_cls(**result)
                        else:
                            return response_model_cls(result)
                return result
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(e)
                )
        return wrapper
    return decorator


async def wrap_async_task(coro, response_cls):
    # task_manager.create_task должен принимать функцию или coroutine
    task_id = task_manager.create_task(coro())
    return response_cls(success=True, task_id=task_id)