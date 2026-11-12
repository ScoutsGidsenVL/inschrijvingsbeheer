from typing import TypeVar

from django.core.exceptions import MultipleObjectsReturned

from inschrijfbeheer.mapping.logic.mapper import Doelgegevens, MappingFout

from .synchronisatie import SynchronisatieActie, SynchronisatieInfo, SyncOnderdelen

N = TypeVar("N")


class InschrijfbeheerDatabank:
    def __init__(self, info: SynchronisatieInfo):
        self.info = info

    def bewaar(self, onderdelen: SyncOnderdelen[N], doel: Doelgegevens[N]) -> tuple[N, bool]:
        """Bewaart Doelgegevens en registreert de actie.

        Dit is de enige plek waar de synchronisatie naar de databank schrijft,
        zodat het tellen niet per model apart gebeurt en niet kan afwijken van
        wat er echt gebeurd is.

        Returns:
            tuple[N, bool]: het bewaarde object en of het aangemaakt werd
        """
        manager = onderdelen.model.objects
        pk_naam = onderdelen.model._meta.pk.name

        if doel.vervang_bestaande:
            filter_sleutels = doel.vervang_sleutels or doel.sleutels
            verouderd = manager.filter(**filter_sleutels)

            nieuwe_pk = doel.velden.get(pk_naam, doel.sleutels.get(pk_naam))
            if nieuwe_pk is not None:
                verouderd = verouderd.exclude(pk=nieuwe_pk)

            for bestaand in verouderd:
                bestaand.delete()
                self.info.registreer(onderdelen.model, SynchronisatieActie.VERWIJDERD)

        try:
            if onderdelen.enkel_aanmaken:
                bewaard, aangemaakt = manager.get_or_create(
                    **doel.sleutels,
                    defaults={**doel.velden},
                )
            else:
                bewaard, aangemaakt = manager.update_or_create(
                    **doel.sleutels, defaults=doel.velden
                )
        except MultipleObjectsReturned as fout:
            # De sleutels horen uniek te zijn, maar de databank bevat dubbels. Behandel dat
            # als onbruikbare data: de aanroeper slaat de rij over en de sync gaat verder.
            pks = list(manager.filter(**doel.sleutels).values_list("pk", flat=True))
            raise MappingFout(
                f"Meerdere {onderdelen.model.__name__} voor sleutels {doel.sleutels!r} "
                f"(pk's: {pks})"
            ) from fout

        if onderdelen.enkel_aanmaken:
            if aangemaakt:
                self.info.registreer(onderdelen.model, SynchronisatieActie.AANGEMAAKT)
            return bewaard, aangemaakt

        self.info.registreer(
            onderdelen.model,
            SynchronisatieActie.AANGEMAAKT if aangemaakt else SynchronisatieActie.BIJGEWERKT,
        )
        return bewaard, aangemaakt
