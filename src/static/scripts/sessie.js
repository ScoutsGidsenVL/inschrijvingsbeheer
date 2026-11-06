// Beheert de aanmelding op de achtergrond:
// - houdt je sessie bij Keycloak actief zolang je de applicatie gebruikt
// - waarschuwt als je niet meer aangemeld bent
// - laat je opnieuw aanmelden in een apart venster, zodat wat je op deze pagina
//   invulde niet verloren gaat
// - verstuurt een formulier pas als je nog aangemeld bent
//
// Het script onthoudt enkel óf je iets deed sinds de vorige verlenging (ja/nee).
// Wat je deed, wordt nergens bewaard of verstuurd.
(function () {
    "use strict";

    const script = document.currentScript;
    const STATUS_URL = script.dataset.statusUrl;
    const VERLENG_URL = script.dataset.verlengUrl;
    const AANMELD_URL = script.dataset.aanmeldUrl;

    const VERLENG_INTERVAL_MS = 10 * 60 * 1000; // ruim onder de 30 minuten SSO Session Idle
    const STATUS_INTERVAL_MS = 60 * 1000;
    const VERLENG_TIMEOUT_MS = 15 * 1000;
    const KANAAL = "inschrijvingsbeheer-sessie";

    const melding = document.getElementById("sessie-melding");
    let laatsteVerlenging = Date.now(); // het laden van de pagina telt als verlenging
    let frame = null;

    function toonMelding(tonen) {
        melding.hidden = !tonen;
    }

    // Vraagt de status op, zonder de sessie bij Keycloak te verlengen.
    // Geeft null terug als de server niet bereikbaar is: dan geen uitspraak.
    async function haalStatus() {
        try {
            const antwoord = await fetch(STATUS_URL, { cache: "no-store", credentials: "same-origin" });
            if (!antwoord.ok) return null;
            const status = await antwoord.json();
            // Na opnieuw aanmelden heeft Django een nieuw CSRF-token: zet het in de open formulieren
            for (const veld of document.querySelectorAll("input[name=csrfmiddlewaretoken]")) {
                veld.value = status.csrf;
            }
            toonMelding(!status.aangemeld);
            return status;
        } catch (fout) {
            return null;
        }
    }

    // Laadt VERLENG_URL in een verborgen iframe. SessionRefresh stuurt die stil langs
    // Keycloak (prompt=none) als het token verlopen is. Keycloak telt dat als activiteit.
    function verlengBijKeycloak() {
        laatsteVerlenging = Date.now();
        return new Promise((klaar) => {
            if (!frame) {
                frame = document.createElement("iframe");
                frame.hidden = true;
                document.body.appendChild(frame);
            }
            const timer = setTimeout(klaar, VERLENG_TIMEOUT_MS);
            frame.onload = () => {
                clearTimeout(timer);
                klaar();
            };
            frame.src = VERLENG_URL + "?t=" + Date.now();
        });
    }

    // Verlengt de sessie en controleert daarna of je nog aangemeld bent.
    // Bij twijfel (server onbereikbaar) blokkeert het niets.
    async function verlengEnControleer() {
        await verlengBijKeycloak();
        const status = await haalStatus();
        return status ? status.aangemeld : true;
    }

    // Activiteit verlengt de sessie, hoogstens om de VERLENG_INTERVAL_MS.
    // Na een lange pauze gebeurt de controle meteen bij de eerste activiteit.
    function bijActiviteit() {
        if (document.visibilityState !== "visible") return;
        if (Date.now() - laatsteVerlenging < VERLENG_INTERVAL_MS) return;
        verlengEnControleer();
    }
    for (const type of ["keydown", "pointerdown", "scroll"]) {
        addEventListener(type, bijActiviteit, { passive: true, capture: true });
    }

    // Detecteert een afmelding elders (bv. in Keycloak of een andere tab)
    setInterval(() => {
        if (document.visibilityState === "visible") haalStatus();
    }, STATUS_INTERVAL_MS);
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") haalStatus();
    });

    // Opnieuw aanmelden in een apart venster: deze pagina en wat je invulde blijven staan
    document.getElementById("sessie-aanmelden").addEventListener("click", () => {
        window.open(AANMELD_URL, "inschrijvingsbeheer-aanmelden", "popup,width=600,height=700");
    });
    new BroadcastChannel(KANAAL).onmessage = () => haalStatus();

    // Verstuur een POST-formulier pas als je nog aangemeld bent.
    // Anders blijft het formulier met je invoer staan en verschijnt de melding.
    const goedgekeurd = new WeakSet();
    document.addEventListener(
        "submit",
        async (gebeurtenis) => {
            const formulier = gebeurtenis.target;
            if (formulier.method.toLowerCase() !== "post" || goedgekeurd.has(formulier)) return;
            gebeurtenis.preventDefault();
            const knop = gebeurtenis.submitter;
            if (await verlengEnControleer()) {
                goedgekeurd.add(formulier);
                formulier.requestSubmit(knop);
            }
        },
        true
    );
})();
