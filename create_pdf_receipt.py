#!/usr/bin/env python3
"""
Create Test PDF Receipt
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_pdf_like_receipt():
    """Create a PDF-like receipt image and save as PDF"""
    
    # Create receipt image
    width, height = 400, 650
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Netflix subscription receipt
    receipt_lines = [
        "NETFLIX",
        "Streaming Service",
        "",
        "Invoice Date: 12/15/2024",
        "Subscription Period:",
        "Dec 15, 2024 - Jan 15, 2025",
        "",
        "Netflix Standard Plan",
        "Monthly Subscription   $15.99",
        "",
        "TOTAL               $15.99",
        "",
        "Auto-charged to card ending 1234",
        "Thank you for your subscription!"
    ]
    
    # Draw the text
    y_position = 30
    for line in receipt_lines:
        if line == "NETFLIX" or line.startswith("TOTAL"):
            draw.text((20, y_position), line, fill='black', font=font)
            y_position += 35
        elif line == "":
            y_position += 20
        else:
            draw.text((20, y_position), line, fill='black', font=small_font)
            y_position += 25
    
    # Save as both JPG and convert to PDF
    jpg_path = "/tmp/netflix_receipt.jpg"
    pdf_path = "/tmp/netflix_receipt.pdf"
    
    image.save(jpg_path, "JPEG", quality=95)
    
    # Convert to PDF
    try:
        image.save(pdf_path, "PDF")
        print(f"Created PDF receipt: {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"Could not create PDF: {str(e)}")
        return None

if __name__ == "__main__":
    create_pdf_like_receipt()