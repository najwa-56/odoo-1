from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    location_id = fields.Many2one('route.line', string='Location', help="Location of route.", related='partner_id.location_id', store=True)
