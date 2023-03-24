## async\_retrying

Next Gen. simple retrying for asyncio - fork/fix from https://GitHub.com/hellysmile/async_retrying but updated for Python 3.10+ only

## Installation

shell

`pip install async_retrying_ng`

## Usage

python

```plaintext
    import asyncio

    from async_retrying_ng import retry

    counter = 0

    @retry
    async def fn():
        global counter

        counter += 1

        if counter == 1:
            raise RuntimeError

    async def main():
        await fn()

    loop = asyncio.get_event_loop()

    loop.run_until_complete(main())

    assert counter == 2

    loop.close()
```

Python 3.10+ is required