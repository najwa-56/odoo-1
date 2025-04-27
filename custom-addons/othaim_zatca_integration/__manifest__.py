# -*- coding: utf-8 -*-
{
    'name': "KSA Zatca Phase-2 For Othaim",
    'summary': """
        Othaim Zatca Integratin""",
    'description': """
        Othaim Zatca Integratin
    """,
   
    'depends': ['ksa_zatca_integration'],
   
    'data': [
      
        
        'data/cron.xml',
        'views/res_company.xml',
        'views/account_journal_views.xml',
        
        'reports/report.xml',
        'reports/vat_invoice_report_print.xml',
        'reports/vat_invoice_report_print2.xml',
        'reports/simpli_vat_invoice_report.xml',
        'reports/standard_invoice_low_margin.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'othaim_zatca_integration/static/src/css/style.css',
          
        ],
    },
    
}
