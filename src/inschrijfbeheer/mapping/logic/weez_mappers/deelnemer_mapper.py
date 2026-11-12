from inschrijfbeheer.mapping.logic.mapper import Doelgegevens, Mapper, Uitkomst
from inschrijfbeheer.models import (
    Deelnemer,
)

from inschrijfbeheer.utils.soap import LidGegevens

from .weez_mappers import InschrijvingsGegevens


class WeezDeelnemerMapper(Mapper[InschrijvingsGegevens, Uitkomst[LidGegevens], Deelnemer]):
    """Deelnemer uit de ingevulde ledengegevens plus de opzoeking.

    Leverde de opzoeking niets op, dan wordt er een deelnemer bewaard op naam
    en mailadres, met een foutboodschap. Zo gaat de inschrijving niet verloren
    en kan iemand ze achteraf rechtzetten.
    """

    def map(
        self, bron: InschrijvingsGegevens, context: Uitkomst[LidGegevens]
    ) -> Doelgegevens[Deelnemer]:
        if context.waarde is None:
            return Doelgegevens(
                sleutels={
                    "voornaam": bron.voornaam,
                    "achternaam": bron.achternaam,
                    "mailadres": bron.mailadres,
                },
                velden={"foutboodschap": context.fout},
            )

        lid = context.waarde
        return Doelgegevens(
            sleutels={"id": lid.id},
            velden={
                "voornaam": lid.voornaam,
                "achternaam": lid.naam,
                "mailadres": lid.emailadres,
            },
        )
