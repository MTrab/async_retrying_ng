""" Test file and example. """
from datetime import datetime
import asyncio

from async_retrying_ng import RetryError, retry


@retry(attempts=3, delay=1, backoff=2)
async def request_api_async():
    """Dummy API."""
    print(f"{datetime.now()}: 200")
    raise Exception


if __name__ == "__main__":
    try:
        asyncio.run(request_api_async())  # retry
    except RetryError as exc:
        print("Retry attempts exceeded.")
