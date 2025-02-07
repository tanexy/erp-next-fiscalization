app_name = "erpnext_fiscalisation"
app_title = "Fiscal Harmony Integration"
app_publisher = "Eskill Trading (Pvt) Ltd"
app_description = "This app implements the Fiscal Harmony API for integration with ERPNext for the fiscalisation of invoices and credit notes."
app_email = "andrew@eskilltrading.com"
app_license = "gpl-3.0"
required_apps = ["erpnext"]

# Jinja
# ----------

# Add methods and filters to jinja environment.
jinja = {
    "methods": "erpnext_fiscalisation.print_api",
}


# DocType Class
# -------------

# Override standard doctype classes.
override_doctype_class = {
    "Sales Invoice": "erpnext_fiscalisation.overrides.doctypes.sales_invoice.FiscalSalesInvoice"
}

# Include js in doctype views.
doctype_js = {
    "Customer": "public/js/doctype/customer.js",
    "Item Group": "public/js/doctype/item_group.js",
}

override_whitelisted_methods = {
    "capture_signatures": "erpnext_fiscalisation.api.capture_signatures"
}


# DocType Customisations
# ----------------------

# Custom data to be exported.
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            ["module", "=", "Fiscal Harmony Integration"],
        ],
    }
]
