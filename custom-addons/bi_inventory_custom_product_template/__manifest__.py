# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{

    "name" : "Product Template for Purchase Order",
    "version" : "17.0.0.0",
    "summary": "Create Product Template with multiple products purchase order product template purchase order PO template  Apply Product Template for Purchase purchase template for product create template for purchase order po product template for PO template for product",
    "category": "Purchase",
    
    "description": """
    This module helps user to create Product Template with multiple products and on selection Product Template from Purchase Order related products will get displayed in Purchase Order.
    Odoo purchase order product template purchase order PO template
    odoo purchase template for product create template for purchase order
    odoo apply template for purchase order po product template for PO
    Create and Apply Product Template for Purchase Order Odoo Apps

    """ ,
    "price": 9,
    "currency": 'EUR',
    "depends" : ["base", "purchase"],
    "data": [
        'views/purchase_custom_view.xml',
	     ],
    "author": "BrowseInfo",
    "website":'https://www.browseinfo.com/demo-request?app=bi_purchase_custom_product_template&version=17&edition=Community',
    "installable": True,
    "application": True,
    'license':'OPL-1',
    "auto_install": False,
    "images":["static/description/Banner.gif"],
    "live_test_url":'https://www.browseinfo.com/demo-request?app=bi_purchase_custom_product_template&version=17&edition=Community',

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
