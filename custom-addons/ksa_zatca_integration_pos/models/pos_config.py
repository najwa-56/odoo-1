from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_customer_id = fields.Many2one('res.partner', string='Default Customer')
