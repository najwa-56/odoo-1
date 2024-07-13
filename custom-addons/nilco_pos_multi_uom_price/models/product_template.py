
from odoo import models, fields, _,api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    multi_uom_price_id = fields.One2many('product.multi.uom.price', 'product_id', string="UOM Price")
    category_id = fields.Many2one(related='uom_id.category_id')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    multi_uom_price_id = fields.Many2one('product.multi.uom.price', string='Multi UOM Price')
    available_uoms = fields.Many2one(related='multi_uom_price_id.uom_id', string='Multi UOM', store=True,compute='_compute_available_uoms'
                                  , domain="[('id', 'in', multi_uom_price_id)]")
    selected_uom_price = fields.Float(compute='_compute_selected_uom_price')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain=lambda self: [('id', 'in', self._get_available_uom_ids())])

    @api.depends('product_id')
    def _compute_available_uoms(self):
        for line in self:
            if line.product_id:
                line.available_uoms = line.product_id.multi_uom_price_id.mapped('uom_id')
            else:
                line.available_uoms = self.env['uom.uom'].browse([])

    @api.depends('product_id', 'product_uom')
    def _compute_selected_uom_price(self):
        for line in self:
            if line.product_id and line.product_uom:
                uom_price = line.product_id.multi_uom_price_id.filtered(lambda uom: uom.uom_id == line.product_uom)
                if uom_price:
                    line.selected_uom_price = uom_price[0].price
                else:
                    line.selected_uom_price = 0.0
            else:
                line.selected_uom_price = 0.0

    def _get_available_uom_ids(self):
        return self.mapped('available_uoms').ids