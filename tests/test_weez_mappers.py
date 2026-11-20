"""Unit tests voor de zuivere functies van de Weez-mappers, zonder databank of netwerk."""

from datetime import datetime

from inschrijfbeheer.mapping.logic.weez_mappers.weez_mappers import (
    EVENT_TIJDZONE,
    bepaal_inschrijvingsgegevens,
    parse_datetime,
    reden_ongeldig_lidnummer,
)


def test_reden_ongeldig_lidnummer():
    assert reden_ongeldig_lidnummer("1234567890123") == ""
    assert reden_ongeldig_lidnummer("") == "leeg"
    assert reden_ongeldig_lidnummer("12345abc") == "bevat andere tekens dan cijfers"
    assert reden_ongeldig_lidnummer("123") == "3 cijfers, verwacht 13"


def test_bepaal_inschrijvingsgegevens():
    vragen = [
        {"question": "Lidnummer", "answer": "1234567890123"},
        {"question": "First name", "answer": " Jo "},
        {"question": "Last name", "answer": "Peeters"},
        {"question": "Email", "answer": "jo@example.org"},
        {"question": "Date of birth", "answer": "01/02/2010"},
        {"question": "Allergieën", "answer": "geen"},
    ]

    volledig = bepaal_inschrijvingsgegevens(vragen)
    zonder_mail = bepaal_inschrijvingsgegevens([v for v in vragen if v["question"] != "Email"])

    assert volledig.fout == ""
    assert volledig.waarde.voornaam == "Jo"
    assert volledig.waarde.lidnummer == "1234567890123"
    assert zonder_mail.waarde is None
    assert zonder_mail.fout == "ontbrekend: e-mailadres"


def test_parse_datetime():
    verwacht = datetime(2026, 7, 14, 9, 30, tzinfo=EVENT_TIJDZONE)

    assert parse_datetime("2026-07-14T09:30:00") == verwacht
    assert parse_datetime("geen datum") is None
    assert parse_datetime(None) is None
