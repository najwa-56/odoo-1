# -*- coding: utf-8 -*-
{
    "name": "task_assignment",
    "author": "Abeer",
    "website": "",
    "license": "OPL-1",
    "version": "0.0.1",
    "category": "Sales",

    "description": """  This module is useful for task_assignment.""",

    'depends': ['base', 'hr'],
    "data": [
      'security/employee_task_rules.xml',
      "security/ir.model.access.csv",
      "views/emplloyee_task.xml",
      'views/task_name_views.xml',
      'data/cron_data.xml',
      'data/repeat_day_data.xml',
      'data/repeat_month_day_data.xml',
      'data/task_sequence.xml',
      'wizard/view_employee_task_reassign_wizard.xml',
      'data/task_mail_templates.xml',
      'data/task_mail_cancel_templates.xml',
      'data/task_mail_ovrdue_templates.xml',
      'data/task_mail_templates_users.xml',

    ],
    
    "images": [ ],
    "auto_install": False,
    "installable": True,
    "application": True,
    "price": 15,
    "currency": "EUR"
}
