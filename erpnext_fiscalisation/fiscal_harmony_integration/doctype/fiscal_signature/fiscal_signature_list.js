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
    let doc_status, colour, filter;
    if (doc.is_retry) {
      doc_status = "Needs Retry";
      colour = "red";
      filter = "is_retry,=,1";
    } else if (doc.fdms_url) {
      doc_status = "Fiscalised";
      colour = "green";
      filter = "fdms_url,is,set";
    } else if (doc.error) {
      doc_status = `${doc.error}`;
      colour = "gray";
      filter = "error,is,set";
    } else {
      doc_status = "Pending FH Response";
      colour = "orange";
      filter = "fdms_url,is,not set";
    }

    return [doc_status, colour, filter];
  },
  hide_name_column: true,
  refresh: () => {},
};
