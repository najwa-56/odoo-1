
from odoo import models, fields, _,api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    multi_uom_price_id = fields.One2many('product.multi.uom.price', 'product_id', string="UOM Price")
    category_id = fields.Many2one(related='uom_id.category_id')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    available_uoms = fields.Many2many('uom.uom', compute='_compute_available_uoms')
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

    @api.model
    def _get_available_uom_ids(self):
        lines = self.search([])
        available_uom_ids = []
        for line in lines:
            available_uom_ids.append(line.available_uoms.id)
            available_uom_ids.append(line.product_uom.id)