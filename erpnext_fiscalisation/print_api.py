"""This module defines print related methods."""

import io
import base64
import qrcode

import frappe

__PNG_SRC_TEMPLATE = r"data:image/png;base64,{}"


def get_fiscal_details(invoice: str) -> dict:
    """Fetch a dictionary of invoice FDMS verification details.

    Args:
        invoice (str): Name of the document.

    Returns:
        dict: An object detailing the verification details of the `invoice`."""

    return frappe.get_value(
        "Fiscal Signature",
        {"sales_invoice": invoice},
        ["verification_code", "fiscal_day", "device_id", "invoice_number"],
        as_dict=True,
    )


def get_fiscal_qr_code(invoice: str) -> str:
    """Generate the QR code to display on a fiscalised invoice/credit note.

    Args:
        invoice (str): Name of the document.

    Returns:
        str: The QR code PNG data."""

    fdms_url = frappe.get_value(
        "Fiscal Signature",
        {"sales_invoice": invoice},
        "fdms_url",
    )

    if not fdms_url:
        return __PNG_SRC_TEMPLATE.format("")

    img = qrcode.make(fdms_url)

    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return __PNG_SRC_TEMPLATE.format(img_str)
