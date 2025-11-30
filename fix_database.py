#!/usr/bin/env python3
"""
Fix database - convert float amounts to string amounts
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def fix_amounts_in_database():
    """Convert all float amounts in database to string format"""
    
    # Load environment variables
    load_dotenv('/app/backend/.env')
    
    # Connect to MongoDB
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'receipts_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🔧 Fixing database amounts...")
    
    # Find all receipts with float amounts
    receipts_with_float_amounts = []
    async for receipt in db.receipts.find({"total_amount": {"$type": "number"}}):
        receipts_with_float_amounts.append(receipt)
    
    print(f"Found {len(receipts_with_float_amounts)} receipts with float amounts")
    
    # Fix each receipt
    fixed_count = 0
    for receipt in receipts_with_float_amounts:
        receipt_id = receipt['id']
        amount = receipt['total_amount']
        
        # Convert to string format
        if isinstance(amount, (int, float)):
            formatted_amount = f"${amount:.2f}"
            
            # Update the receipt
            await db.receipts.update_one(
                {"id": receipt_id},
                {"$set": {"total_amount": formatted_amount}}
            )
            
            print(f"  ✅ Fixed receipt {receipt_id}: {amount} → {formatted_amount}")
            fixed_count += 1
    
    # Also fix item amounts
    receipts_with_float_item_amounts = []
    async for receipt in db.receipts.find({"items.amount": {"$type": "number"}}):
        receipts_with_float_item_amounts.append(receipt)
    
    print(f"Found {len(receipts_with_float_item_amounts)} receipts with float item amounts")
    
    for receipt in receipts_with_float_item_amounts:
        receipt_id = receipt['id']
        items = receipt.get('items', [])
        
        # Fix item amounts
        for item in items:
            if 'amount' in item and isinstance(item['amount'], (int, float)):
                item['amount'] = f"${item['amount']:.2f}"
        
        # Update the receipt
        await db.receipts.update_one(
            {"id": receipt_id},
            {"$set": {"items": items}}
        )
        
        print(f"  ✅ Fixed item amounts for receipt {receipt_id}")
    
    print(f"\n🎉 Database fix completed!")
    print(f"   - Fixed {fixed_count} receipt amounts")
    print(f"   - Fixed {len(receipts_with_float_item_amounts)} receipts with item amounts")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_amounts_in_database())