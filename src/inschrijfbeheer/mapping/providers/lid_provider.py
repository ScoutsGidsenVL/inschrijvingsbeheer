"""Provider voor de ledenopzoeking via SOAP."""

from zeep.exceptions import Fault

from inschrijfbeheer.mapping.logic.mapper import Uitkomst
from inschrijfbeheer.utils.soap import LidGegevens, haal_lidgegevens

from .data_provider import ObjectProvider


class LidProvider(ObjectProvider[LidGegevens]):
    """Zoekt één lid op via zijn lid-id of lidnummer, de Groepsadministratie aanvaardt beide.

    Deze bron heeft geen lijstvariant, vandaar enkel ObjectProvider.
    """

    def haal_op(self, identifier: str) -> LidGegevens | None:
        return self.zoek_op(identifier).waarde

    def zoek_op(self, identifier: str) -> Uitkomst[LidGegevens]:
        """Zoekt het lid op en houdt de oorzaak bij als dat mislukt.

        Een SOAP-fault betekent dat de Groepsadministratie zelf antwoordde, meestal
        omdat ze het lid niet kent. Elke andere fout is technisch (timeout, WSDL,
        transport) en zegt niets over het lid.

        Deze provider logt zelf niets: de aanroeper logt de fout met zijn eigen context.
        """
        try:
            return Uitkomst(waarde=haal_lidgegevens(identifier))
        except Fault as fout:
            return Uitkomst(
                fout=f"Lidnummer {identifier} niet gevonden in de Groepsadministratie: {fout}"
            )
        except Exception as fout:
            return Uitkomst(
                fout=f"Groepsadministratie niet bereikbaar ({type(fout).__name__}): {fout}"
            )
