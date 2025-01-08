# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Candidroot Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.
{
    'name': 'Web Chatter Position',
    'version': '17.0.1.0',
    'summary': 'Chatter Position Custom Configuration based on users specific',
    'author': 'Candidroot Solutions Pvt. Ltd.',
    'description': """
			With the help of this module user can configure chatter position based on specific position
			like 'Side', 'Bottom' & 'Responsive'.
    """,
    'website': 'www.candidroot.com',
    'depends': ['web', 'mail'],
    'category': 'Extra Tools',
    'data': [
        'views/res_users.xml',
        'views/web.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/web_chatter_position_cr/static/src/js/web_chatter_position.esm.js',
            '/web_chatter_position_cr/static/src/scss/chatter_custom.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'live_test_url': 'https://youtu.be/3ZlMi8o6D0E',
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
