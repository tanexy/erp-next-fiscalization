"""This module defines API endpoints for receiving data from the Fiscal Harmony platform."""

import json
import jsonschema

from werkzeug.wrappers import Response

import frappe

from erpnext_fiscalisation.fiscal_harmony_integration.doctype.fiscal_harmony_settings.fiscal_harmony_settings import (
    FiscalHarmonySettings,
)

from erpnext_fiscalisation.fiscal_harmony_integration.doctype.fiscal_harmony_log.fiscal_harmony_log import (
    fh_log,
    FiscalHarmonyLogData,
)

from erpnext_fiscalisation.fiscal_harmony_integration.doctype.fiscal_signature.fiscal_signature import (
    FiscalSignature,
)

SIGNATURE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "RequestId": {"type": "string"},
            "Success": {"type": "boolean"},
            "FiscalInvoicePdf": {"type": ["string", "null"]},
            "QrData": {
                "type": ["object", "null"],  # QrData can be an object or null
                "properties": {
                    "QrCodeUrl": {"type": "string"},
                    "VerificationCode": {"type": "string"},
                    "FiscalDay": {"type": "integer"},
                    "DeviceId": {"type": "integer"},
                    "InvoiceNumber": {"type": "integer"},
                },
                "required": [
                    "QrCodeUrl",
                    "VerificationCode",
                    "FiscalDay",
                    "DeviceId",
                    "InvoiceNumber",
                ],
            },
        },
        "required": ["RequestId", "Success", "QrData"],
    },
}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def capture_signatures() -> Response:
    """Endpoint for the Fiscal Harmony platform to post fiscal signatures to.

    Returns:
        Response: Custom response based on validation of received payload."""

    fiscal_harmony_settings: FiscalHarmonySettings = frappe.get_single(
        "Fiscal Harmony Settings"
    )

    # Prepare the response.
    response = Response(
        mimetype="application/json",
    )
    raw_data = frappe.request.get_data(as_text=True)
    log_data: FiscalHarmonyLogData = {
        "request_url": frappe.request.url,
        "payload": raw_data,
    }

    # Retrieve the signature from headers.
    received_signature = frappe.get_request_header("X-Api-Signature")

    # Verify the signature.
    if fiscal_harmony_settings.test_signature(received_signature, raw_data):
        # Parse the JSON data.
        try:
            payload = json.loads(raw_data)
            jsonschema.validate(payload, SIGNATURE_SCHEMA)

            response_data = {"status": "Success"}
            response.status_code = 200
            response.data = json.dumps(response_data, separators=(",", ":"))

            log_data["response"] = json.dumps(response_data, indent=2)
            log_data["response_status_code"] = 200
            log_data["status"] = "Success"

            for signature_data in payload:
                signature: FiscalSignature = frappe.get_last_doc(
                    "Fiscal Signature",
                    filters={"fiscal_harmony_id": signature_data["RequestId"]},
                )
                signature.is_retry = (
                    signature_data["IsActionable"] and not signature_data["Success"]
                )
                if signature_data["Error"]:
                    signature.error = signature_data["Error"]
                elif signature.error:
                    signature.error = ""

                if qr_data := signature_data["QrData"]:
                    signature.fdms_url = qr_data["QrCodeUrl"]
                    signature.verification_code = qr_data["VerificationCode"]
                    signature.fiscal_day = qr_data["FiscalDay"]
                    signature.device_id = qr_data["DeviceId"]
                    signature.invoice_number = qr_data["InvoiceNumber"]

                signature.fiscal_harmony_filename = signature_data.get(
                    "FiscalInvoicePdf",
                    None,
                )
                signature.save(ignore_permissions=True)
                if signature.fiscal_harmony_filename:
                    signature.download_or_generate_pdf()

        except json.JSONDecodeError:
            log_data["response"] = json.dumps(
                {
                    "error": "Invalid JSON",
                },
                indent=2,
            )
            log_data["response_status_code"] = 400
            log_data["status"] = "Invalid JSON"
            log_data["error_details"] = (
                "Invalid JSON data received from Fiscal Harmony."
            )

        except jsonschema.ValidationError as exc:
            log_data["response"] = json.dumps(
                {
                    "error": "Invalid JSON structure",
                    "details": str(exc),
                },
                indent=2,
            )
            log_data["response_status_code"] = 400
            log_data["status"] = "Invalid JSON"
            log_data["error_details"] = (
                "Invalid JSON structure received from Fiscal Harmony."
            )

        except frappe.DoesNotExistError as exc:
            log_data["response"] = json.dumps(
                {
                    "error": "RequestId is unknown",
                    "details": str(exc),
                },
                indent=2,
            )
            log_data["response_status_code"] = 404
            log_data["status"] = "Failure"
            log_data["error_details"] = (
                "Unknown RequestId received from Fiscal Harmony."
            )

        except Exception as exc:
            frappe.log_error(
                "Fiscal Harmony Integration",
                f"Exception occurred: {str(exc)}\nReceived data: {raw_data}",
            )

            log_data["response"] = json.dumps(
                {
                    "error": "Internal Server Error",
                    "details": str(exc),
                },
                indent=2,
            )
            log_data["response_status_code"] = 500
            log_data["status"] = "Failure"
            log_data["error_details"] = str(exc)

    else:
        response_data = {"error": "Unauthorized - Invalid signature"}
        response.data = json.dumps(response_data, separators=(",", ":"))
        response.status_code = 401

        log_data["response"] = json.dumps(response_data, indent=2)
        log_data["response_status_code"] = 401
        log_data["status"] = "Unauthorised"
        log_data["signature_valid"] = False
        log_data["error_details"] = "Received an invalid signature."

    fh_log(log_data)

    return response
