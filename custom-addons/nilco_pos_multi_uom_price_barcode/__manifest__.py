
{
    'name': "POS Multi UoM Price Barcode",
    'summary': 'POS Price Per Unit of Measure with Barcode',
    'category': 'Point of Sale',
    'version': '17.0.1.0.1',
    'license': "AGPL-3",
    'description': """
         Sell product with multi UoMs in POS with Barcode Scanner.
    """,
    'author': "Nilco Technology",
    'website': "nilcotechnology@gmail.com",
  
    'depends': ['point_of_sale','stock','uom','nilco_pos_multi_uom_price','sale_management','purchase','account'],
    'data': [
        'views/product_view.xml',
    ],
    'currency': 'USD',
    'price': 29,
    'images': [
        'static/description/background.gif','static/description/**.png','static/description/images/logo.jpeg',
    ],
    'installable': True,
    'auto_install': False,
    'assets': {
        'point_of_sale._assets_pos':[
            'nilco_pos_multi_uom_price_barcode/static/src/js/pos_scan.js',
        ],
    },
}
