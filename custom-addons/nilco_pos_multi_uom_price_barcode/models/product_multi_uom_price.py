from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression
import re

class Inheritmulti_uom(models.Model):
    _inherit = 'product.multi.uom.price'


    barcode = fields.Char('Barcode')
    product_variant_id =fields.Many2one('product.product',related="product_id.product_variant_id",store=True)
    product_variant_count = fields.Integer('Product Variant Count')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

