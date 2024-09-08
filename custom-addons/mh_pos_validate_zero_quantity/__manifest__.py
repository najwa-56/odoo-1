# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'POS Zero Quantity and Empty Order Validation',
    'summary': """POS Zero Quantity and Empty Order Validation""",
    'sequence': -1,
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'author': 'Software Box',
    'website': 'http://softwarebox18@gmail.com',
    'module_type': 'industries',
    'price': '3.25',
    'currency': 'USD',
    'depends': ['point_of_sale'],
    'data': [
        # 'views/views.xml',
        # 'security/ir.model.access.csv',
    ],
    'images': ['static/description/main.PNG'],
    'installable': True,
    'application': True,
    'assets': {
        'point_of_sale._assets_pos': [
            'mh_pos_validate_zero_quantity/static/src/app/screens/product_screen/action_pad/payment_button.js',
        ]
    },
    'license': 'OPL-1',
}
