
# -*- coding: utf-8 -*-

{
    'name': 'Editing',
    'version': '1.0',
    'category': 'Product',
    'sequence': 6,
    'author': 'Najwa and Abeer',
    'summary': "A module for editing purposes",
    'description': """This module provides editing functionality.""",
    'depends': ['sale_management', 'stock','point_of_sale'],
    'data': [
        'views/editing.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'editing/static/src/**/*',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'website': 'https://www.example.com',
    'auto_install': False,
}