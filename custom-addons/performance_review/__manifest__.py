{
    'name': 'Odoo 17 HR performance_review',
    'category': 'Generic Modules/Human Resources',
    'version': '17.0.0.0',
    'sequence': 1,
    'author': 'Abeer Saleh',
    'summary': 'performance_review For Odoo 17 Community Edition',
    'description': "Odoo 17 performance_review",
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'task_assignment',  # ✅ Correct name of your actual task module

    ],
    'data': [
        "security/ir.model.access.csv",
        'views/performance_review_menu.xml',
        'views/employee_performance.xml',

    ],
    'images': [],
    'application': True,
}