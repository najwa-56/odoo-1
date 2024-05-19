# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Receipt and Payment Voucher Print(Payment Receipt)',
    'version': '17.0.0.0',
    'category': 'Accounting',
    'sequence': 1,
    'summary': 'Receipt and Payment Voucher Print(Payment Receipt).',
    'description': """
This module helps to print receipt and payment voucher with both customer/vendor copy and office copy.
Also it automatically loads the sub currency of each country and which in turn helps to show the amount in words. 
    """,
    'website': 'http://technaureus.com/',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'depends': ['account'],
    'price': 8,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'data': [
        'report/layout.xml',
        'report/report_header.xml',
        'report/report_footer.xml',
        'report/account_report.xml',
        'report/report_voucher.xml',
    ],
    'demo': [],
    'css': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
