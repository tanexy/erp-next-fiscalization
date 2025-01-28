# Copyright (c) 2025, Eskill Trading (Pvt) Ltd and contributors
# For license information, please see license.txt

import re
from typing import TYPE_CHECKING

import frappe
from frappe.model.document import Document

if TYPE_CHECKING:
    from frappe.types import DF


class FiscalHSCode(Document):
    """This doctype represents an HS Code used to identify a product during fiscalisation."""

    if TYPE_CHECKING:
        hs_code: DF.Data

    def before_rename(self, old: str, new: str, merge: bool = False) -> str:
        """Validate the new name before renaming the document.

        Args:
            old (str): The original name of the document.
            new (str): The new name of the document.
            merge (bool, optional): Whether to merge with an existing document. Defaults to False.

        Returns:
            str: The new name of the document after validation."""

        self._validate_hs_code(new)

        return new

    def validate(self):
        """Validate the document before saving."""

        self._validate_hs_code(self.hs_code)

    def _validate_hs_code(self, code: str):
        """Validate the given HS Code.

        Args:
            code (str): The code to be validated."""

        if not re.fullmatch(r"^\d{8,10}$", code):
            frappe.throw(
                "Invalid HS Code provided. Please ensure that it is 8-10 digits."
            )
