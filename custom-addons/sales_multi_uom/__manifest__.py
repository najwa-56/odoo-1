# -*- coding: utf-8 -*-

{
    'name': 'Sales multi UOM',
    'version': '1.0',
    'category': 'Product',
    'sequence': 6,
    'author': 'Webveer',
    'summary': "",
    'description': """

=======================


""",
    'depends': ['sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml'
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'images': [
        'static/description/custom.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 50,
    'currency': 'EUR',
}
