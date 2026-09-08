import re
import io
from pypdf import PdfReader
from typing import List, Dict, Any
from app.core.config import EXAM_CONFIG

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extracts text content from PDF file bytes."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    extracted = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            extracted.append(text)
    return "\n".join(extracted)

def parse_pdf_questions(pdf_text: str, exam_slug: str) -> List[Dict[str, Any]]:
    """
    Parses questions from extracted PDF text and assigns correct language
    according to exam rules:
    - Group 1 -> Tamil only ('ta')
    - Group 2 -> Tamil & English ('ta', 'en')
    - Group 4 -> Tamil only ('ta')
    """
    cfg = EXAM_CONFIG.get(exam_slug)
    allowed_langs = cfg["allowed_languages"] if cfg else ["ta"]

    # Split text into question blocks based on numbers (e.g., "1.", "Q1", "1)", "Q1.")
    blocks = re.split(r'\n(?=(?:Q?\d+[\.\)]|\d+\s*\.))\s*', pdf_text)

    parsed_items = []
    order = 1

    for block in blocks:
        block = block.strip()
        if not block or len(block) < 15:
            continue

        # Extract Question Text and Options A, B, C, D
        # Patterns for options: A), A., (A), Option A
        opt_pattern = r'(?:[\(\[]?[ABCD][\)\.\:]|Option\s+[ABCD][\:\.]?)\s*(.*?)(?=(?:[\(\[]?[ABCD][\)\.\:]|Option\s+[ABCD][\:\.]?|Answer|Correct|Explanation|\Z))'
        
        # Split Question vs Options
        opt_matches = list(re.finditer(opt_pattern, block, re.DOTALL | re.IGNORECASE))
        
        if len(opt_matches) >= 4:
            q_text = block[:opt_matches[0].start()].strip()
            # Clean leading numbers e.g. "1. " or "Q1: "
            q_text = re.sub(r'^(?:Q?\d+[\.\:\)]|\d+)\s*', '', q_text).strip()

            opts = [m.group(1).strip() for m in opt_matches[:4]]
            
            # Look for Answer key e.g. "Answer: A" or "Correct: B"
            ans_match = re.search(r'(?:Answer|Correct|Key)[\:\s]*([ABCD])', block, re.IGNORECASE)
            correct_opt = ans_match.group(1).upper() if ans_match else "A"

            # Look for Explanation
            exp_match = re.search(r'(?:Explanation|Solution|Notes)[\:\s]*(.*)', block, re.IGNORECASE | re.DOTALL)
            explanation = exp_match.group(1).strip() if exp_match else None

            # Detect language or assign default allowed language
            # Check if block contains English ASCII letters
            is_english = len(re.findall(r'[a-zA-Z]', block)) > len(re.findall(r'[\u0B80-\u0BFF]', block))
            
            lang = "en" if is_english else "ta"
            if lang not in allowed_langs:
                lang = allowed_langs[0]  # Force to allowed language (e.g. 'ta' for Group 1 & 4)

            parsed_items.append({
                "question_order": order,
                "language": lang,
                "question_text": q_text,
                "option_a": opts[0],
                "option_b": opts[1],
                "option_c": opts[2],
                "option_d": opts[3],
                "correct_option": correct_opt,
                "explanation": explanation,
                "source": "PDF"
            })
            order += 1

    # Fallback sample if text parsing was too loose
    if not parsed_items:
        lang = allowed_langs[0]
        parsed_items.append({
            "question_order": 1,
            "language": lang,
            "question_text": "PDF Extracted Sample Question: " + (pdf_text[:100] if pdf_text else "Question text"),
            "option_a": "Option A",
            "option_b": "Option B",
            "option_c": "Option C",
            "option_d": "Option D",
            "correct_option": "A",
            "explanation": "Extracted from uploaded PDF document.",
            "source": "PDF"
        })

    return parsed_items
