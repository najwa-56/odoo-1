{
    'name': 'HR Expense Custom',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Filters expense products based on assigned users using record rules.',
    'author': 'Adnan',
    'depends': ['hr_expense'],
    'data': [
        'security/rules.xml',
        'views/product_product_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
