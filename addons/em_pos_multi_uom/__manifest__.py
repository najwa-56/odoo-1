# -*- coding: utf-8 -*-

{
    'name': 'Pos multi UOM with Barcode',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'ErpMstar Solutions',
    'summary': 'Allows you to sell one products in different unit of measure.',
    'description': "Allows you to sell one products in different unit of measure.",
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'em_pos_multi_uom/static/src/**/*',
        ],
    },
    'images': [
        'static/description/change.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 39,
    'currency': 'EUR',
}
