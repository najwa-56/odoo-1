from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_customer_id = fields.Many2one(
        'res.partner',
        string='Default Customer',
        domain=[('customer_rank', '>', 0)],
        help='Default customer for new orders in POS'
    )

class PosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        result = super(PosSession, self)._pos_ui_models_to_load()
        result.append('res.partner')
        return result

    def _loader_params_res_partner(self):
        result = super(PosSession, self)._loader_params_res_partner()
        if self.config_id.default_customer_id:
            result['search_params']['domain'] = [('id', '=', self.config_id.default_customer_id.id)]
        return result
