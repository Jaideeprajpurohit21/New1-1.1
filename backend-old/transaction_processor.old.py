#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Master Transaction Processor with ML Category Prediction

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""
#!/usr/bin/env python3


#!/usr/bin/env python3



"""

LUMINA - ADVANCED TRANSACTION PROCESSOR

Optimized for Tesseract OCR output

Supports:

- Merchant extraction

- Date extraction

- Total amount extraction

- Category detection

- Line item extraction

"""



import re

from typing import Optional, Dict, Any, List

import logging



logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)





class TransactionProcessor:

    """Advanced transaction parser."""



    # ---------------------------

    # MAIN ENTRY POINT

    # ---------------------------

    def process_transaction(self, raw_text: str) -> Dict[str, Any]:

        if not raw_text:

            return self.fail("Empty OCR text")



        merchant = self.extract_merchant(raw_text)

        date = self.extract_date(raw_text)

        amount = self.extract_total_amount(raw_text)

        items = self.extract_line_items(raw_text)

        category, confidence = self.detect_category(raw_text, merchant)



        return {

            "merchant": merchant,

            "date": date,

            "amount": amount,

            "items": items,

            "category": category,

            "confidence": confidence,

            "raw_text": raw_text,

            "processing_status": "completed"

        }



    # ---------------------------

    # MERCHANT EXTRACTION

    # ---------------------------



    def extract_merchant(self, text: str) -> Optional[str]:

        """

        Detect merchant name based on:

        - Uppercase lines

        - Lines containing merchant keywords

        - First long line in header

        """



        merchant_keywords = [

            "cafe", "restaurant", "repair", "shop", "store", "inc", "corp",

            "company", "market", "service", "garage", "auto", "center"

        ]



        lines = [line.strip() for line in text.splitlines() if line.strip()]



        for line in lines[:10]:

            low = line.lower()



            # Skip irrelevant header text

            skip = ["invoice", "receipt", "order", "bill", "qty", "table"]

            if any(s in low for s in skip):

                continue



            # Keyword-based detection

            if any(k in low for k in merchant_keywords):

                return line



            # Uppercase heuristic

            if line.replace(" ", "").isupper() and 3 <= len(line.split()) <= 8:

                return line



            # Generic fallback

            if 3 <= len(line.split()) <= 8:

                return line



        return None



    # ---------------------------

    # DATE EXTRACTION

    # ---------------------------



    def extract_date(self, text: str) -> Optional[str]:

        patterns = [

            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",

            r"\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",

            r"\b([A-Za-z]{3,9}\s+\d{1,2},\s*\d{4})\b"

        ]



        for p in patterns:

            m = re.search(p, text)

            if m:

                return m.group(1)



        return None



    # ---------------------------

    # TOTAL AMOUNT EXTRACTION

    # ---------------------------



    def extract_total_amount(self, text: str) -> Optional[float]:

        """

        Gets the final total by prioritizing:

        1. "Amount Due"

        2. "Total"

        3. Largest number in the document

        """



        lines = text.splitlines()

        candidates = []



        # 1. Look for specific total indicators

        for line in lines:

            low = line.lower()

            if "amount due" in low or "total" in low or "amt due" in low:

                nums = re.findall(r"(\d{1,3}(?:,\d{3})*(?:\.\d{2}))", line)

                for n in nums:

                    try:

                        candidates.append(float(n.replace(",", "")))

                    except:

                        pass



        if candidates:

            return max(candidates)



        # 2. Fallback: largest monetary value found in entire text

        nums = re.findall(r"(\d{1,3}(?:,\d{3})*(?:\.\d{2}))", text)

        if nums:

            try:

                return max(float(n.replace(",", "")) for n in nums)

            except:

                pass



        return None



    # ---------------------------

    # LINE ITEM EXTRACTION

    # ---------------------------



    def extract_line_items(self, text: str) -> List[Dict[str, Any]]:

        """

        Detects structured line items (description + price).

        Example:

            "Blueberry Cheesecake 175.00"

        """



        items = []

        lines = text.splitlines()



        pattern = r"(.+?)\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2}))$"



        for line in lines:

            line = line.strip()

            m = re.search(pattern, line)

            if m:

                desc = m.group(1).strip()

                amt_str = m.group(2).replace(",", "")

                try:

                    amt = float(amt_str)

                except:

                    amt = None



                items.append({

                    "description": desc,

                    "amount": f"{amt:.2f}" if amt else None,

                    "confidence": 0.90

                })



        return items



    # ---------------------------

    # CATEGORY DETECTION

    # ---------------------------



    def detect_category(self, text: str, merchant: Optional[str]):

        text_l = text.lower()

        categories = {

            "Automotive": ["repair", "tire", "oil", "brake", "auto", "labor"],

            "Food & Dining": ["cafe", "restaurant", "coffee", "burger", "tea", "cheesecake"],

            "Groceries": ["market", "grocery", "foods", "supercenter"],

            "Fuel": ["gas", "fuel", "station", "shell", "bp"],

            "Shopping": ["store", "mall", "purchase"],

            "Healthcare": ["clinic", "pharmacy", "med", "health"],

        }



        best_category = "Uncategorized"

        best_score = 0



        for cat, keys in categories.items():

            score = sum(k in text_l for k in keys)



            if merchant:

                ml = merchant.lower()

                score += sum(k in ml for k in keys)



            if score > best_score:

                best_score = score

                best_category = cat



        confidence = min(0.99, best_score / 3)

        return best_category, confidence



    # ---------------------------

    # FAILURE RESPONSE

    # ---------------------------



    def fail(self, msg: str):

        return {

            "merchant": None,

            "date": None,

            "amount": None,

            "items": [],

            "category": "Uncategorized",

            "confidence": 0.0,

            "raw_text": "",

            "processing_status": "failed",

            "error": msg

        }





if __name__ == "__main__":

    print("TransactionProcessor OK")


