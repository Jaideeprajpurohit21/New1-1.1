
#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Master Transaction Processor with ML Category Prediction

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""
#!/usr/bin/env python3


import re

from dataclasses import dataclass

from typing import Optional, Dict, Any





@dataclass

class ParsedReceipt:

    merchant: Optional[str]

    date: Optional[str]

    total: Optional[float]

    subtotal: Optional[float]

    tax: Optional[float]

    service_charge: Optional[float]

    category: str

    confidence: float





def clean_ocr_text(text: str) -> str:

    text = text.replace("\r", "").replace("\n\n", "\n")

    corrections = {

        "34g of beans": "bag of beans",

        "0o": "00",

        "o0": "00",

        "—": "-",

        "–": "-",

        "_": " ",

    }

    lower = text.lower()

    for bad, good in corrections.items():

        lower = lower.replace(bad, good)

    lower = re.sub(r"[ \t]+", " ", lower)

    return lower





KNOWN_MERCHANTS = {

    "bag of beans": "Bag Of Beans Cafe & Restaurant",

    "bag of beans cafe": "Bag Of Beans Cafe & Restaurant",

    "walgreens": "Walgreens",

    "walmart": "Walmart",

    "wal mart": "Walmart",

    "cvs": "CVS",

    "target": "Target",

    "shell": "Shell Gas Station",

    "mcdonald": "McDonald's",

    "7-eleven": "7-Eleven",

    "7 eleven": "7-Eleven",

    "costco": "Costco",

}





def extract_merchant(text: str) -> Optional[str]:

    lower = text.lower()

    for key, clean in KNOWN_MERCHANTS.items():

        if key in lower:

            return clean



    lines = [l.strip() for l in lower.split("\n") if len(l.strip()) > 1]

    best_line = None

    best_score = -999



    for idx, line in enumerate(lines[:6]):

        score = 0

        if re.search(r"(cafe|restaurant|mart|store|market|shop|inc)", line):

            score += 5

        if not re.search(r"\d{3,}", line):

            score += 3

        if line.isupper():

            score += 1

        if idx == 0:

            score += 4

        if score > best_score:

            best_score = score

            best_line = line



    if best_line:

        return " ".join(w.capitalize() for w in best_line.split())



    return None





DATE_PATTERNS = [

    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",

    r"\b\d{4}-\d{1,2}-\d{1,2}\b",

    r"\b\d{1,2}-\d{1,2}-\d{2,4}\b",

]





def extract_date(text: str) -> Optional[str]:

    for p in DATE_PATTERNS:

        m = re.search(p, text)

        if m:

            return m.group(0)

    return None





def _extract_amount(keyword_list, text: str) -> Optional[float]:

    lines = text.split("\n")

    for line in lines:

        if any(k in line for k in keyword_list):

            nums = re.findall(r"\d+\.\d{2}", line)

            if nums:

                return float(nums[-1])

    return None





def extract_totals(text: str):

    subtotal = _extract_amount(["subtotal"], text)

    tax = _extract_amount(["tax", "vat"], text)

    service = _extract_amount(["service", "serv charge"], text)

    total = _extract_amount(["amount due", "total"], text)



    if total is None:

        nums = re.findall(r"\d+\.\d{2}", text)

        if nums:

            total = max(float(n) for n in nums)



    return subtotal, tax, service, total





def categorize_receipt(text: str) -> (str, float):

    lower = text.lower()



    if any(w in lower for w in ["coffee", "cafe", "restaurant", "diner"]):

        return "Meals & Entertainment", 0.85



    if any(w in lower for w in ["fuel", "gas", "petrol", "diesel", "shell"]):

        return "Transportation & Fuel", 0.9



    if any(w in lower for w in ["grocery", "supermarket", "market", "walgreens", "walmart"]):

        return "Groceries", 0.8



    return "Uncategorized", 0.5





class TransactionProcessor:

    def process_transaction(self, raw_text: str) -> Dict[str, Any]:

        cleaned = clean_ocr_text(raw_text)



        merchant = extract_merchant(cleaned)

        date = extract_date(cleaned)

        subtotal, tax, service, total = extract_totals(cleaned)

        category, conf = categorize_receipt(cleaned)



        return {

            "merchant": merchant,

            "date": date,

            "amount": total,

            "subtotal": subtotal,

            "tax": tax,

            "service_charge": service,

            "category": category,

            "confidence": conf,

        }



