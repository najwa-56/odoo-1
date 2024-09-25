{
    "name": "Print / Downlod Invoice ",
    "author": "IdeaCode Academy",
    'category': 'Sales/Point of Sale',
    "depends": ["point_of_sale"],
    "data": [
        "views/pos_config.xml",
    ],
    'assets': {
        # Main PoS assets, they are loaded in the PoS UI and in the PoS unit tests
        'point_of_sale._assets_pos': [
            # PoS files
            'pos_should_download_invoice/static/src/**/*.js',
        ]
    },

    "license": "LGPL-3",
    'installable': True,
    'auto_install': True,
"price": "0",
    "currency": "USD",
}
