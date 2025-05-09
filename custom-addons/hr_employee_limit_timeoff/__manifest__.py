{
    'name': 'HR Leave Date Limit',
    'version': '1.0',
    'summary': 'Limit leave requests to only within the next 30 days',
    'author': 'Abeer',
    'depends': ['hr_holidays'],
    'data': [    'views/hr_leave_type_view.xml',],
    'installable': True,
    'application': False,
}
