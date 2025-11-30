#!/usr/bin/env python3
"""
Create Test Receipt Image for Upload Testing
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_test_receipt_image():
    """Create a proper test receipt image"""
    
    # Create a white image
    width, height = 400, 600
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a better font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Receipt content
    receipt_lines = [
        "STARBUCKS COFFEE",
        "123 Main Street", 
        "Seattle, WA 98101",
        "",
        "Date: 12/15/2024",
        "Time: 07:23 AM",
        "",
        "Latte Grande     $5.25",
        "Croissant        $3.50", 
        "Tax              $0.70",
        "",
        "TOTAL           $9.45",
        "",
        "Card ending 1234",
        "Thank you!"
    ]
    
    # Draw the text
    y_position = 30
    for line in receipt_lines:
        if line == "STARBUCKS COFFEE" or line.startswith("TOTAL"):
            # Make headers bold/larger
            draw.text((20, y_position), line, fill='black', font=font)
            y_position += 35
        elif line == "":
            # Empty line spacing
            y_position += 20
        else:
            # Regular text
            draw.text((20, y_position), line, fill='black', font=small_font)
            y_position += 25
    
    # Save the image
    image_path = "/tmp/starbucks_receipt.jpg"
    image.save(image_path, "JPEG", quality=95)
    print(f"Created test receipt image: {image_path}")
    return image_path

def create_test_grocery_receipt():
    """Create a grocery receipt for variety"""
    
    width, height = 400, 700
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Grocery receipt content
    receipt_lines = [
        "WALMART SUPERCENTER",
        "SAVE MONEY. LIVE BETTER.",
        "",
        "Date: 12/16/2024",
        "",
        "Milk Organic 1 Gal    $4.98",
        "Bread Whole Wheat     $2.49", 
        "Eggs Dozen           $3.25",
        "Apples 3 lbs         $4.99",
        "Bananas              $1.89",
        "",
        "SUBTOTAL            $17.60",
        "TAX                 $1.41",
        "TOTAL              $19.01",
        "",
        "Visa ending 4567",
        "Thank you for shopping!"
    ]
    
    # Draw the text
    y_position = 25
    for line in receipt_lines:
        if line == "WALMART SUPERCENTER" or line.startswith("TOTAL"):
            draw.text((15, y_position), line, fill='black', font=font)
            y_position += 30
        elif line == "":
            y_position += 15
        else:
            draw.text((15, y_position), line, fill='black', font=small_font)
            y_position += 22
    
    image_path = "/tmp/walmart_receipt.jpg"
    image.save(image_path, "JPEG", quality=95)
    print(f"Created grocery receipt image: {image_path}")
    return image_path

if __name__ == "__main__":
    create_test_receipt_image()
    create_test_grocery_receipt()