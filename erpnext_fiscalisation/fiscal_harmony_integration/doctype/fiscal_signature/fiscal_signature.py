# Copyright (c) 2024, Eskill Trading (Pvt) Ltd and contributors
# For license information, please see license.txt

import datetime
from typing import TYPE_CHECKING

import pytz

import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext.selling.doctype.customer.customer import Customer
from frappe.contacts.doctype.address.address import Address
from frappe.contacts.doctype.contact.contact import Contact
from frappe.model.document import Document
from frappe.types import DF

if TYPE_CHECKING:
    from erpnext_fiscalisation.fiscal_harmony_integration.doctype.fiscal_harmony_settings.fiscal_harmony_settings import (
        FiscalHarmonySettings,
    )


class FiscalSignature(Document):
    """This document manages an individual transaction to be posted to Fiscal Harmony."""

    if TYPE_CHECKING:
        sales_invoice: DF.Link
        fdms_url: DF.Data
        is_retry: DF.Check
        error: DF.Data
        fiscal_harmony_id: DF.Data
        fiscal_harmony_filename: DF.Data
        bypass_tin: DF.Check

    @frappe.whitelist()
    def fetch_signing_data(self):
        """Fetch the fiscal data if transaction was submitted,\
            but no data was received via webhook."""

        if not self.fiscal_harmony_id:
            frappe.throw(
                "There is no Fiscal Harmony ID to check against.",
                title="Fiscal Harmony Signature Processing",
            )

        if self.fdms_url:
            frappe.throw(
                "All data has already been fetched.",
                title="Fiscal Harmony Signature Processing",
            )

        if "System Manager" not in frappe.get_roles():
            frappe.throw(
                (
                    "You do not have access to retry fiscalisation. "
                    "Please contact system admin to proceed."
                ),
                title="Authorisation Error",
            )

        fiscal_settings: FiscalHarmonySettings = frappe.get_doc(
            "Fiscal Harmony Settings"
        )
        fiscal_settings.fetch_signature_data(self)

    @frappe.whitelist()
    def retry_fiscalisation(self):
        """Retry fiscalisation of the linked document."""

        if not self.is_retry:
            frappe.throw(
                (
                    "This signature can't be resubmitted, it has either been fiscalised or there "
                    "is an unrecoverable error. Check document details."
                ),
                title="Fiscal Harmony Signature Processing",
            )

        if "System Manager" not in frappe.get_roles():
            frappe.throw(
                (
                    "You do not have access to retry fiscalisation. "
                    "Please contact system admin to proceed."
                ),
                title="Authorisation Error",
            )

        self.__fiscalise()

    def after_insert(self):
        """Processes the signature after insertion."""

        self.__fiscalise()

    @frappe.whitelist()
    def download_or_generate_pdf(self):
        """Download or generate the PDF using default print formats then attach it to the linked\
            invoice."""

        fiscal_settings: FiscalHarmonySettings = frappe.get_doc(
            "Fiscal Harmony Settings"
        )

        # Fetch the PDF content.
        if fiscal_settings.attach_local_print:
            pdf = frappe.get_print("Sales Invoice", self.sales_invoice, as_pdf=True)
        else:
            pdf = fiscal_settings.download_fiscal_pdf(self)

        if not pdf:
            return

        try:
            posting_date = frappe.get_value(
                "Sales Invoice",
                self.sales_invoice,
                "posting_date",
            )
            base_folder = _create_folder("Fiscal Invoices")
            year_folder = _create_folder(str(posting_date.year), base_folder)
            month_folder = _create_folder(posting_date.strftime(r"%m"), year_folder)

            if not frappe.db.exists(
                "File",
                {
                    "file_name": f"{self.sales_invoice}.pdf",
                    "folder": month_folder,
                },
            ):
                file_doc = frappe.get_doc(
                    {
                        "doctype": "File",
                        "file_name": f"{self.sales_invoice}.pdf",
                        "content": pdf,
                        "attached_to_doctype": "Sales Invoice",
                        "attached_to_name": self.sales_invoice,
                        "folder": month_folder,
                        "is_private": True,
                    }
                )
                file_doc.insert(ignore_permissions=True)
                frappe.db.commit()

        except Exception as exc:
            frappe.log_error(
                "Fiscal Harmony: PDF Download",
                f"Failed to attach the downloaded PDF to invoice {self.sales_invoice}. Error {exc}",
            )

    def get_payload_data(self) -> dict[str,]:
        """Generate the structured payload for posting the referenced invoice/credit note.

        Returns:
            dict[str,]: The payload data for posting."""

        transaction: SalesInvoice = frappe.get_doc("Sales Invoice", self.sales_invoice)

        if transaction.is_return:
            return self.__get_credit_note_data(transaction)

        return self.__get_invoice_data(transaction)

    def __fiscalise(self):
        """Submit the signature details for fiscalisation."""

        fiscal_settings: FiscalHarmonySettings = frappe.get_doc(
            "Fiscal Harmony Settings"
        )
        fiscal_settings.fiscalise_transaction(self)

    def __get_invoice_data(self, transaction: SalesInvoice) -> dict[str,]:
        """Generate the invoice data payload.

        Args:
            transaction (SalesInvoice): The invoice object.

        Returns:
            dict[str,]: The generated payload to transmit to FiscalHarmony."""

        buyer_contact = self.__get_buyer_contact(transaction)
        line_items = self.__get_line_items(transaction)

        data = {
            "InvoiceId": transaction.name,
            "InvoiceNumber": transaction.name,
            "Reference": transaction.po_no,
            "IsDiscounted": bool(transaction.is_discounted),
            "IsTaxInclusive": True,
            "BuyerContact": buyer_contact,
            "Date": self.__create_timestamp(
                transaction.posting_date,
                transaction.posting_time,
            ),
            "LineItems": line_items,
            "SubTotal": round(transaction.net_total, 2),
            "TotalTax": round(transaction.total_taxes_and_charges, 2),
            "Total": round(transaction.grand_total, 2),
            "CurrencyCode": transaction.currency,
            "IsRetry": bool(self.is_retry),
        }

        return data

    def __get_credit_note_data(self, transaction: SalesInvoice) -> dict[str,]:
        """Generate the credit note data payload.

        Args:
            transaction (SalesInvoice): The credit note object.

        Returns:
            dict[str,]: The generated payload to transmit to FiscalHarmony."""

        buyer_contact = self.__get_buyer_contact(transaction)
        line_items = self.__get_line_items(transaction)

        data = {
            "CreditNoteId": transaction.name,
            "CreditNoteNumber": transaction.name,
            "OriginalInvoiceId": transaction.return_against,
            "Reference": transaction.return_reason,
            "IsTaxInclusive": True,
            "BuyerContact": buyer_contact,
            "Date": self.__create_timestamp(
                transaction.posting_date,
                transaction.posting_time,
            ),
            "LineItems": line_items,
            "SubTotal": round(abs(transaction.net_total), 2),
            "TotalTax": round(abs(transaction.total_taxes_and_charges), 2),
            "Total": round(abs(transaction.grand_total), 2),
            "CurrencyCode": transaction.currency,
            "IsRetry": bool(self.is_retry),
        }

        return data

    def __get_line_items(self, transaction: SalesInvoice) -> list[dict]:
        """Creates a list of line items for the given transaction.

        Args:
            transaction (SalesInvoice): The Sales Invoice object being processed.

        Returns:
            list[dict]: The list of dictionaries detailing the sold items."""

        fiscal_settings: FiscalHarmonySettings = frappe.get_doc(
            "Fiscal Harmony Settings"
        )
        tax_codes = set()
        default_tax_code = None
        for tax_mapping in fiscal_settings.tax_mappings:
            tax_codes.add(tax_mapping.tax_code)
            if tax_mapping.is_default:
                default_tax_code = tax_mapping.tax_code

        line_items: list[dict] = []
        for item in transaction.items:
            item_dict = {
                "Description": item.item_name,
                "UnitAmount": round(abs(item.rate), 3),
                "TaxCode": "S",
                "LineAmount": round(abs(item.amount), 2),
                "DiscountAmount": round(abs(item.discount_amount), 2) or None,
                "Quantity": round(abs(item.qty), 3),
            }

            # Work out the tax code, trying first for an item-specific tax code
            # before moving on to the document tax code, and then the default
            # if no valid tax code is set.
            tax_code = None
            if item.item_tax_template in tax_codes:
                tax_code = item.item_tax_template
            elif transaction.taxes_and_charges in tax_codes:
                tax_code = transaction.taxes_and_charges
            elif default_tax_code:
                tax_code = default_tax_code

            # Throw out an error message if a tax code can't be found.
            if not tax_code:
                frappe.throw(
                    "Failed to generate fiscal payload for invoice "
                    f"{transaction.name} due to no tax templates being mapped.",
                    title="Fiscalisation Error",
                )

            item_dict["TaxCode"] = tax_code

            # Include HS Codes if the setting is enabled.
            if fiscal_settings.include_hs_codes:
                # Default to the HS Code based on the item.
                hs_code = (
                    frappe.get_value("Item", item.item_code, "fh_hs_code")
                    if item.item_code
                    else ""
                )

                # If HS Code not found, try fetching it from the item group.
                if not hs_code and item.item_group:
                    hs_code = frappe.get_value(
                        "Item Group",
                        item.item_group,
                        "fh_hs_code",
                    )

                # Throw an error message if no HS Code is found.
                if not hs_code:
                    frappe.throw(
                        "Failed to generate fiscal payload for invoice "
                        f"{transaction.name} due to missing HS Code for "
                        f'item "{item.item_name}".',
                        title="Fiscalisation Error",
                    )

                item_dict["ProductCode"] = hs_code

            line_items.append(item_dict)

        return line_items

    def __get_buyer_contact(self, transaction: SalesInvoice) -> dict[str]:
        """Returns a dictionary detailing the customer information.

        Args:
            transaction (SalesInvoice): The Sales Invoice object being processed.

        Returns:
            dict[str]: A dictionary detailing the customer contact information."""

        customer: Customer = frappe.get_doc("Customer", transaction.customer)
        customer_names = transaction.customer_name.split(r" t/a ")

        contact_person: Contact = frappe.get_doc("Contact", transaction.contact_person)
        billing_address: Address = frappe.get_doc(
            "Address",
            transaction.customer_address,
        )

        buyer_contact = {
            "Name": customer_names[0],
            "Address": {
                "Province": billing_address.country,
                "Street": (
                    billing_address.address_line2 or billing_address.address_line1
                ),
                "HouseNo": billing_address.address_line1,
                "City": billing_address.city,
            },
        }

        if len(customer_names) > 1:
            buyer_contact["TradeName"] = customer_names[1]

        if contact_person.phone:
            buyer_contact["Phone"] = contact_person.phone

        if contact_person.email_id:
            buyer_contact["Email"] = contact_person.email_id

        if customer.tin_number:
            buyer_contact["Tin"] = customer.tin_number
            if customer.tax_id:
                buyer_contact["VatNumber"] = customer.tax_id

        elif (customer.customer_type == "Individual" or self.bypass_tin) and not (
            buyer_contact["Name"].startswith("Cash ")
        ):
            buyer_contact["Name"] = "Cash " + buyer_contact["Name"]

        return buyer_contact

    def __create_timestamp(self, date: DF.Date, time: datetime.timedelta) -> str:
        """Returns a formatted timestamp for submitting to Fiscal Harmony.

        Args:
            date (DF.Date): The date component of the datetime.
            time (datetime.timedelta): The time component of the datetime.

        Returns:
            str: Timestamp formatted as "1970-1-1T00:00:00+0000"."""

        time_zone = frappe.db.get_single_value("System Settings", "time_zone")
        tz_info = pytz.timezone(time_zone)

        dt = datetime.datetime.combine(date, datetime.time())
        dt += time
        dt = tz_info.localize(dt, False)

        formatted_dt = dt.strftime(r"%Y-%m-%dT%H:%M:%S%z")

        return formatted_dt[:-2] + ":" + formatted_dt[-2:]


def _create_folder(folder_name: str, parent_folder: str = "Home") -> str:
    """Generating and return the given folder structure.

    Args:
        folder_name (str): The name of the folder.
        parent_folder (str, optional): The parent folder. Defaults to "Home".

    Returns:
        str: The name of the folder document."""

    existing_folder: str | None = frappe.db.exists(
        "File",
        {
            "file_name": folder_name,
            "is_folder": True,
            "folder": parent_folder,
        },
    )

    if existing_folder:
        return existing_folder

    folder = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": folder_name,
            "is_folder": True,
            "folder": parent_folder,
            "is_private": True,
        }
    )
    folder.insert(ignore_permissions=True)
    frappe.db.commit()

    return folder.name
