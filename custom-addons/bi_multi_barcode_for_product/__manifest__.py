# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name" : "Product Multiple Barcodes",
    "version" : "17.0.0.0",
    "category" : "Warehouse",
    'summary': 'Product Multi Barcode for Product multiple barcode for product barcode search product based on barcode product barcode generator product different barcode product many barcode product multi barcode for sale multi barcode create multiple barcode for product',
    "description": """
    
        Multi barcode for product in odoo,
        Assigned multiple barcode to single product in odoo,
        Search product based on multiple barcode in odoo,
        Raised warning when assigned same barcode to product in odoo,
        Multiple barcode for sale order or purchase order in odoo,
        Multiple barcode for invoice or vendor bill in odoo,
        Multiple barcode for delivery and shipment in odoo,

    """,
    "author": "BrowseInfo",
    "website" : "https://www.browseinfo.com",
    "price": 10,
    "currency": 'EUR',
    "depends" : ['base','sale_management','purchase','account','stock'],
    "data": [
        'security/ir.model.access.csv',
        'views/res_config_inherit.xml',
        'views/product.xml',
        'views/inherit_view.xml',
    ],
    "auto_install": False,
    "installable": True,
    "live_test_url":'https://youtu.be/6pCMrTdyp_Q',
    "images":["static/description/Banner.gif"],
    'license': 'OPL-1',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
