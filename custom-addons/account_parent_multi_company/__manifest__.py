##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2020 - Today O4ODOO (Omal Bastin)
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################
{
    'name': "Consolidated Chart of Account Hierarchy",
    'summary': """
        Ability to open consolidated chart of account hierarchical view for multi company""",
    'description': """
This module Adds two Consolidated Chart of account hierarical view.
        * 1. Based on same account code: If account structure is same for every company.
        * 2. Based on account type: If each company is in different country
        * Provide PDF and XLS reports
    
    """,

    'author': 'Omal Bastin / O4ODOO',
    'license': 'OPL-1',
    'website': 'http://o4odoo.com',
    'category': 'Accounting &amp; Finance',
    'version': '17.0.1.0.3',
    'depends': ['account_parent'],
    'data': [
        'views/open_chart_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'currency': 'EUR',
    'price': '50.0',
    'installable': True,
}