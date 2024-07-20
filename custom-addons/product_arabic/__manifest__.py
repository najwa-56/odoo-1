# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU Odoo Proprietary License
#    v1.0 (OPL-1).
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Odoo Proprietary License v1.0 (OPL-1) for more details.
#
#    You should have received a copy of the GNU Odoo Proprietary
#    License v1.0 (OPL-1) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': 'Arabic Product Name in POS',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': "Generates Arabic product names in POS product screen and"
               "Receipt",
    'description': "This module enables user to view the arabic name of product"
                   "in POS product screen and POS Receipts",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'depends': ['point_of_sale','account','sale'],
    'data': ['views/product_template_views.xml'],
    'assets': {
        'point_of_sale._assets_pos': [
            'product_arabic/static/src/js/orderline.js',
            'product_arabic/static/src/js/ProductCard.js',
            'product_arabic/static/src/xml/ProductCard.xml',
            'product_arabic/static/src/xml/arabic_name_templates.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'OPL-1',
    'price': 9.99,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': False,
}
