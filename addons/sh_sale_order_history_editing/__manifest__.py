# -*- coding: utf-8 -*-
{
    "name": "Customer Sales Order History Editing",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "license": "OPL-1",
    "version": "0.0.1",
    "support": "support@softhealer.com",
    "category": "Sales",
    "summary": "Generate Customer Sales Order History Last Sales Order History sale history sales history SO Reorder Product Lines Client Quotation History From SO Last Sale Order History Search Customer Last Quote History Quotation History Odoo",
    "description": """
This module useful to give customer sales history from last sales orders,
easily reorder product lines from the previous sale order.
Generate Customer Sales Order History Odoo
Give History Of Last Sales Order Module, Reorder Product Lines From Sales Order,
Client Quotation History, Find History From SO, Get History Of Last Sale Order,
Search Customer Last Quote History Odoo.
Last Sales Order History Module, SO Reorder Product Lines,
Client Quotation History, Find History From SO App,
Get Last Sale Order History Application, Search Customer Last Quote History Odoo.
""",
    "depends": ["sale_management","account"],
    "data": [
        "views/sale_order_history.xml",  # Corrected filename
    ],
    "images": ["static/description/background.jpg"],
    "live_test_url": "https://youtu.be/_NvHHWaev1k",
    "auto_install": False,
    "installable": True,
    "application": True,
    "price": 15,
    "currency": "EUR"
}
