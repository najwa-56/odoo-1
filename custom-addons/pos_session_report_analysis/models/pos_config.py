# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################
from odoo import fields, models
class PosConfig(models.Model):
    _inherit = 'pos.config'

    wk_print_session_summary = fields.Boolean("Print Session Summary", default=1)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_wk_print_session_summary = fields.Boolean(related='pos_config_id.wk_print_session_summary',readonly=False)
