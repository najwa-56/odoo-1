# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

{
    'name': 'Employee Bonus Management',
    'version': '17.0.1.0',
    'sequence': 1,
    'category': 'Human Resources/Employees',
    
    'summary': 'Apps will add bonus management functioality for employee,Bonus Allowance in Employee Payslip,Bonus Notification to many employee,Employee Bonus and Payroll Integration,Employee bonus,hr bonus, hr employee bonus, bonus management,Bonus for Employee',
   
    'depends': ['om_hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_bonus.xml',
        'data/hr_employee_bonus_email_data.xml',
        'data/hr_payroll_data.xml',
    ],
    'demo': [],
    'assets': {},
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
    
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
