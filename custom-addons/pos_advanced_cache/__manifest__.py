# -*- coding: utf-8 -*-

{
    'name': 'Pos Advanced Cache',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'Webveer',
    'summary': 'Pos advanced cache allows to load product very fast.',
    'description': "Pos advanced cache allows to load product very fast.",
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_cache_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_advanced_cache/static/src/js/pos_cache.js',
        ]
    },
    'images': [
        'static/description/pos.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 129,
    'currency': 'EUR',
}
