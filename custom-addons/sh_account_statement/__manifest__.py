# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Customer Account Statement | Customer Overdue Statement | Vendor Bank Statement | Vendor Bank Overdue Statement",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "version": "0.0.8",
    "category": "Accounting",
    "summary": "Customer Bank Statement Supplier Statement Overdue Statement Print Customer Statement Report Print Vendor Statement Payment Reminder customer payment followup send customer statement print account statement print overdue statement customer overdue statement print customer overdue statement customer statement generator send overdue statement client Payment Followup Print client Statement Report client Bank Statement Client Statement Contact Statement Overdue Statement Partner Statement of Account Print Overdue Statement send client statement Account Statement Report print account statement client overdue statement print client overdue statement client statement generator send overdue statement user Payment Followup Print user Statement Report user Bank Statement user Statement Contact Statement Overdue Statement Partner Statement of Account Print Overdue Statement send user statement Account Statement Report print account statement user overdue statement print user overdue statement user statement generator send overdue statement partner Payment Followup Print partner Statement Report partner Bank Statement partner Statement Contact Statement Overdue Statement Partner Statement of Account Print Overdue Statement send partner statement Account Statement Report print account statement partner overdue statement print partner overdue statement partner statement generator send overdue statement Odoo vendor statement Odoo",
    "description": """This module allows customers or vendors to see statements as well as overdue statement details. You can send statements by email to the customers and vendors. You can also see customers/vendors mail log history with statements and overdue statements. You can also send statements automatically weekly, monthly & daily, or you can send statements using cron job also. You can filter statements by dates, statements & overdue statements. You can group by statements by the statement type, mail sent status & customers/vendors. You can print statements and overdue statements.""",
    "depends": [
        'account'
    ],

    'assets': {

        'web.assets_frontend': [
            'sh_account_statement/static/src/js/portal.js',
        ]

    },

    "data": [
        'security/sh_account_statement_groups.xml',
        'security/ir.model.access.csv',
        'views/res_user_views.xml',
        'wizard/mail_compose_views.xml',
        'views/sh_partner_mail_history_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/sh_statement_config_views.xml',
        'report/sh_customer_statement_report_templates.xml',
        'report/sh_customer_due_statement_report_templates.xml',
        'report/sh_vendor_statement_report_templates.xml',
        'report/sh_vendor_due_statement_report_templates.xml',
        'report/sh_customer_filter_statement_report_templates.xml',
        'report/sh_vender_filtered_statement_report_templates.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'views/sh_customer_statement_portal_templates.xml',
        'views/sh_vendor_statement_portal_templates.xml',
        'wizard/sh_partners_mass_update_wizard_views.xml',
        'wizard/sh_partners_config_mass_update_wizard_views.xml',
    ],
    "images": ["static/description/background.png", ],
    "license": "OPL-1",
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": "79.37",
    "currency": "EUR"
}
