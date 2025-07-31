# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
    "name":  "POS Session Report",
    "summary":  """This module prints POS Session Summary as well as send Session Summary to the current login user.Session Report|Session Report Summary|Report |Report Session""",
    "category":  "Point Of Sale",
    "version":  "1.0.0",
    "author":  "Webkul Software Pvt. Ltd.",
    "license":  "Other proprietary",
    "website":  "https://store.webkul.com/Odoo-POS-Session-Report.html",
    "description":  """POS Session Report , POS Session Report Analysis, Session Report in Running Session, Session report as receipt
                              POS Sales Report, User Wise Session Summary, Session Summary in Running Session, Print Session Summary, POS Summary,
                              https://webkul.com/blog/odoo-pos-session-report""",
    "live_test_url":  "http://odoodemo.webkul.com/?module=pos_session_report_analysis&custom_url=/pos/web",
    "depends":  [
        'point_of_sale',
        'mail',
    ],
    "data":  [
        'views/pos_session_report_view.xml',
        'views/report_session_summary.xml',
        'views/pos_session_view.xml',
        'edi/wk_session_report.xml',
        'views/pos_config_view.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_session_report_analysis/static/src/apps/**/*',
            'pos_session_report_analysis/static/src/xml/**/*',
        ],
    },
    "images":  ['static/description/Banner.png'],
    "application":  True,
    "installable":  True,
    "auto_install":  False,
    "price":  69,
    "currency":  "USD",
    "pre_init_hook":  "pre_init_check",
}