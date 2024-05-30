# -*- coding: utf-8 -*-

{
    'name': 'Pos Multi Barcode Options',
    'version': '1.0',
    'category': 'Product',
    'sequence': 6,
    'author': 'Webveer',
    'summary': "Pos multi barcode option module allows you give create multiple barcode of single product with different options." ,
    'description': """

=======================

Pos multi barcode option module allows you give create multiple barcode of single product with different options.

""",
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml'
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_multi_barcodes/static/src/**/*',
        ],
    },
    'images': [
        'static/description/adds.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 29,
    'currency': 'EUR',
}
