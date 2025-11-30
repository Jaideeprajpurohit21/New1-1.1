
import asyncio

from db.db import db   # <-- this is the correct import for your project



async def check():

    receipts = await db.receipts.find().to_list(None)

    print("RECEIPTS IN DB:")

    for r in receipts:

        print(r)



asyncio.run(check())


