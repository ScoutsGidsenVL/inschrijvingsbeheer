"""Views rond aanmelden en afmelden"""

import logging

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.clickjacking import xframe_options_exempt

logger = logging.getLogger("inschrijfbeheer")


@never_cache
@xframe_options_exempt
def frontchannel_logout(request: HttpRequest) -> HttpResponse:
    """Front-channel logout van Keycloak, voor `/sessie/afmelden/`

    Bij het afmelden laadt Keycloak deze URL in een iframe, met `iss` en `sid`
    als parameters. Komen ze overeen met de sessie, dan wordt de gebruiker ook
    hier afgemeld. Het antwoord is altijd leeg.

    Args:
        request (HttpRequest): HTTP request van de iframe van Keycloak

    Returns:
        HttpResponse: een lege response
    """
    iss = request.GET.get("iss")
    sid = request.GET.get("sid")

    if (
        request.user.is_authenticated
        and iss == settings.KEYCLOAK_REALM_URL
        and sid
        and sid == request.session.get("oidc_sid")
    ):
        logger.info("Gebruiker %s afgemeld via Keycloak", request.user)
        auth.logout(request)

    return HttpResponse(status=200)


@never_cache
@xframe_options_exempt
def sessie_verlengen(request: HttpRequest) -> HttpResponse:
    """Heartbeat voor `/sessie/verleng/`, geladen in een verborgen iframe

    Het werk gebeurt in de SessionRefresh-middleware: is het ID token verlopen,
    dan stuurt die de iframe stil langs Keycloak (prompt=none) en terug naar
    hier. Keycloak telt dat als activiteit, waardoor de SSO-sessie niet
    verloopt zolang je de applicatie gebruikt. Deze view geeft enkel een lege
    pagina terug.

    Args:
        request (HttpRequest): HTTP request van de verborgen iframe

    Returns:
        HttpResponse: een lege response
    """
    return HttpResponse(status=200)


@never_cache
def sessie_status(request: HttpRequest) -> JsonResponse:
    """Status van de aanmelding voor `/sessie/status/`, gebruikt door `scripts/sessie.js`

    Staat in OIDC_EXEMPT_URLS: deze controle verlengt de sessie bij Keycloak niet.
    Het CSRF-token zit erbij omdat Django bij een nieuwe aanmelding een nieuw token
    maakt. Het script zet dat in de formulieren die al open staan.

    Args:
        request (HttpRequest): HTTP request van het script

    Returns:
        JsonResponse: `aangemeld` (bool) en `csrf` (het huidige CSRF-token)
    """
    return JsonResponse({"aangemeld": request.user.is_authenticated, "csrf": get_token(request)})


@login_required
def sessie_aangemeld(request: HttpRequest) -> HttpResponse:
    """Landingspagina na opnieuw aanmelden in een apart venster, voor `/sessie/aangemeld/`

    De pagina verwittigt de andere tabs van de applicatie en sluit zichzelf.

    Args:
        request (HttpRequest): HTTP request na de aanmelding

    Returns:
        HttpResponse: de pagina
    """
    return render(request, "sessie_aangemeld.html")


def geen_toegang(request: HttpRequest) -> HttpResponse:
    """Pagina voor wie niet aangemeld is of geen toegang heeft, voor `/geen-toegang/`

    Args:
        request (HttpRequest): HTTP request voor de pagina

    Returns:
        HttpResponse: de pagina met een knop om aan te melden
    """
    return render(request, "geen_toegang.html")
