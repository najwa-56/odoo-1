# -*- coding: utf-8 -*-
{
    'name': "POS Speed Up | POS Performance",
    'summary': """
        A solution to the performance problem of loading POS. This solution has been deployed to the retail chain of 500 stores with more than 1 000 000 customers and more than 100 000 products with a speed of 10 seconds.
        """,
    'description': """
        Pulling all customers and products to the client is not nearly possible with a large number of stores and a large number of customers and a large number of products, including using data cache on the client side or cache data on the server side. When loading data for the first time or suddenly losing data cache, it is a disaster for a retail chain.
    """,
    'author': "Dev Happy",
    'website': "https://www.dev-happy.com",
    'category': 'Point of Sale',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale'],

    # always loaded
    'data': [
        'views/res_company_view.xml',
        'views/product_product_view.xml',
    ],
    'assets': {
    'point_of_sale.assets': [
        '/pos_speed_performance/static/src/js/models.js',
        '/pos_speed_performance/static/src/js/screens/ClientListScreen/ClientListScreen.js',
        '/pos_speed_performance/static/src/js/screens/ProductsWidget/ProductsWidget.js',
    ],
    'web.assets_qweb': [
    ],
},


    'live_test_url':'https://youtu.be/Y6NOPP6gMYE',
    'images':['static/description/banner.png'],
    'currency': 'EUR',
    'support':"dev.odoo.vn@gmail.com",
    'price': 99.99,
    'license': 'OPL-1',
}
