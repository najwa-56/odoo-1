# -*- coding: utf-8 -*-
{
    'name': "KSA Zatca Phase-2 Point Of Sale Integration",
    'summary': """
        Phase-2 of ZATCA e-Invoicing(Fatoorah): Integration Phase, its include solution for KSA business""",
    'description': """
        Phase-2 of ZATCA e-Invoicing(Fatoorah): Integration Phase, its include solution for KSA business
    """,
    'live_test_url': 'https://youtu.be/ZEG1JcXuHF0',
    "author": "Alhaditech",
    "website": "www.alhaditech.com",
    'license': 'OPL-1',
    'images': ['static/description/cover.png'],
    'category': 'Invoicing',
    'version': '16.1.1',
    'price': 300, 'currency': 'USD',
    'depends': ['ksa_zatca_integration', 'point_of_sale'],
    'external_dependencies': {
        'python': ['cryptography', 'lxml']
    },
    'data': [
        'views/pos_order.xml',
        'views/res_company.xml',
        'views/pos_payment_method.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'ksa_zatca_integration_pos/static/src/xml/PaymentScreen.xml',
            'ksa_zatca_integration_pos/static/src/js/ReprintReceiptScreen.js',
            'ksa_zatca_integration_pos/static/src/js/PaymentScreen.js',
            'ksa_zatca_integration_pos/static/src/js/ReceiptScreen.js',
            'ksa_zatca_integration_pos/static/src/js/models.js',
            'ksa_zatca_integration_pos/static/src/css/style.css',
        ],
    },

}
