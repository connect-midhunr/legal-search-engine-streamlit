from enum import Enum

class DocumentType(Enum):
    INTERIM_ORDER = "Interim Order"
    JUDGEMENT = "Judgement"

class Languages(Enum):
    ENGLISH = "en"
    HINDI = "hi"
    BENGALI = "bn"
    MARATHI = "mr"
    GUJARATI = "gu"
    TAMIL = "ta"
    TELUGU = "te"
    KANNADA = "kn"
    MALAYALAM = "ml"
    PUNJABI = "pa"
    ODIYA = "or"
    URDU = "ur"