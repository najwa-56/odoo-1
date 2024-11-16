# -*- coding: utf-8 -*-
#################################################################################
# Author      : CFIS (<https://www.cfis.store/>)
# Copyright(c): 2017-Present CFIS.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.cfis.store/>
#################################################################################

{
    "name": "Pdf Print Preview | Pdf Report Print Preview | Direct Print | Report Preview",
    "summary": """Preview and print a PDF report in your browser | Print without downloading | Quick printer | 
        Without downloading a PDF file | Preview report | Preview pdf | Odoo direct print | Pdf direct preview | 
        Easily print a report | Preview without downloading """,
    "version": "17.1",
    "description": """
        This module will allows you to Preview and print PDF Reports.
        Print Preview.
        Report Preview.
        PDF report preview.
        PDF report preview an Print.
        Print Report.
        Direct Print.
        Report Direct Print.
        Print Report.
    """,    
    "author": "CFIS",
    "maintainer": "CFIS",
    "license" :  "Other proprietary",
    "website": "https://www.cfis.store/",
    "images": ["images/print_report_preview.png"],
    "category": "web",
    "depends": [
        "base",
        "web",
    ],
    "data": [
        "views/res_users.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "print_report_preview/static/src/css/style.css",
            "print_report_preview/static/src/js/user_menu_items.js",
            "print_report_preview/static/src/js/print_report_preview.js",
            "print_report_preview/static/src/js/report_preview_dialog.js",
            "print_report_preview/static/src/xml/pdf_report_print_preview.xml",
        ],
        "web.assets_qweb": [
            
        ],
    },
    "installable": True,
    "application": True,
    "price"                :  20,
    "currency"             :  "EUR",
    "pre_init_hook"        :  "pre_init_check",
}
