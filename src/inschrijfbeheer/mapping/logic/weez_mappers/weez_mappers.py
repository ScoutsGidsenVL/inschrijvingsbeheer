"""Mappers van de Weezevent-brondata naar de Inschrijfbeheer-modellen.

Elke mapper hier is een zuivere functie van brondata plus context naar
Doelgegevens. Geen databankwerk, geen tellers, geen netwerkaanroepen. Wat niet
omzetbaar is, wordt een MappingFout.

De controleregels rond lidnummers staan bewust buiten de mappers, in
los_lid_op(), omdat dat synchronisatiebeleid is en geen omzetting.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import NamedTuple
from zoneinfo import ZoneInfo

from django.utils import timezone

from inschrijfbeheer.mapping.logic.mapper import Uitkomst
from inschrijfbeheer.mapping.providers.lid_provider import LidProvider
from inschrijfbeheer.utils.soap import LidGegevens

logger = logging.getLogger("inschrijfbeheer")

EVENT_TIJDZONE = ZoneInfo("Europe/Brussels")


class Veld(NamedTuple):
    """Een verplicht veld uit het Weez-formulier."""

    attribuut: str  # attribuut in InschrijvingsGegevens
    naam: str  # veldnaam die de gebruiker kent, voor foutmeldingen


# Weez-label van elke verplichte vraag. Een nieuw verplicht veld voeg je enkel hier toe
# (plus het attribuut in InschrijvingsGegevens).
VERPLICHTE_VELDEN = {
    "lidnummer": Veld("lidnummer", "lidnummer"),
    "first name": Veld("voornaam", "voornaam"),
    "last name": Veld("achternaam", "achternaam"),
    "email": Veld("mailadres", "e-mailadres"),
    "date of birth": Veld("geboortedatum", "geboortedatum"),
}
VERPLICHTE_VRAGEN = set(VERPLICHTE_VELDEN)
LIDNUMMER_LENGTE = 13


def parse_datetime(waarde: str | None) -> datetime | None:
    """Zet een Weez-tijdstip zonder tijdzone om naar een bewust tijdstip."""
    if not waarde:
        return None
    try:
        tijdstip = datetime.fromisoformat(waarde.replace("Z", "+00:00"))
    except ValueError:
        return None
    if timezone.is_naive(tijdstip):
        return timezone.make_aware(tijdstip, EVENT_TIJDZONE)
    return tijdstip


@dataclass
class InschrijvingsGegevens:
    """De ledengegevens zoals de deelnemer ze zelf invulde in het formulier."""

    lidnummer: str = ""
    voornaam: str = ""
    achternaam: str = ""
    mailadres: str = ""
    geboortedatum: datetime = datetime.now()


def check_verplichte_vragen(vragen: list[dict] | None) -> tuple[bool, set]:
    """Controleert of het formulier alle verplichte vragen bevat."""
    labels = {
        (vraag.get("question") or "").lower() for vraag in vragen or [] if vraag.get("question")
    }
    return VERPLICHTE_VRAGEN.issubset(labels), VERPLICHTE_VRAGEN.difference(labels)


def bepaal_inschrijvingsgegevens(vragen: list[dict] | None) -> Uitkomst[InschrijvingsGegevens]:
    """Haalt de ledengegevens uit de antwoorden van een deelnemer.

    Geeft een fout zonder waarde terug wanneer niet precies vijf verplichte antwoorden
    ingevuld zijn, want dan valt er geen deelnemer van te maken. De reden noemt
    welke velden ontbreken en welke dubbel ingevuld zijn.
    """
    gegevens = InschrijvingsGegevens()
    ingevuld = dict.fromkeys(VERPLICHTE_VELDEN, 0)

    for vraag in vragen or []:
        waarde = str(vraag.get("answer") or "").strip()
        if not waarde:
            continue

        label = (vraag.get("question") or "").lower()
        veld = VERPLICHTE_VELDEN.get(label)
        if veld is None:
            continue
        setattr(gegevens, veld.attribuut, waarde)
        ingevuld[label] += 1

    if sum(ingevuld.values()) == len(VERPLICHTE_VRAGEN):
        return Uitkomst(waarde=gegevens)

    ontbrekend = [VERPLICHTE_VELDEN[label].naam for label, n in ingevuld.items() if n == 0]
    dubbel = [VERPLICHTE_VELDEN[label].naam for label, n in ingevuld.items() if n > 1]
    redenen = []
    if ontbrekend:
        redenen.append(f"ontbrekend: {', '.join(ontbrekend)}")
    if dubbel:
        redenen.append(f"dubbel ingevuld: {', '.join(dubbel)}")
    return Uitkomst(fout="; ".join(redenen))


def reden_ongeldig_lidnummer(lidnummer: str) -> str:
    """Geeft aan waarom een lidnummer ongeldig is, of een lege string als het geldig is."""
    if not lidnummer:
        return "leeg"
    if not lidnummer.isnumeric():
        return "bevat andere tekens dan cijfers"
    if len(lidnummer) != LIDNUMMER_LENGTE:
        return f"{len(lidnummer)} cijfers, verwacht {LIDNUMMER_LENGTE}"
    return ""


def _gelijk(a: str | None, b: str | None) -> bool:
    """Vergelijkt twee waarden zonder witruimte errond en zonder onderscheid in hoofdletters."""
    return (a or "").strip().casefold() == (b or "").strip().casefold()


def los_lid_op(provider: LidProvider, gegevens: InschrijvingsGegevens) -> Uitkomst[LidGegevens]:
    """Zoekt het lid op en past de controleregels toe.

    De uitkomst dient als context voor WeezDeelnemerMapper. Een fout wordt op de
    deelnemer bewaard, zodat iemand het achteraf kan rechtzetten.
    """
    reden = reden_ongeldig_lidnummer(gegevens.lidnummer)
    if reden:
        return Uitkomst(fout=f"Ongeldig lidnummer ({reden}): {gegevens.lidnummer}")

    opzoeking = provider.zoek_op(gegevens.lidnummer)
    lidgegevens = opzoeking.waarde
    if lidgegevens is None:
        # De fout van de provider noemt het lid niet, de deelnemerpagina heeft het nummer nodig.
        return Uitkomst(fout=f"Lidnummer {gegevens.lidnummer}: {opzoeking.fout}")

    overeenkomsten = {
        "voornaam": _gelijk(lidgegevens.voornaam, gegevens.voornaam),
        "achternaam": _gelijk(lidgegevens.naam, gegevens.achternaam),
        "e-mailadres": _gelijk(lidgegevens.emailadres, gegevens.mailadres),
        "geboortedatum": datetime.strptime(lidgegevens.geboortedatum, "%Y-%m-%d")
        == datetime.strptime(gegevens.geboortedatum, "%d/%m/%Y"),
        "lidnummer": _gelijk(lidgegevens.lidnummer, gegevens.lidnummer),
    }

    if sum(overeenkomsten.values()) < 3:
        afwijkend = [veld for veld, gelijk in overeenkomsten.items() if not gelijk]
        return Uitkomst(
            fout=(
                f"Onvoldoende overeenkomende velden ({gegevens.lidnummer}), "
                f"afwijkend: {', '.join(afwijkend)}"
            )
        )

    return opzoeking
