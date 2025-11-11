import easyocr
from loguru import logger

_reader = None

def initialize_ocr():
    """Initialize OCR reader"""
    global _reader
    if _reader is None:
        logger.info("Initializing OCR reader...")
        _reader = easyocr.Reader(["en"])
    return _reader

def extract_text(image, confidence_threshold=0.5):
    """Extract text from image"""
    reader = initialize_ocr()
    results = reader.readtext(image)
    texts = []
    for (bbox, text, confidence) in results:
        if confidence >= confidence_threshold:
            texts.append({"text": text, "confidence": confidence, "bbox": bbox})
    return texts
