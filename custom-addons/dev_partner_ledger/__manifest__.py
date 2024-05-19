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
    'name': 'Partner Ledger On Screen',
    'version': '17.0.1.0',
    'sequence': 1,
    'category': 'Sales',
    'description':
        """
         Odoo app will display Partner Ledger on customer screen

    Partner Ledger 
    Odoo partner Leadger 
    Odoo partner Details ledger
    Odoo due balance 
    Odoo Partner ledger Balance
        
    """,
    'summary': 'Odoo app will display Partner Ledger on customer screen,partner Leadger, Partner move line, partner due balance, partner overdue report',
    'depends': ['sale','account'],
    'data': [
        'views/partner_view.xml',
    ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    # author and support Details =============#
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'price':19.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
    'pre_init_hook' :'pre_init_check',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
