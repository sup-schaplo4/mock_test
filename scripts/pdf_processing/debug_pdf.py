# debug_extraction.py
import pdfplumber
import re
import json


pdf_path = "rbi_pdf/RBI_PYP_PHASE_01_2023_General_Awareness_Questions.pdf"

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    print("="*80)
    
    # Let's focus on page 2 where we saw Q.1)
    if len(pdf.pages) > 1:
        page = pdf.pages[1]  # Page 2 (0-indexed)
        text = page.extract_text()
        
        print("RAW TEXT FROM PAGE 2:")
        print("-"*80)
        print(text)
        print("-"*80)
        
        # Save raw text to file for inspection
        with open('page2_raw.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        print("✅ Saved raw text to page2_raw.txt")
        
        # Try to find Q.1) and see what's around it
        print("🔍 SEARCHING FOR Q.1):")
        print("-"*40)
        
        # Find position of Q.1)
        q1_pos = text.find('Q.1)')
        if q1_pos != -1:
            print(f"Found Q.1) at position {q1_pos}")
            print("Text around Q.1) (100 chars before and 500 after):")
            print("-"*40)
            start = max(0, q1_pos - 100)
            end = min(len(text), q1_pos + 500)
            snippet = text[start:end]
