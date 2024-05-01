# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
{
    "name": "Customer Sales Order History",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "license": "OPL-1",
    "version": "0.0.1",
    "support": "support@softhealer.com",
    "category": "Sales",
    
    "summary": "Generate Customer Sales Order History Odoo Give History Of Last Sales Order Module Reorder Product Lines From Sales Order Client Quotation History Find History From SO Get History Of Last Sale Order Search Customer Last Quote History Odoo Last Sales Order History Module SO Reorder Product Lines Client Quotation History Find History From SO App Get Last Sale Order History Application Search Customer Last Quote History Odoo Sales Order History Sale Order History Sale Order History Details Sales Order History Details Re-Order From Sales History Re-Ordering From Sale Order History Customer Sale Order History Customer Sale History Re-Ordering From Sale History Re-Order From Sales Order History Customer Sales Order History Customer Sales History Re-Order Customer Sales Order Re-Ordering Customer Sale Order Sales History Of Customer Sale Order History Of Customer SO History SO History Details Re-Ordering From SO History Customer SO History Re-Ordering From SO History",
    
    "description": """  This module is useful for giving customer sales history from the last sales orders and easily reordering product lines from the previous sale order.""",

    "depends": ["sale_management"],
    "data": [
        "security/ir.model.access.csv",
        "security/stages_security.xml",
        "views/sale_order_history.xml",
        "views/res_config_settings.xml",
        "views/sale_order_stages.xml",
        "data/stages_data.xml",
    ],
    
    "images": ["static/description/background.png", ],
    "auto_install": False,
    "installable": True,
    "application": True,
    "price": 15,
    "currency": "EUR"
}
