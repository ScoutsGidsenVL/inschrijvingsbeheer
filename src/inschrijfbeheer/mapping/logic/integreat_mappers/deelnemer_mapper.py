from inschrijfbeheer.mapping.logic.mapper import Doelgegevens, Mapper, MappingFout
from inschrijfbeheer.models import (
    Deelnemer,
    IntegreatParticipant,
)
from inschrijfbeheer.utils.soap import LidGegevens

from .integreat_mapper import tekst


class IntegreatDeelnemerMapper(Mapper[IntegreatParticipant, LidGegevens | None, Deelnemer]):
    """Deelnemer uit een Integreat-deelnemer plus de ledenopzoeking.

    lid is het resultaat van de SOAP-opzoeking, of None als de opzoeking niets
    opleverde. Anders dan bij Weez wordt er hier geen deelnemer met foutboodschap
    bewaard, want bij een migratie wil je geen half ingevulde leden aanmaken. De
    inschrijving wordt dan overgeslagen.
    """

    def map(self, bron: IntegreatParticipant, lid: LidGegevens | None) -> Doelgegevens[Deelnemer]:
        lid_id = tekst(bron.lid_id)
        if not lid_id:
            raise MappingFout("deelnemer zonder lid-id")
        if lid is None:
            raise MappingFout(f"geen ledengegevens gevonden voor lid-id {lid_id}")

        return Doelgegevens(
            sleutels={"id": lid_id},
            velden={
                "voornaam": tekst(lid.voornaam),
                "achternaam": tekst(lid.naam),
                "mailadres": tekst(lid.emailadres),
            },
        )
