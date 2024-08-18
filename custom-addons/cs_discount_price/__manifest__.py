# -*- coding: utf-8 -*-
{
    "name": "Discount On Price",
    "version": "17.0.0.1",
    "summary": "Calculates Discount percentage on change of Discount Price.",
    'sequence': 1,
    "discription": """
        The Discount Calculator Application is designed to effortlessly compute discount percentages based on changes in price, as well as determine the discounted price from a given discount percentage.
    """,
    "author": "Code Sparks",
    "website": "",
    "license": "LGPL-3",
    "category": "Invoicing",
    "depends": ["base", "account"],
    "data": [
        "views/account_move_inherit.xml"
    ],
    "images": ['static/description/banner.png'],
    "installable": True,
    "auto_install": False,
    "application": True,
}
