// Copyright (c) 2024, Eskill Trading (Pvt) Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fiscal Harmony Settings", {
  refresh(frm) {
    frm.add_custom_button(__("Check User Profile"), () => {
      checkUserProfile(frm);
    });
    frm.add_custom_button(__("Get Device Info"), () => {
      getDeviceInfo(frm);
    });
    frm.add_custom_button(__("Update API Token"), () => {
      updateApiToken(frm);
    });
    frm.add_custom_button(__("Get Webhook URL"), () => {
      const webhook = `https://${window.location.hostname}/api/method/capture_signatures`;
      frappe.msgprint(
        "<p>To use the webhook, your ERPNext site must use HTTPS.</p>" +
          `<p>The webhook url to enter in the portal is <strong>${webhook}</strong></p>`,
        "Fiscal Harmony Webhook URL"
      );
    });
  },

  check_supported_currencies(frm) {
    frappe.call({
      doc: frm.doc,
      method: "check_supported_currencies",
      callback: (_) => frm.reload_doc(),
    });
  },

  validate_currency_mappings(frm) {
    if (!(frm.doc.api_key && frm.doc.api_secret) || frm.is_dirty()) return;

    frappe.call({
      doc: frm.doc,
      method: "validate_currency_mappings",
      callback: (_) => frm.reload_doc(),
    });
  },

  validate_tax_mappings(frm) {
    if (!(frm.doc.api_key && frm.doc.api_secret) || frm.is_dirty()) return;

    frappe.call({
      doc: frm.doc,
      method: "validate_tax_mappings",
      callback: (_) => frm.reload_doc(),
    });
  },
});

/**
 * Prompt the user for API authentication details, and update them if they are valid.
 * @param frm A reference to the form body.
 */
const updateApiToken = (frm) => {
  if (frm.is_dirty()) frm.save();
  frappe.prompt(
    [
      {
        label: "API Key",
        fieldname: "api_key",
        fieldtype: "Data",
        reqd: true,
        default: frm.doc.api_key,
      },
      {
        label: "API Secret",
        fieldname: "api_secret",
        fieldtype: "Password",
        reqd: true,
      },
    ],
    (values) => {
      const apiKey = values.api_key;
      const apiSecret = values.api_secret;

      const keyRegex = /^[A-Z\d]{32}$/gm;
      if (keyRegex.exec(apiKey) == null) {
        frappe.throw("Please provide a valid API key.");
      }
      const secretRegex = /^[a-zA-Z\d\/\+]{86}==$/gm;
      if (secretRegex.exec(apiSecret) == null) {
        frappe.throw("Please provide a valid API secret.");
      }

      frappe.call({
        doc: frm.doc,
        method: "validate_api_details",
        args: {
          api_key: apiKey,
          api_secret: apiSecret,
        },
        callback: (_) => frm.reload_doc(),
      });
    },
    "Update API Key & Secret",
    "Submit"
  );
};

/**
 * Checks the Fiscal Harmony user profile ID.
 * @param frm A referemce to the form body.
 */
const checkUserProfile = (frm) => {
  if (!(frm.doc.api_key && frm.doc.api_secret) || frm.is_dirty()) return;

  frappe.call({
    doc: frm.doc,
    method: "check_user_profile",
    callback: (_) => frm.reload_doc(),
  });
};

/**
 * Fetches the Fiscal Harmony device details.
 * @param frm A referemce to the form body.
 */
const getDeviceInfo = (frm) => {
  if (!(frm.doc.api_key && frm.doc.api_secret) || frm.is_dirty()) return;

  frappe.call({
    doc: frm.doc,
    method: "get_device_info",
    callback: (_) => frm.reload_doc(),
  });
};
