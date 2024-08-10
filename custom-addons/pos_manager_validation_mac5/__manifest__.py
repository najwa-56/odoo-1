{
    'name': '[Original] POS Manager Validation using User PIN',
    'version': '17.0.2.0',
    'summary': """Validation of Closing POS, Order Deletion, Order Line Deletion,
                  Discount Application, Order Payment, Price Change and Decreasing Quantity,
Odoo POS validation, Odoo POS validate, Odoo POS confirmation, Odoo POS confirm,
Odoo POS checking, Odoo POS check, Odoo POS access, Odoo POS user, user access, access right,
delete order, delete order line, POS closing, closing POS, decrease quantity, POS Cash In/Out,
POS Cash Out/In""",
    'description': """
POS Manager Validation using User PIN
=====================================

This module allows validation for certain features on POS UI
if the cashier has no access rights or not a manager

Per Point of Sale, you can define manager validation for the following features:
* POS Closing
* Order Deletion
* Order Line Deletion
* Discount Application
* Order Payment
* Price Change
* Decresing Quantity
* Cash In/Out


Compatibility
-------------

This module is compatible and tested with these modules:
* Restaurant module (pos_restaurant)
""",
    'category': 'Sales/Point of Sale',
    'author': 'MAC5',
    'contributors': ['MAC5'],
    'website': 'https://apps.odoo.com/apps/modules/browse?author=MAC5',
    'depends': [
        'point_of_sale',
    ],
    'data': [
        'views/res_users_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_manager_validation_mac5/static/src/js/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': ['static/description/banner.gif'],
    'price': 24.99,
    'currency': 'USD',
    'support': 'mac5_odoo@outlook.com',
    'license': 'OPL-1',
    'live_test_url': 'https://youtu.be/pk07THpL7Ks',
}
