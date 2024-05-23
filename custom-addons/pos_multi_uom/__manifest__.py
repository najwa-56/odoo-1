# -*- coding: utf-8 -*-

{
    'name': 'Pos multi UOM',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'Webveer',
    'summary': 'Pos multi UOM allows you to sell one products in different unit of measure.',
    'description': "Pos multi UOM allows you to sell one products in different unit of measure.",
     'license': 'AGPL-3',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_multi_uom/static/src/**/*',
        ],
    },
    'images': [
        'static/description/change.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 29,
    'currency': 'EUR',
}
