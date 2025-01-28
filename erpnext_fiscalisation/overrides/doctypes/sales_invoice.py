"""This module defines an override for the Sales Invoice doctype."""

import frappe

from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice


class FiscalSalesInvoice(SalesInvoice):
    """This subclass of SalesInvoice implements fiscalisation processes."""

    def on_submit(self):
        super().on_submit()

        fiscal_settings = frappe.get_single("Fiscal Harmony Settings")
        if not fiscal_settings.disabled:
            signature = frappe.new_doc("Fiscal Signature")
            signature.sales_invoice = self.name
            signature.insert(ignore_permissions=True)
            # signature.save()
