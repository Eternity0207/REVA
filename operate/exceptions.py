"""Custom exceptions"""

class ModelNotRecognizedException(Exception):
    def __init__(self, model, message="Model not recognized"):
        self.model = model
        self.message = message
        super().__init__(f"{message}: {model}")
