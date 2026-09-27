import frappe
import requests
from frappe import _
from frappe.utils import cint, flt, strip_html

REQUEST_TIMEOUT = 30

# Correspondance modes de paiement ERPNext -> e-MECeF (PaymentTypeEnum)
PAYMENT_MODE_MAP = {
    "Cash": "ESPECES",
    "Bank Draft": "VIREMENT",
    "Bank": "VIREMENT",
    "Wire Transfer": "VIREMENT",
    "Credit Card": "CARTEBANCAIRE",
    "Debit Card": "CARTEBANCAIRE",
    "Mobile Money": "MOBILEMONEY",
    "Cheque": "CHEQUES",
    "Customer Credit": "CREDIT",
}


def get_mecef_settings(company, required=True):
    """Charge MeCef Settings pour une société. Soft-disable → None si required=False.

    """
    if not company:
        if required:
            frappe.throw(_("Société manquante pour MeCef Settings."))
        return None

    settings = None
    if frappe.db.exists("MeCef Settings", company):
        settings = frappe.get_doc("MeCef Settings", company)
        if not cint(settings.is_active):
            settings = None

    if settings is None:
        if required:
            frappe.throw(
                _("MeCef Settings non configuré pour la société {0}.").format(company)
            )
        return None

    if required and (not settings.api_key or not settings.host or not settings.ifu):
        frappe.throw(
            _("Veuillez configurer l'IFU, l'hôte et la clé API dans 'MeCef Settings'.")
        )
    return settings


def get_mecef_settings_by_ifu(ifu, required=True):
    """Charge le MeCef Settings actif correspondant à un IFU (proxy FACNO)."""
    ifu = (ifu or "").strip()
    if not ifu:
        if required:
            frappe.throw(_("IFU manquant pour MeCef Settings."))
        return None

    name = frappe.db.get_value(
        "MeCef Settings",
        {"ifu": ifu, "is_active": 1},
        "name",
    )
    if not name:
        if required:
            frappe.throw(
                _("Aucun MeCef Settings actif pour l'IFU {0}.").format(ifu)
            )
        return None

    settings = frappe.get_doc("MeCef Settings", name)
    if required and (not settings.api_key or not settings.host or not settings.ifu):
        frappe.throw(
            _("Veuillez configurer l'hôte et la clé API dans 'MeCef Settings' (IFU {0}).").format(
                ifu
            )
        )
    return settings


def get_tax_group_for_item(item):
    """
    Retourne le groupe de taxe MECeF (A-F) pour une ligne de facture.

    Le groupe est porté par l'Item Tax Template lié à l'article (champ
    personnalisé `mecef_tax_group`). Un article sans modèle est considéré
    exonéré (groupe A).
    """
    tax_template = _resolve_item_tax_template(item)
    if tax_template:
        group = frappe.get_cached_value(
            "Item Tax Template", tax_template, "mecef_tax_group"
        )
        if group:
            return group
    return "A"  # Groupe A par défaut (exonéré)


def _resolve_item_tax_template(item):
    """Modèle de taxe d'une ligne : celui de la ligne, sinon celui par défaut
    défini sur la fiche article."""
    tax_template = item.get("item_tax_template")
    if not tax_template and item.get("item_code"):
        tax_template = frappe.db.get_value(
            "Item Tax",
            {"parent": item.get("item_code"), "parenttype": "Item"},
            "item_tax_template",
        )
    return tax_template


def get_item_tax_rate(item):
    """Taux de taxe total (%) applicable à l'article, depuis son Item Tax
    Template (ex. 18 pour la TVA groupe B, 0 si exonéré)."""
    tax_template = _resolve_item_tax_template(item)
    if not tax_template:
        return 0.0
    rows = frappe.get_all(
        "Item Tax Template Detail",
        filters={"parent": tax_template},
        fields=["tax_rate"],
    )
    return sum(flt(r.tax_rate) for r in rows)


def build_invoice_payload(doc, settings):
    """Construit le payload JSON conforme à l'API e-MECeF (InvoiceRequestDataDto)."""
    payload = {
        "ifu": settings.ifu,
        "type": "FA" if doc.is_return else (settings.invoice_type or "FV"),
        "items": [],
    }

    # e-MECeF attend un prix unitaire TTC (taxe comprise). Si les prix ERPNext
    # sont HT (taxe exclusive), on ajoute la taxe ; s'ils sont déjà TTC (taxe
    # incluse dans le prix), on les envoie tels quels.
    prices_are_ttc = any(
        t.get("included_in_print_rate") for t in (doc.get("taxes") or [])
    )

    # Articles
    for item in doc.items:
        tax_rate = get_item_tax_rate(item)
        factor = 1.0 if prices_are_ttc else (1 + tax_rate / 100.0)

        unit_price = int(round(flt(item.rate) * factor))
        item_dto = {
            "name": item.item_name,
            "price": unit_price,
            "quantity": flt(item.qty),
            "taxGroup": get_tax_group_for_item(item),
        }
        if item.item_code:
            item_dto["code"] = item.item_code

        # Prix d'origine (avant remise), converti en TTC de la même façon
        original_ht = flt(item.price_list_rate) or (
            flt(item.rate) + flt(item.discount_amount)
        )
        original_price = int(round(original_ht * factor))
        if original_price > unit_price:
            item_dto["originalPrice"] = original_price
            item_dto["priceModification"] = _("Remise {0} FCFA").format(original_price - unit_price)

        payload["items"].append(item_dto)

    # Client (acheteur) - optionnel
    client = {}
    if doc.get("tax_id"):
        client["ifu"] = doc.tax_id
    if doc.get("customer_name"):
        client["name"] = doc.customer_name
    contact = ", ".join(
        [v for v in [doc.get("contact_mobile"), doc.get("contact_email")] if v]
    )
    if contact:
        client["contact"] = contact
    if doc.get("address_display"):
        client["address"] = strip_html(doc.address_display).strip()
    if client:
        payload["client"] = client

    # Opérateur (caissier/vendeur) - obligatoire
    payload["operator"] = {
        "name": settings.get("operator_name")
        or frappe.utils.get_fullname(frappe.session.user)
        or "Vendeur"
    }

    # Paiements - optionnel (ESPECES par défaut côté e-MECeF si absent)
    payments = []
    for payment in (doc.get("payments") or []):
        mecef_mode = PAYMENT_MODE_MAP.get(payment.mode_of_payment, "AUTRE")
        payments.append({"name": mecef_mode, "amount": int(round(flt(payment.amount)))})
    if not payments:
        payments.append({"name": "ESPECES", "amount": int(round(flt(doc.grand_total)))})
    payload["payment"] = payments

    # Facture d'avoir (credit note) : référence à la facture originale (24 car. sans tirets)
    if doc.is_return and doc.return_against:
        original_code = frappe.db.get_value(
            "Sales Invoice", doc.return_against, "mecef_numero"
        )
        if original_code:
            payload["reference"] = original_code.replace("-", "")[:24]

    return payload


def _get_headers(settings, with_content_type=True):
    """En-têtes d'authentification. Utilise get_password pour récupérer le
    vrai jeton (un champ Password ne doit pas être lu directement)."""
    token = settings.get_password("api_key") if settings.get("api_key") else None
    if not token:
        frappe.throw(_("Clé API MECeF manquante dans 'MeCef Settings'."))
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if with_content_type:
        headers["Content-Type"] = "application/json"
    return headers


def _call_mecef(method, url, headers, step, **kwargs):
    """Appelle l'API e-MECeF et renvoie le JSON, avec des erreurs explicites."""
    try:
        response = requests.request(
            method, url, headers=headers, timeout=REQUEST_TIMEOUT, **kwargs
        )
    except requests.exceptions.RequestException as e:
        frappe.log_error(message=frappe.get_traceback(), title=f"MECeF - Échec réseau ({step})")
        frappe.throw(_("Erreur réseau e-MECeF ({0}) : {1}").format(step, str(e)))

    # Réponse non-JSON (ex. page HTML si l'URL 'host' est incorrecte)
    try:
        data = response.json()
    except ValueError:
        snippet = (response.text or "").strip()[:300]
        frappe.log_error(
            message="HTTP {0}\nContent-Type: {1}\nURL: {2}\nBody: {3}".format(
                response.status_code, response.headers.get("content-type"), url, snippet
            ),
            title=f"MECeF - Réponse non-JSON ({step})",
        )
        if response.status_code == 401:
            frappe.throw(_("e-MECeF : jeton non autorisé ou expiré (401). Renouvelez la clé API dans 'MeCef Settings'."))
        frappe.throw(
            _("e-MECeF ({0}) a renvoyé une réponse invalide [HTTP {1}]. Vérifiez que 'host' se termine bien par /api/invoice.").format(
                step, response.status_code
            )
        )

    # Statut HTTP d'erreur mais corps JSON (problem+json ou DTO d'erreur)
    if response.status_code >= 400:
        if response.status_code == 401:
            frappe.throw(_("e-MECeF : jeton non autorisé ou expiré (401). Renouvelez la clé API dans 'MeCef Settings'."))
        desc = data.get("errorDesc") or data.get("title") or data.get("detail") or str(data)
        code = data.get("errorCode") or data.get("status") or response.status_code
        frappe.throw(_("e-MECeF ({0}) erreur [{1}] : {2}").format(step, code, desc))

    return data


def send_to_mecef(doc):
    """Envoie la facture à l'API e-MECeF (deux étapes) et met à jour les champs."""
    settings = get_mecef_settings(doc.company)

    base_url = settings.host.rstrip("/")
    headers = _get_headers(settings)

    # Étape 1 : POST / (Demande de facture)
    payload = build_invoice_payload(doc, settings)
    data = _call_mecef("POST", f"{base_url}/", headers, "demande de facture", json=payload)

    uid = data.get("uid")
    if not uid:
        error_code = data.get("errorCode")
        error_desc = data.get("errorDesc", "Aucun UID retourné")
        frappe.throw(_("e-MECeF a retourné une erreur : [{0}] {1}").format(error_code, error_desc))

    # Vérification des totaux (recommandé par la spécification)
    returned_total = data.get("total")
    if returned_total is not None and abs(int(returned_total) - int(round(flt(doc.grand_total)))) > 1:
        frappe.log_error(
            message=_("Total e-MECeF: {0} / Total ERPNext: {1}").format(
                returned_total, doc.grand_total
            ),
            title="MECeF - Écart de total (facture {0})".format(doc.name),
        )

    # Étape 2 : PUT /{UID}/confirm (Demande de finalisation)
    security = _call_mecef("PUT", f"{base_url}/{uid}/confirm", headers, "finalisation")

    if not security.get("codeMECeFDGI"):
        error_code = security.get("errorCode")
        error_desc = security.get("errorDesc", "Code MECeF manquant")
        frappe.throw(_("Finalisation échouée : [{0}] {1}").format(error_code, error_desc))

    # Mise à jour des champs personnalisés (document déjà soumis -> db_set)
    doc.db_set(
        {
            "mecef_numero": security.get("codeMECeFDGI"),
            "mecef_qr_code": security.get("qrCode"),
            "mecef_nim": security.get("nim"),
            "mecef_envoye": 1,
        }
    )
    frappe.msgprint(
        _("Facture normalisée e-MECeF enregistrée : {0}").format(security.get("codeMECeFDGI")),
        indicator="green",
        alert=True,
    )


def on_submit(doc, method=None):
    if not doc.get("demande_facture_normalisee"):
        return
    if doc.get("mecef_envoye"):
        return
    if not get_mecef_settings(doc.company, required=False):
        return
    # ponytail: restaurant POS submits via URY make_invoice — MECeF at print (pos_whatsapp).
    if doc.doctype == "POS Invoice":
        return
    send_to_mecef(doc)


def file_to_data_uri(file_url):
    """Retourne une image en data-URI base64 (lue sur le disque) pour un
    affichage fiable en PDF (wkhtmltopdf), sans dépendre d'une URL réseau.

    Fonctionne pour les fichiers publics et privés. Méthode Jinja utilisable
    dans les Letter Head / formats d'impression pour embarquer un logo.
    """
    if not file_url:
        return ""
    if file_url.startswith("data:"):
        return file_url
    import base64
    import mimetypes

    try:
        name = frappe.db.get_value("File", {"file_url": file_url}, "name")
        if not name:
            return ""
        path = frappe.get_doc("File", name).get_full_path()
        with open(path, "rb") as fh:
            content = fh.read()
    except Exception:
        frappe.log_error(message=frappe.get_traceback(), title="MECeF - Logo introuvable")
        return ""

    mime = mimetypes.guess_type(file_url)[0] or "image/png"
    return "data:%s;base64,%s" % (mime, base64.b64encode(content).decode())


def mecef_qr_base64(content, scale=4):
    """Génère un QR code PNG (data URI base64) à partir du CONTENU MECeF.

    Le champ `mecef_qr_code` renvoyé par l'e-MECeF est la chaîne à encoder
    (ex. "F;TS01...;...") et NON une image. Cette méthode Jinja produit une
    image auto-contenue, compatible avec la génération PDF (wkhtmltopdf).
    """
    if not content:
        return ""
    import io
    import base64
    import pyqrcode

    buffer = io.BytesIO()
    pyqrcode.create(content, error="M").png(buffer, scale=int(scale or 4), quiet_zone=1)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


@frappe.whitelist()
def check_status(company=None):
    """Vérifie la connectivité et la validité du jeton avec l'API e-MECeF.
    Utilise l'API de facturation (demande de statut)."""
    company = company or frappe.defaults.get_user_default("Company")
    if not company:
        company = frappe.db.get_single_value("Global Defaults", "default_company")
    settings = get_mecef_settings(company)
    base_url = settings.host.rstrip("/")
    headers = _get_headers(settings, with_content_type=False)
    return _call_mecef("GET", f"{base_url}/", headers, "demande de statut")
