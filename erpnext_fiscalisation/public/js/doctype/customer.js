frappe.ui.form.on("Customer", {
  before_save(frm) {
    validate_tax_fields(frm);
  },
});

/**
 * Checks that the tax number fields are valid.
 *
 * @param frm A reference to the form object for the current Customer document.
 */
const validate_tax_fields = (frm) => {
  if (frm.doc.tax_id && !frm.doc.tax_id.match(/^2\d{8}$/gm)) {
    frappe.msgprint(
      `<p>
        <strong>${frm.doc.tax_id}</strong> is an invalid VAT number. It must start with 2 followed by 8 digits.
      </p>`
    );
    frappe.validated = false;
  }

  if (frm.doc.tin_number && !frm.doc.tin_number.match(/^\d{10}$/gm)) {
    frappe.msgprint(
      `<p>
        <strong>${frm.doc.tin_number}</strong> is an invalid TIN number. It must contain 10 digits.
      </p>`
    );
    frappe.validated = false;
  }
};
