# -*- coding: utf-8 -*-

{
    "name" : "Mixed Discount in Sale, Purchase and Invoice",
    "author": "Edge Technologies",
    "version" : "1.0",
    "live_test_url":'https://youtu.be/lKPn7gGi2A0',
    "images":["static/description/main_screenshot.png"],
    'summary': 'Multiple discount invoice mixed discounts sale discount multiple discounts invoice purchase multiple discounts sale multi discount on sale multi discount on purchase multi discount on invoice multiple discounts on sale offer discount double discounts deals',
    "description": """Mixed discount in sale, purchase and invoice helps to give mixed discounts to the customers. in sale and purchase lines you can add mixed discount amounts separated by '+'. first discount would be applied to the first amount and then to the calculated amount.


Multiple discounts 
Mixed dicounts sale dicount multiple discounts invoice purchase multiple discounts sale 
Multi discount on sale multi discount on purchase multi discount on invoice step discount
Step discount apply multiple discount for an order
Many discount on invoice multiple discounts on purchase 
Discount on discount
Offer on offer special discounting 
Multi dicounts  multi-buy promotions multiple discounts multi-policy discount
Offer discounts
Double discounts 
Promotions discounts 
Specific discounts discounts
Offers discount coupons & promo
Deals and discount

    """,
    "license" : "OPL-1",  
    "depends" : ['base','sale_management','purchase','account','stock'],
    "data": [
        'views/sale_order_line_inherit_views.xml',
        'security/mixed_discount_security.xml',
        'report/report_purchase.xml',
    ],
    "auto_install": False,
    "installable": True,
    "price": 25,
    "currency": 'EUR',
    "category" : "Sales",
    
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
