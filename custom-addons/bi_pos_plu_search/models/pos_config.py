# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    allow_plu_search = fields.Boolean(default=False)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_allow_plu_search = fields.Boolean(related='pos_config_id.allow_plu_search', readonly=False)

class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        result['search_params']['fields'].append('plu_number')
        return result





