def text_to_speech(text):
    """Convert text to speech"""
    try:
        from RealtimeTTS import TextToSpeechEngine
        engine = TextToSpeechEngine()
        engine.speak(text)
    except ImportError:
        print(f"[Voice] {text}")
