from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    print_invoice = fields.Boolean(default=False)
