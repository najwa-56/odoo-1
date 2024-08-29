# -*- coding: utf-8 -*-

{
    'name': 'Pos multi UOM',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'Azkob',
    "website": "https://www.azkob.com",
    'summary': 'Allows you to sell one products in different unit of measure.',
    'description': "Allows you to sell one products in different unit of measure.",
    'depends': ['point_of_sale'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'ss_pos_multi_uom/static/src/js/pos.js',
        ],
        'web.assets_qweb': [
            'ss_pos_multi_uom/static/src/xml/**/*',
        ],
    },
    'images': [
        'static/description/popup.jpg',
    ],
    'installable': True,
    'website': 'https://azkob.com',
    'auto_install': False,
    'price': 29,
    'currency': 'EUR',
}
