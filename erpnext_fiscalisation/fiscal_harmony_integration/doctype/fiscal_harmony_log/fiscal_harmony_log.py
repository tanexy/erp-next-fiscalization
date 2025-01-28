# Copyright (c) 2024, Eskill Trading (Pvt) Ltd and contributors
# For license information, please see license.txt

from typing import TYPE_CHECKING, TypedDict, Optional

import frappe
from frappe.model.document import Document

if TYPE_CHECKING:
    from frappe.types import DF


class FiscalHarmonyLog(Document):
    """Doctype used to log activity in the Fiscal Harmony integration."""

    if TYPE_CHECKING:
        status = DF.Data
        payload = DF.Text
        response = DF.Text
        response_status_code = DF.Int
        signature_valid = DF.Check
        request_id = DF.Data
        error_details = DF.Text
        request_url = DF.Data


class FiscalHarmonyLogData(TypedDict):
    """A dictionary to define data to be parsed into a log entry.

    ## Keys:
        status (str): The result of the transaction.
        payload (str): The raw request JSON payload.
        response (str): The raw response JSON payload.
        response_status_code (int): HTTP status code of the transaction. Either sent or returned.
        signature_valid (bool, optional): Whether the payload signature was valid. Defaults to True.
        request_id (str | None, optional): The request ID tracked in Fiscal Harmony.\
            Defaults to None.
        error_details (str | None, optional): Additional error details, if any. Defaults to None.
        request_url (str | None, optional): The URL that the request was posted to.\
            Defaults to None."""

    status: str
    payload: Optional[str]
    response: str
    response_status_code: int
    signature_valid: Optional[bool]
    request_id: Optional[str]
    error_details: Optional[str]
    request_url: Optional[str]


def fh_log(log_data: FiscalHarmonyLogData):
    """Create a log for Fiscal Harmony activities.

    Args:
        log_data (FiscalHarmonyLogData): The data to be logged."""

    try:
        log: FiscalHarmonyLog = frappe.new_doc("Fiscal Harmony Log")
        log.status = log_data.get("status")
        log.payload = log_data.get("payload", "")
        log.response = log_data.get("response")
        log.response_status_code = log_data.get("response_status_code")
        log.signature_valid = log_data.get("signature_valid", True)
        log.request_id = log_data.get("request_id", None)
        log.error_details = log_data.get("error_details", None)
        log.request_url = log_data.get("request_url", None)

        log.insert(ignore_permissions=True)
        frappe.db.commit()

    except Exception as exc:
        message = (
            f"Failed to create Fiscal Harmony Log.\nError: {exc}\n\n"
            + "Received the following logs:"
        )
        for key, val in log_data.items():
            message += f"\n{key}: {str(val).strip()}"

        frappe.log_error("Fiscal Harmony Logging Error", message=message)
