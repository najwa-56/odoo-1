# -*- coding: utf-8 -*-

{
    "name": "Automated Credit/Debit Note Generation from Return Picking",
    "version": "17.0.1.0.1",
    "category": "Sales",
    "summary": "For creating credit note and debit note while picking.",
    "description": "We can create credit note or debit note while return the"
    " picking by using this module in Odoo 17. ",
  
    "depends": ["sale_management", "stock", "purchase"],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_picking_views.xml",
        "views/stock_return_picking_views.xml",
        "wizard/return_move_views.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
