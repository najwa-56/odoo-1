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
        'reports/e_invoicing_b2c_invoice.xml',
        'reports/report.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'ksa_zatca_integration_pos/static/src/xml/payment_screen.xml',
            'ksa_zatca_integration_pos/static/src/xml/receipt_screen.xml',
            'ksa_zatca_integration_pos/static/src/js/reprint_receipt_screen.js',
            'ksa_zatca_integration_pos/static/src/js/payment_screen.js',
            'ksa_zatca_integration_pos/static/src/js/receipt_screen.js',
            'ksa_zatca_integration_pos/static/src/js/order_receipt.js',
            'ksa_zatca_integration_pos/static/src/js/models.js',
            'ksa_zatca_integration_pos/static/src/js/invoice_button.js',
            'ksa_zatca_integration_pos/static/src/js/zatca_report_service.js',
            'ksa_zatca_integration_pos/static/src/css/style.css',
            
        ],
    },

}
