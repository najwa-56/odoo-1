
{
    'name': 'Sales Man Manager',
    'version': '17.0.1.0.0',
    'summary': 'Manage salespeople and their dashboards',
    'description': """
        This module allows supervisors to manage their salespeople and their dashboards.
    """,
    'category': 'Sales',
    'author': 'Lovable',
    'website': 'https://lovable.dev',
    'depends': ['hr', 'ks_dashboard_ninja','customer_route_management', 'sale'],
    'data': [
        'security/salesman_manager_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/hr_employee_views.xml',
        'views/ks_dashboard_views.xml',
        'views/sales_man_views.xml',
        'views/weekly_routs_views.xml',
        'views/my_routes_views.xml',
        'views/daily_visit_views.xml',
        'views/route_line.xml',
        'views/weekly_routs_report.xml',
        'views/daily_visit_report.xml',
        'views/sale_order_view.xml',
        'views/account_move_view.xml',
        'views/daily_realtime_report_views.xml',
        'wizard/partner_update.xml',
        'views/res_partner_views.xml',
        'views/partner_adjustment.xml',
        'views/account_payment.xml'


    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
