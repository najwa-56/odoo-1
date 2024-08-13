
{
    'name': "POS Multi UoM Price",
    'summary': 'POS Price Per Unit of Measure',
    'category': 'Point of Sale',
    'version': '17.0.1.0.1',
    'license': "AGPL-3",
    'description': """
         Sell product with multi UoMs in POS.
         POS Multi UoM Price
    """,
    'author': "Nilco Technology",
    'website': "nilcotechnology@gmail.com",
    'currency': 'USD',
    'price': 25.6,
    'depends': ['point_of_sale','stock','uom','base'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/posz_js.xml',

    ],
    'images': [
        'static/description/background.gif','static/description/**.png','static/description/images/logo.jpeg',
    ],
    'installable': True,
    'auto_install': False,
    'assets': {
        'point_of_sale._assets_pos':[
            'nilco_pos_multi_uom_price/static/src/js/multi_uom_price.js',
            'nilco_pos_multi_uom_price/static/src/js/models.js',
            'nilco_pos_multi_uom_price/static/src/js/new_file.js',
            'nilco_pos_multi_uom_price/static/src/xml/multi_uom_price.xml',

        ],
    },
}
