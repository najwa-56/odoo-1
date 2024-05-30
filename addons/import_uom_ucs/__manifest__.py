# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO Open Source Management Solution
#
#    ODOO Addon module by Uncanny Consulting Services LLP
#    Copyright (C) 2023 Uncanny Consulting Services LLP (<https://uncannycs.com>).
#
##############################################################################
{
    "name": "Import UOM",
    "summary": "Import UOM",
    "version": "17.0.1.0.0",
    "category": "sale",
    "website": "https://uncannycs.com",
    "author": "Uncanny Consulting Services LLP",
    "maintainers": "Uncanny Consulting Services LLP",
    "license": "Other proprietary",
    "application": False,
    "installable": True,
    "preloadable": True,
    "depends": [
        "base", "sale_management", "purchase", "stock"
    ],
    "images": ["static/description/banner.gif"],
    "data": [
        "security/ir.model.access.csv",
        "data/sample_import_uom_view.xml",
        "wizard/import_uom_wizard.xml",
    ],
    "price": 5,
    "currency": "USD",
}
