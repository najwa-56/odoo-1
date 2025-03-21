# -*- coding: utf-8 -*-
{'name': "Employee Contract Allowances ",
 'summary': """
       Multiple Allowances for employee""",
 'description': """
            Add many allowances to any employee, include in payroll and END of Service Reward calculation
    """,
 'author': "I VALUE solutions",
 'website': "https://ivalue-s.com",
 'email': "info@ivalue-s.com",
 'license': "OPL-1",
 'category': 'HR',
 'version': '0.1',
 'images': ['static/description/Banner.png'],
 'depends': ['base', 'mail', 'hr_contract', 'om_hr_payroll'],
 'data': [
     'security/ir.model.access.csv',
     'views/hr_contract_views.xml',
 ],

 }
