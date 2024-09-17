# -*- coding: utf-8 -*-

{
    'name': 'Pos total qty',
    'version': '0.1',
    'author': 'Buildfish',
    'category': 'Point of Sale',
    'summary': 'Pos quantity of products',
    'website': 'build-fish.com',
    'license': 'AGPL-3',
    'description': """
        Pos Quantity of products.
    """,
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            "/bf_pos_total_qty/static/src/js/total_qty.js",
            "/bf_pos_total_qty/static/src/css/pos.css",
            '/bf_pos_total_qty/static/src/xml/**/*',
        ],
    },
    'price': 11.00,
    'currency': 'USD',
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
}
