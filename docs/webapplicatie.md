# Webapplicatie

Deze component heeft als doel om de data in de databank te visualiseren en bepaalde handelingen te doen.

## Uitvoeren

Om de applicatie uit te voeren moet men het onderstaande command uitvoeren

```shell
> cd src/
> python manage.py runserver 2197
```

## Structuur

De applicatie verdeelt de verantwoordelijkheden voor de paden van de URLs onder enkele verschillenden modules in [inschrijfbeheer/urls](../src/inschrijfbeheer/urls/). Daarbovenop zijn er enkele speciale regels voorzien voor simpele paden en afwijkende noden. Hieronder de voornaamste paden en waar de verantwoordelijkheid ligt.

| Pad | Verantwoordelijkheid |
|-----|----------------------|
| /oidc | django-oidc-auth |
| /sessie | sessie afstemmen op Keycloak: afmelden, verlengen, status (zie [Toegang](#toegang)) |
| /geen-toegang | pagina voor wie niet aangemeld is of geen toegang heeft |
| /docs | wordt rechtstreeks doorverwezen naar de [README](./README.md) of een bestand [docs](./) |
| /logs | wordt rechtstreeks afgehandeld door log_lijst (slechts één pad) |
| /evenementen | wordt afgehandeld door [evenementen_urls.py](../src/inschrijfbeheer/urls/evenementen_urls.py) |
| /deelnemers | wordt afgehandeld door [deelnemers_urls.py](../src/inschrijfbeheer/urls/deelnemers_urls.py) |
| /inschrijvingen | wordt afgehandeld door [inschrijvingen_urls.py](../src/inschrijfbeheer/urls/inschrijvingen_urls.py) |
| /handleidingen | wordt afgehandeld door [handleidingen_urls.py](../src/inschrijfbeheer/urls/handleidingen_urls.py) |

Voor `/evenementen`, `/deelnemers` en `/inschrijvingen` worden de views vervolgens gedefinieerd in de corresponderende module in [inschrijfbeheer/views](../src/inschrijfbeheer/views/).

Deze views maken voor het merendeel gebruik van templates gevonden in [templates](../src/templates/). Deze templates maken gebruik van stylesheets in de directory [static](../src/static/). Deze directory bevat alle statische bestanden zoals stylesheets, afbeeldingen, scripts.

## Toegang

- Je meldt aan via Keycloak (Login). Enkel personeel krijgt toegang: groep `X1027G` met de verantwoordelijkheid `personeel` in Groepsadmin.
- Die controle gebeurt bij het aanmelden en daarna opnieuw op elke pagina via `check_rollen` in [utils/auth.py](../src/inschrijfbeheer/utils/auth.py). Een geslaagde controle blijft 5 minuten geldig in de sessie.
- Alle pagina's vragen aanmelding, ook `/docs` en `/handleidingen`. Enkel `/geen-toegang`, `/oidc` en de statische bestanden zijn publiek.
- Wie geen personeel is, wordt niet bewaard in de databank.
- Meld je af bij Keycloak, dan laadt Keycloak `/sessie/afmelden/` in een verborgen iframe en word je ook hier afgemeld. Daarnaast controleert `SessionRefresh` elke minuut of je sessie bij Keycloak nog geldig is.
- [scripts/sessie.js](../src/static/scripts/sessie.js), geladen in `base.html`, regelt de aanmelding op de achtergrond:
  - Zolang je de applicatie gebruikt, blijft je sessie bij Keycloak actief, ook zonder nieuwe pagina te laden. Druk je een toets in, klik of scrol je terwijl de tab zichtbaar is, en is de laatste verlenging meer dan 10 minuten geleden, dan laadt het script `/sessie/verleng/` in een verborgen iframe. Doe je 30 minuten niets, dan verloopt je sessie zoals ingesteld in Keycloak.
  - Elke minuut vraagt het `/sessie/status/` op. Die vraag verlengt de sessie niet. Ben je niet meer aangemeld, dan verschijnt een melding met de knop **Opnieuw aanmelden**. Die opent de aanmelding in een apart venster, zodat wat je invulde blijft staan. Na de aanmelding sluit dat venster zichzelf en verdwijnt de melding.
  - Een formulier met POST wordt pas verstuurd als je nog aangemeld bent. Anders blijft het formulier staan en verschijnt de melding. Na opnieuw aanmelden zet het script het nieuwe CSRF-token in de formulieren.
  - Het script onthoudt enkel óf je iets deed sinds de vorige verlenging. Wat je deed, wordt nergens bewaard of verstuurd.
