import cv2

import numpy as np

import easyocr

import re

from datetime import datetime



# Initialize EasyOCR reader

reader = easyocr.Reader(['en'], gpu=False)



# -----------------------------

# IMAGE PREPROCESSING

# -----------------------------

def preprocess_image(image_path):

    img = cv2.imread(image_path)

    if img is None:

        return None



    # Grayscale

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)



    # Denoise

    gray = cv2.fastNlMeansDenoising(gray, h=30)



    # Threshold

    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)



    # Deskew

    coords = np.column_stack(np.where(thresh > 0))

    angle = cv2.minAreaRect(coords)[-1]



    if angle < -45:

        angle = -(90 + angle)

    else:

        angle = -angle



    (h, w) = thresh.shape[:2]

    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)

    deskewed = cv2.warpAffine(thresh, M, (w, h), flags=cv2.INTER_CUBIC)



    return deskewed





# -----------------------------

# TEXT EXTRACTION

# -----------------------------

def extract_text(image_path):

    processed = preprocess_image(image_path)

    if processed is None:

        return ""



    result = reader.readtext(processed, detail=0)

    return "\n".join(result)





# -----------------------------

# TOTAL EXTRACTION

# -----------------------------

def extract_total(text):

    lines = text.split("\n")



    # 1) Prefer line with the word TOTAL (avoid savings)

    for line in lines:

        if "total" in line.lower() and "savings" not in line.lower():

            m = re.search(r"(\d+\.\d{2})", line.replace(",", "."))

            if m:

                return m.group(1)



    # 2) Fallback: choose largest money-looking number between 5 and 5000

    nums = re.findall(r"\d+\.\d{2}", text.replace(",", "."))

    amounts = [float(x) for x in nums if 5 <= float(x) <= 5000]



    if amounts:

        return f"{max(amounts):.2f}"



    return None





# -----------------------------

# DATE EXTRACTION

# -----------------------------

def extract_date(text):

    date_patterns = [

        r"RECEIPT DATE[: ]*(\d{1,2}/\d{1,2}/\d{4})",

        r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b",

        r"\b(\d{4}-\d{2}-\d{2})\b",

    ]



    # Try normal patterns first

    for pattern in date_patterns:

        m = re.search(pattern, text)

        if m:

            return m.group(1)



    # Special case: if there is a time (AM/PM), try to grab any nearby date

    if "PM" in text or "AM" in text:

        dm = re.search(r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b", text)

        if dm:

            return dm.group(1)



    return None





# -----------------------------

# MERCHANT EXTRACTION

# -----------------------------

def extract_merchant(text):

    # 1) Known brands (exact match shortcuts)

    merchant_keywords = {

        "walmart": "Walmart",

        "walgreens": "Walgreens",

        "target": "Target",

        "starbucks": "Starbucks",

        "mcdonald": "McDonald's",

        "costco": "Costco",

        "shell": "Shell",

        "7-eleven": "7-Eleven",

        "7 eleven": "7-Eleven",

        "cvs": "CVS",

        "kroger": "Kroger",

        "home depot": "Home Depot",

        "best buy": "Best Buy",

        "bag of beans": "Bag of Beans Cafe & Restaurant",

        "beans cafe": "Bag of Beans Cafe & Restaurant",

        "of beans cafe": "Bag of Beans Cafe & Restaurant",

    }



    lower = text.lower()

    for key, val in merchant_keywords.items():

        if key in lower:

            return val



    # 2) Split into lines

    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 2]



    best_line = None

    best_score = -999



    for idx, line in enumerate(lines[:8]):  # top lines only

        l = line.lower()

        score = 0



        # Give bonus if the line contains a business keyword

        biz_keywords = ["cafe", "restaurant", "coffee", "bar", "grill", "inc", "mart", "shop"]

        for kw in biz_keywords:

            if kw in l:

                score += 4



        # Penalize addresses

        if re.search(r"\d{3,}", l):

            score -= 2



        # Shorter business names score better

        score -= len(line) * 0.02



        # Uppercase lines tend to be business names

        if line.isupper():

            score += 2



        # First 2 lines get priority

        if idx <= 2:

            score += 2



        # Save the best-scoring line

        if score > best_score:

            best_score = score

            best_line = line.strip()



    # Remove extra junk after colon

    if ":" in best_line:

        best_line = best_line.split(":")[0].strip()



    return best_line






# -----------------------------

# MAIN PROCESSOR

# -----------------------------

def process_receipt(image_path):

    raw_text = extract_text(image_path)



    merchant = extract_merchant(raw_text)

    date = extract_date(raw_text)

    total = extract_total(raw_text)



    # Simple confidence score

    confidence = 0.0

    if merchant:

        confidence += 0.3

    if date:

        confidence += 0.3

    if total:

        confidence += 0.4

    confidence = min(1.0, confidence)



    return {

        "merchant_name": merchant,

        "receipt_date": date,

        "total_amount": total,

        "raw_text": raw_text,

        "confidence_score": confidence,

    }


