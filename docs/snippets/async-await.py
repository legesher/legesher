import asyncio


async def brew(drink, seconds):
    await asyncio.sleep(seconds)
    print(drink, "is ready")
    return drink


async def main():
    drinks = await asyncio.gather(brew("tea", 0.2), brew("coffee", 0.1))
    print("served:", drinks)


asyncio.run(main())
