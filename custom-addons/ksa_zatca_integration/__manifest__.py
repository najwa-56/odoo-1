# -*- coding: utf-8 -*-
{
    'name': "KSA Zatca Phase-2",
    'summary': """
        Phase-2 of ZATCA e-Invoicing(Fatoorah): Integration Phase, its include solution for KSA business""",
    'description': """
        Phase-2 of ZATCA e-Invoicing(Fatoorah): Integration Phase, its include solution for KSA business
    """,
    'live_test_url': 'https://youtu.be/UaXFwibu0zU',
    "author": "Alhaditech",
    "website": "www.alhaditech.com",
    'license': 'OPL-1',
    'images': ['static/description/cover.png'],
    'category': 'Invoicing',
    'version': '17.9.0',
    'price': 890, 'currency': 'USD',
    'depends': ['account', 'sale', 'l10n_sa', 'purchase', 'account_debit_note', 'account_edi_ubl_cii'],
    'external_dependencies': {
        'python': ['cryptography', 'lxml', 'qrcode', 'fonttools']
    },
    'data': [
        # 'views/update.xml',
        'security/groups.xml',
        'data/data.xml',
        'reports/account_move.xml',
        'views/account_move.xml',
        'views/res_partner.xml',
        'views/res_company.xml',
        'views/account_tax.xml',
        'views/product_template.xml',
        'views/product_product.xml',
        'reports/e_invoicing_b2b.xml',
        'reports/e_invoicing_b2c.xml',
        'reports/report.xml',
        'wizard/account_debit_note.xml',
        'wizard/account_move_reversal.xml',
        'views/client_action.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ksa_zatca_integration/static/src/css/style.css',
            'ksa_zatca_integration/static/src/js/zatca_dashboard.js',
            'ksa_zatca_integration/static/src/xml/zatca_dashboard.xml',
        ],
    },
}
