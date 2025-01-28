// Copyright (c) 2024, Eskill Trading (Pvt) Ltd and contributors
// For license information, please see license.txt

/** Colour options for the signature status. */
const colours = {
  Open: {
    Urgent: "red",
    High: "orange",
    Normal: "blue",
    Low: "green",
  },
  "On Hold": {
    Urgent: "lightred",
    High: "lightorange",
    Normal: "lightblue",
    Low: "lightgreen",
  },
};

frappe.listview_settings["Fiscal Signature"] = {
  add_fields: ["sales_invoice", "is_retry", "fdms_url", "error"],
  colwidths: {
    sales_invoice: 1,
  },
  get_indicator: (doc) => {
    let doc_status, colour;
    if (doc.is_retry) {
      doc_status = "Needs Retry";
      colour = "red";
    } else if (doc.fdms_url) {
      doc_status = "Fiscalised";
      colour = "green";
    } else {
      doc_status = `${doc.error}`;
      colour = "gray";
    }

    return [doc_status, colour, `is_retry,=,${doc.is_retry}`];
  },
  hide_name_column: true,
  refresh: () => {},
};
