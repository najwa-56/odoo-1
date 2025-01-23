# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

{
    'name': "Stock Inventory Report",
    'category': 'Inventory',
    'version': '17.0.1.0',
    'author': 'Equick ERP',
    'description': """
        This Module allows you to generate Stock Inventory Report PDF/XLS wise.
        * Allows you to Generate Stock Inventory PDF/XLS Report.
        * Support Multi Warehouse And Multi Locations.
        * Group By Product Category Wise.
        * Filter By Product/Category Wise.
    """,
    'summary': """ This Module allows you to generate Stock Inventory Report. Inventory Report | Stock Report | Real Time Inventory Report | Real Time Stock Report | Stock card | Inventory Report | Odoo Inventory Report | location wise report.""",
    'depends': ['base', 'stock'],
    'price': 30,
    'currency': 'EUR',
    'license': 'OPL-1',
    'website': "",
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_stock_inventory_view.xml',
        'report/report.xml',
        'report/stock_inventory_template_report.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: