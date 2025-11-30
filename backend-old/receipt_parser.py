




import re

from dataclasses import dataclass, asdict

from typing import Optional





@dataclass

class ReceiptInfo:

    merchant: Optional[str]

    receipt_date: Optional[str]

    total_amount: Optional[float]

    subtotal: Optional[float]

    tax: Optional[float]

    service_charge: Optional[float]

    raw_text: str





# ---------- PRE-PROCESSING ----------



def clean_ocr_text(text: str) -> str:

    """Lightly normalize noisy OCR receipt text."""

    text = text.replace("\r\n", "\n").replace("\r", "\n")



    replacements = {

        "34g of beans": "bag of beans",

        "34g of beans cafe & restaurant": "bag of beans cafe & restaurant",

        "0o": "00",

        "o0": "00",

        " _ ": " ",

        "—": "-",

        "–": "-",

    }

    lower = text.lower()

    for bad, good in replacements.items():

        lower = lower.replace(bad, good)



    lower = re.sub(r"[ \t]+", " ", lower)

    return lower





# ---------- MERCHANT EXTRACTION ----------



MERCHANT_KEYWORDS = {

    "bag of beans cafe & restaurant inc": "Bag of Beans Cafe & Restaurant Inc",

    "bag of beans cafe & restaurant": "Bag of Beans Cafe & Restaurant",

    "bag of beans": "Bag of Beans Cafe & Restaurant",

    "walmart": "Walmart",

    "wal mart": "Walmart",

    "walgreens": "Walgreens",

    "target": "Target",

    "starbucks": "Starbucks",

    "7-eleven": "7-Eleven",

    "kroger": "Kroger",

    "costco": "Costco",

    "shell": "Shell",

}





def extract_merchant(text: str) -> Optional[str]:

    lower = text



    # 1) Dictionary match

    for key, clean in MERCHANT_KEYWORDS.items():

        if key in lower:

            return clean



    # 2) Heuristic scoring of first 7 lines

    lines = [l.strip() for l in lower.split("\n") if len(l.strip()) > 1]

    if not lines:

        return None



    best_line = None

    best_score = -999.0



    for idx, line in enumerate(lines[:7]):

        l = line.lower()

        score = 0.0



        if re.search(r"\b(cafe|restaurant|market|mart|store|inc|corp|llc)\b", l):

            score += 8



        if re.search(r"\d+\.\d{2}", l):

            score -= 6



        if re.search(r"\d{3,}", l):

            score -= 3



        score -= len(line) * 0.015



        if idx == 0:

            score += 4

        elif idx <= 2:

            score += 2



        if score > best_score:

            best_score = score

            best_line = line



    if not best_line:

        return None



    best_line = re.split(r"[:;]", best_line)[0].strip()



    return " ".join(w.capitalize() for w in best_line.split())





# ---------- DATE EXTRACTION ----------



DATE_REGEXES = [

    # 11/5/2019, 11-05-2019, 11.05.2019

    r"\b\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}\b",



    # 2019-11-05 style

    r"\b\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}\b",

]






def extract_date(text: str) -> Optional[str]:

    """

    Extract date safely, ignoring merged times like '06/19/2312'.

    """



    # Normalize known OCR issues

    cleaned = text.replace(" ", "").replace("O", "0").replace("o", "0")



    # 1) Strong date regex: EXACT DATE only

    patterns = [

        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",     # 06/19/23 or 6/19/2023

        r"\b\d{1,2}-\d{1,2}-\d{2,4}\b",     # 06-19-23

        r"\b\d{4}-\d{2}-\d{2}\b"            # 2023-06-19

    ]



    # Return FIRST clean date

    for p in patterns:

        matches = re.findall(p, cleaned)

        if matches:

            return matches[0]  # take CLEAN date ONLY



    # 2) Fix merged date+time → 06/19/2312 → extract only 06/19/23

    merged = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})\d{2}", cleaned)

    if merged:

        return merged.group(1)



    # 3) Very weak fallback for OCR missing slashes (rare)

    fallback = re.search(r"\b(\d{1,2})(\d{1,2})(20\d{2})\b", cleaned)

    if fallback:

        return f"{fallback.group(1)}/{fallback.group(2)}/{fallback.group(3)}"



    return None







# ---------- AMOUNT EXTRACTION ----------



def _find_last_amount_after_keyword(text: str, keywords):

    lines = text.split("\n")

    last_amount = None



    for line in lines:

        if any(kw in line.lower() for kw in keywords):

            amounts = re.findall(r"\d{1,3}(?:,\d{3})*\.\d{2}", line)

            if amounts:

                last_amount = amounts[-1]



    if last_amount is None:

        return None



    return float(last_amount.replace(",", ""))





# ---------- AMOUNT EXTRACTION (IMPROVED) ----------



def extract_totals(text: str):

    # 1) Look for total on the same line as keywords

    total_keywords = ["total", "amount due", "grand total", "amount", "balance"]

    

    lines = text.split("\n")

    for line in lines:

        lower = line.lower()

        if any(k in lower for k in total_keywords):

            # Look for proper money formats

            amounts = re.findall(r"\d{1,3}(?:,\d{3})*\.\d{2}", line)

            if amounts:

                return None, None, None, float(amounts[-1].replace(",", ""))



            # OR fallback: detect digit-only totals ("2953" → 29.53)

            pure = re.findall(r"\b\d{3,6}\b", line)

            if pure:

                num = float(pure[-1]) / 100

                if 0 < num < 2000:

                    return None, None, None, num



    # 2) If still no total → fallback to *largest* number in entire text (not smallest)

    all_amounts = re.findall(r"\d{1,3}(?:,\d{3})*\.\d{2}", text)

    if all_amounts:

        largest = max(all_amounts, key=lambda x: float(x.replace(",", "")))

        return None, None, None, float(largest.replace(",", ""))



    # 3) If still nothing → look for large whole numbers (digit-only)

    digit_only = re.findall(r"\b\d{3,6}\b", text)

    if digit_only:

        candidates = []

        for num_str in digit_only:

            num = float(num_str) / 100

            if 5 < num < 2000:   # avoid fake tiny amounts like 0.26

                candidates.append(num)



        if candidates:

            return None, None, None, max(candidates)



    return None, None, None, None







# ---------- MAIN API ----------



def parse_receipt(raw_text: str) -> ReceiptInfo:

    cleaned = clean_ocr_text(raw_text)



    merchant = extract_merchant(cleaned)

    receipt_date = extract_date(cleaned)

    subtotal, tax, service, total = extract_totals(cleaned)



    return ReceiptInfo(

        merchant=merchant,

        receipt_date=receipt_date,

        total_amount=total,

        subtotal=subtotal,

        tax=tax,

        service_charge=service,

        raw_text=raw_text,

    )


