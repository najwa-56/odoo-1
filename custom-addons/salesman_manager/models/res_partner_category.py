
from odoo import models, fields

class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    value = fields.Integer(string="Value")
