
from odoo import models, fields, _,api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    multi_uom_price_id = fields.One2many('product.multi.uom.price', 'product_id', string="UOM Price")
    category_id = fields.Many2one(related='uom_id.category_id')
    selected_uom_ids = fields.Many2many(comodel_name="product.multi.uom.price", string="Uom Ids", compute='_get_all_uom_id', store=True)




class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

