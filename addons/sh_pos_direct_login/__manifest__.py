# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
{
    "name": "POS Direct Login Without Odoo Backend",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Point of Sale",
    "license": "OPL-1",
    "summary": "Quick POS Login Without Backend Point Of Sale Login POS Screen Login POS Session Login Point Of Sales Direct POS Login POS Sign In POS Signin Direct Sign In POS Access Direct Redirect To POS Screen Point Of Sale Session Login Odoo",
    "description": """ POS Direct Login Without Odoo Backend, This module is very useful for pos user. 
    Normally pos user logged its redirect to odoo backend than user need to go point of sale and start/resume session. Our module helps to save this unusual time, It will directly redirect you to pos screen instead of odoo backend.
redirect to pos screen app, quick pos login module, pos login without backend, point of sale login odoo, quick pos login, responsive point of sale login""",
    "version": "0.0.1",
    "depends": ['point_of_sale','web'],
    "application": True,
    "data": [
        'views/res_users.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'sh_pos_direct_login/static/src/**/*',
        ],
    },
    "images": ["static/description/background.jpg", ],
    "auto_install": False,
    "installable": True,
    "price": 15,
    "currency": "EUR"
}
