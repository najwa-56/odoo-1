# -*- coding: utf-8 -*-

{
    "name" : "POS Access Rules - Allow Disable Access for POS",
    "author": "Edge Technologies",
    "version" : "17.0",
    "live_test_url":'https://youtu.be/n_6K78DfMoI',
    "images":["static/description/main_screenshot.png"],
    "price": 15,
    "currency": 'EUR',
    'summary': 'Point of sales access rights on pos access rights on point of sale access rights pos access rule pos disable button pos disable access allow and disable pos access pos disable payment pos disable qty pos disable price pos disable discount pos hide button.',
    "description": """
    
        This app help to disable buttons from pos screen.
    """,
    "license" : "OPL-1",
    "depends" : ['base','point_of_sale'],
    "data": [
        'views/pos_js.xml',
    ],

    'assets': {
        'point_of_sale._assets_pos': [
            'pos_access_rights_app/static/src/js/PaymentScreen.js',
        ],
    },

    "auto_install": False,
    "installable": True,
    "category" : "Point of Sale",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: