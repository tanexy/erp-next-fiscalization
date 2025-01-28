import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count

from erpnext.setup.doctype.item_group.item_group import ItemGroup


@frappe.whitelist()
def set_hs_codes_on_items(group_name: str):
    """Set HS Codes on items linked to the given item group.

    Args:
        group_name (str): The name of the item group."""

    item_group: ItemGroup = frappe.get_doc("Item Group", group_name)
    if not item_group:
        frappe.throw(f'Item Group "{group_name}" does not exist.')

    items = DocType("Item")
    count_query = (
        frappe.qb.from_(items)
        .select(Count("*"))
        .where(items.item_group == group_name)
        .where(items.fh_hs_code.isnull())
    )
    item_count = count_query.run()[0][0]

    update_query = (
        frappe.qb.update(items)
        .set(items.fh_hs_code, item_group.fh_hs_code)
        .where(items.item_group == group_name)
        .where(items.fh_hs_code.isnull())
    )
    update_query.run()

    frappe.msgprint(f"HS Codes updated on {item_count} items.")
