"""This patch corrects the docstatus of Fiscal Signatures to correctly reflect 0."""

import frappe
from frappe.query_builder import DocType


def execute():
    """This patch corrects the docstatus of Fiscal Signatures to correctly reflect 0."""

    fiscal_signatures = DocType("Fiscal Signature")
    (
        frappe.qb.update(fiscal_signatures)
        .set(fiscal_signatures.docstatus, 0)
        .where(fiscal_signatures.docstatus != 0)
    ).run()
