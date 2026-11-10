"""Datumformaten voor de hele applicatie (dd/mm/jjjj).

Geladen via FORMAT_MODULE_PATH in config/settings.py. De map heet `en` omdat
LANGUAGE_CODE op "en-us" staat en Django daarvoor `en_US` en daarna `en` zoekt.
"""

DATE_FORMAT = "d/m/Y"
SHORT_DATE_FORMAT = "d/m/Y"
DATETIME_FORMAT = "d/m/Y H:i"
SHORT_DATETIME_FORMAT = "d/m/Y H:i"
