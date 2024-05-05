# -*- coding: utf-8 -*-
{
    "name": "Limit Cash Control in Odoo Point of Sale editing",
    "version": "0.1.2",
    "category": "Sales/Point of Sale",
    'summary': "Customize Cash Control Mechanism in Point of Sales",
    "author": "Ewetoye Ibrahim",
    "auto_install": False,
    "depends": ["point_of_sale"],
    'installable': True,
    'application': False,
    "price": 150,
    "currency": 'USD',
    'assets': {
        'point_of_sale.assets': [
            'limit_cash_control_editing/static/src/xml/**/*.xml', ],
    },
    'images': ['static/description/limit_cash_control.jpg'],
    'license': 'LGPL-3',
}
