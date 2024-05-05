# -*- coding: utf-8 -*-
{
    "name": "Limit Cash Control in Odoo Point of Sale",
    "version": "0.1.2",
    "category": "Sales/Point of Sale",
    'summary': "Customize Cash Control Mechanism in Point of Sales",
    "author": "Ewetoye Ibrahim",
    "auto_install": False,
    "depends": ["point_of_sale"],
    'installable': True,
    'application': False,
    'data': ['pos_config.xml'],
    "price": 120,
    "currency": 'USD',
    'images': ['static/description/limit_cash_control.jpg'],
    'license': 'OPL-1',
    'website': 'https://youtu.be/qjOuFaAxWNE',
    'assets':{
        'point_of_sale._assets_pos': [
            'limit_cash_control/static/src/**/*',
        ],
    }
}