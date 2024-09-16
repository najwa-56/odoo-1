# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'POS Search with PLU Number',
    'version': '17.0.0.0',
    'category': 'Point of Sale',
    'summary': 'Pos plu search in pos product search with plu number point of sale plu search point of sales plu search point of sale plu number pos price lookup number pos product plu Code pos plu number pos PLU code plu number search on pos search product with plu code',
    'description': """
        
        POS Search with PLU Number Odoo App Odoo App helps users in international supermarkets to control the inventory. User have access to allow or disallow PLU search from POS configuration. User can set PLU(Price Look Up) code or number on each product which will be 4 or 5 digits. User will enter the PLU number on search bar to find the product in POS screen.

    """,
    'author': 'BrowseInfo',
    "price": 20,
    "currency": 'EUR',
    'website': 'https://www.browseinfo.com',
    'depends': ['base','stock', 'point_of_sale','account'],
    'data': [
        'views/pos_config_view.xml',
        'views/product_view_inherit.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'bi_pos_plu_search/static/src/js/posDb.js',
            'bi_pos_plu_search/static/src/js/posStore.js',
            'bi_pos_plu_search/static/src/js/show_plu_product.js',
        ],
    },
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'live_test_url': 'https://youtu.be/Kq-JoiFdi4g',
    "images": ['static/description/POS-Search-PLU-Number-Banner.gif'],
}
