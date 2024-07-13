
from odoo import models, fields, _,api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    multi_uom_price_id = fields.One2many('product.multi.uom.price', 'product_id', string="UOM Price")
    category_id = fields.Many2one(related='uom_id.category_id')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    available_uoms = fields.Many2many('uom.uom', compute='_compute_available_uoms')
    selected_uom_price = fields.Float(compute='_compute_selected_uom_price')

    @api.depends('product_id')
    def _compute_available_uoms(self):
        for line in self:
            if line.product_id:
                line.available_uoms = line.product_id.multi_uom_price_id.mapped('uom_id')
            else:
                line.available_uoms = False
