from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    user_ids = fields.Many2many('res.users', string='Allowed Users')
