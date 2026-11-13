"""Provider voor de ledenopzoeking via SOAP."""

from zeep.exceptions import Fault

from inschrijfbeheer.mapping.logic.mapper import Uitkomst
from inschrijfbeheer.utils.soap import LidGegevens, haal_lidgegevens


class LidProvider:
    """Zoekt één lid op via zijn lid-id of lidnummer, de Groepsadministratie aanvaardt beide.

    zoek_op() geeft een Uitkomst terug met de reden van een mislukte opzoeking, in
    plaats van enkel None zoals DataProvider.haal_op().
    """

    def zoek_op(self, identifier: str) -> Uitkomst[LidGegevens]:
        """Zoekt het lid op en houdt de oorzaak bij als dat mislukt.

        Een SOAP-fault betekent dat de Groepsadministratie zelf antwoordde, meestal
        omdat ze het lid niet kent. Elke andere fout is technisch (timeout, WSDL,
        transport) en zegt niets over het lid.

        Deze provider logt zelf niets en de fout bevat geen identifier: de aanroeper
        voegt die context zelf toe.
        """
        try:
            return Uitkomst(waarde=haal_lidgegevens(identifier))
        except Fault as fout:
            return Uitkomst(fout=f"Lid niet gevonden in de Groepsadministratie ({fout})")
        except Exception as fout:
            return Uitkomst(
                fout=f"Groepsadministratie niet bereikbaar ({type(fout).__name__}: {fout})"
            )
