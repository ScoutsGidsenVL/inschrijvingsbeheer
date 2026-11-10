from datetime import date

from django import template
from django.utils.formats import date_format

register = template.Library()


@register.filter
def is_boolean(waarde):
    return isinstance(waarde, bool)


@register.filter
def is_none(waarde):
    return waarde is None


@register.simple_tag(takes_context=True)
def sorteer_url(context, kolom):
    """Geeft de querystring terug voor een link die op `kolom` sorteert,
    of de sortering omdraait als er al op `kolom` gesorteerd wordt."""
    request = context["request"]
    huidig = request.GET.get("sorteer", "") or context.get("standaard_sortering", "")

    nieuw = f"-{kolom}" if huidig == kolom else kolom

    params = request.GET.copy()
    params["sorteer"] = nieuw
    return "?" + params.urlencode()


@register.simple_tag(takes_context=True)
def sorteer_icoon(context, kolom):
    """Toont een pijltje als er op `kolom` gesorteerd wordt."""
    huidig = context["request"].GET.get("sorteer", "") or context.get("standaard_sortering", "")
    if huidig == kolom:
        return "↑"
    elif huidig == f"-{kolom}":
        return "↓"
    return "⇵"


@register.filter
def formateer_iso_datum(waarde):
    """Toont een ISO-datumstring (jjjj-mm-dd) in het standaard datumformaat.
    Een lege of onleesbare waarde komt ongewijzigd terug.

    Enkel de eerste 10 tekens tellen: zeep kan een tijdzone of tijd meegeven
    (bv. "1990-05-12+02:00" of "1990-05-12T00:00:00"), wat fromisoformat
    voor een date niet aanvaardt."""
    if not waarde:
        return waarde
    try:
        return date_format(date.fromisoformat(str(waarde)[:10]), "DATE_FORMAT")
    except (TypeError, ValueError):
        return waarde
