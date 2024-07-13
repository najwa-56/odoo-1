
from odoo import models, fields, _,api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    multi_uom_price_id = fields.One2many('product.multi.uom.price', 'product_id', string="UOM Price")
    category_id = fields.Many2one(related='uom_id.category_id')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    multi_uom_price_id = fields.One2many('product.multi.uom.price', 'product_id', string="UOM Price")
    multi_uom_price_info = fields.Char(string='UOM Prices', compute='_compute_multi_uom_price_info')

    @api.depends('product_id')
    def _compute_multi_uom_price_info(self):
        for line in self:
            if line.product_id:
                uom_prices = line.product_id.multi_uom_price_id
                prices_info = ', '.join([f"{uom.uom_id.name}: {uom.price}" for uom in uom_prices])
                line.multi_uom_price_info = prices_info
            else:
                line.multi_uom_price_info = ''