# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.
{
    "name": "All In One Secondary Unit Of Measure",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Extra Tools",
    "license": "OPL-1",
    "summary": "purchase secondary uom Purchase Secondary Unit of Measure po secondary uom PO Secondary Unit of Measure Purchase Order Secondary Unit of Measure Purchase Order Secondary UOM Request for quotation secondary uom Request for quotation secondary unit of measure rfq secondary uom rfq secondary unit of measure multiple uom multiple unit of measure multiple secondary uom multiple secondary unit of measure invoice secondary uom invoice secondary unit of measure manage multiple uom multiple unit of measure Account Secondary Unit Of Measure Account Secondary UOM vendor bill secondary uom vendor bill secondary unit of measure payment secondary uom payment secondary unit of measure Credit Note Secondary Unit of Measure Credit Note Secondary UOM Debit Note Secondary Unit of Measure Debit Note Secondary UOM Receipt Secondary Unit of Measure Receipt Secondary UOM multiple secondary uom multiple secondary unit of measure Inventory Secondary UOM Stock Secondary UOM Stock Unit Of Measure Delivery Order Secondary UOM Incoming Order Secondary UOM Delivery Order Secondary Unit Of Measure Incoming Order Secondary Unit Of Measure Inventory Unit of Measure Odoo Inventory Secondary Unit of Measure Internal Transer Secondary Unit Of Measure Internal Transer Secondary UOM multiple uom multiple unit of measure multiple secondary uom multiple secondary unit of measure Sale Secondary Unit of Measure Sale Order Secondary Unit of Measure Sales Secondary UOM Sales Secondary Unit Of Measure Sale Order Secondary UOM Quotation Secondary UOM Sales secondary unit of measure Sale Secondary uom multiple uom multiple unit of measure multiple secondary uom multiple secondary unit of measure All In One Secondary UOM All in one secondary UOM Odoo All in one secondary Unit of measure Odoo all secondary units of measures all secondary unit of measure stock secondary unit of measure Bill Secondary unit of measure Credit note secondary unit of measure secondary unit of measure for warehouse secondary unit of measure for Inventory secondary unit of measure for Purchase secondary unit of measure for Sale secondary unit of measure for Accounts secondary unit of measure for Invoices Secondary unit of measure Product Product secondary unit of measure secondary unit of measure for product UOM all in one convert UOM convert unit of measure",
    "description": """
Do you have more than one unit of measure in product ?
Yes! so, you are at right palce.
We have created beautiful module to manage secondary unit of product in sales,
purchase,inventory operations and accounting.
It will help you to get easily secondary unit value.
so you don't need to waste your time to calculate that value.
you can also show that value in pdf reports
so your customer/vendor also easily understand that.
""",
    "version": "0.0.4",
    "depends": [
        "sale_management",
        "account",
        "purchase",
        "stock",
        "product_multi_uom_price",
    ],
    "application": True,
    "data": [
        "security/sh_secondary_unit_group.xml",
        "views/product_template_views.xml",
        "views/product_product_views.xml",
        "views/sale_order_views.xml",
        "views/purchase_order_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_move_views.xml",
        "views/account_move_views.xml",
        "views/stock_scrap_views.xml",
        "report/sale_order_templates.xml",
        "report/purchase_order_templates.xml",
        "report/account_move_templates.xml",
        "report/stock_picking_templates.xml",
        "report/stock_picking_deliveryslip_templates.xml",
        "report/invoice_report_view.xml",
    ],
    "auto_install": False,
    "installable": True,
    "price": 25,
    "currency": "EUR",
    "images": ['static/description/background.png', ],
    "live_test_url": "https://www.youtube.com/watch?v=KrX_zvlWRdI&feature=youtu.be",
}
