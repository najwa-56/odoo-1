{
    'name': 'payroll report excel (engine)',
    'version': '1.0',
    'category': 'payroll',
    'sequence': 60,
    'summary': 'Dynamic Payroll Report Excel',
    'description': "It shows payroll report in excel for given month,create your own report",
    'author':'Mutwkil Faisal',
    'depends': ['base','hr', 'om_hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_bank.xml',
        'views/payroll_report.xml',
        'wizard/payroll_report_wiz.xml'
      ],
    'images': ['static/description/cover.png'],
    'auto_install': False,
    'installable': True,
    'application': True,
    'support': 'mutwkil.faisal@gmail.com',
}
