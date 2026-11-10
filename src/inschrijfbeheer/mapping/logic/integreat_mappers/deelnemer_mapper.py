from typing import Any

from inschrijfbeheer.mapping.logic.mapper import Doelgegevens, Mapper, MappingFout
from inschrijfbeheer.models import (
    Deelnemer,
    IntegreatParticipant,
)

from .integreat_mapper import tekst


class IntegreatDeelnemerMapper(Mapper[IntegreatParticipant, Any, Deelnemer]):
    """Deelnemer uit een Integreat-deelnemer plus de ledenopzoeking.

    De context is het LidGegevens-object uit de SOAP-opzoeking, of None als de
    opzoeking niets opleverde. Anders dan bij Weez wordt er hier geen deelnemer
    met foutboodschap bewaard, want bij een migratie wil je geen half
    ingevulde leden aanmaken. De inschrijving wordt dan overgeslagen.
    """

    def map(self, bron: IntegreatParticipant, context: Any) -> Doelgegevens[Deelnemer]:
        lid_id = tekst(bron.lid_id)
        if not lid_id:
            raise MappingFout("deelnemer zonder lid-id")
        if context is None:
            raise MappingFout(f"geen ledengegevens gevonden voor lid-id {lid_id}")

        return Doelgegevens(
            sleutels={"id": lid_id},
            velden={
                "voornaam": tekst(context.voornaam),
                "achternaam": tekst(context.naam),
                "mailadres": tekst(context.emailadres),
            },
        )
