import functools
import asyncio

process_requests = {}

def idempotency(func):
    """Decorator for idempotency functions"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        idempotency_key = kwargs.pop('idempotency_key', None)
        if not idempotency_key:
            raise ValueError("idempotency key not found")

        if idempotency_key in process_requests:
            print(f"requests process with key {idempotency_key}")
            return process_requests[idempotency_key]

        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)

        process_requests[idempotency_key] = result
        print(f"Requisição processada com a chave: {idempotency_key}")
        return result

    return wrapper