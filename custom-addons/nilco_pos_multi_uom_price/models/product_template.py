
from odoo import models, fields, _,api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    multi_uom_price_id = fields.One2many('product.multi.uom.price', 'product_id', string="UOM Price")
    category_id = fields.Many2one(related='uom_id.category_id')
    selected_uom_ids = fields.Many2many(comodel_name="product.multi.uom.price", string="Uom Ids", compute='_get_all_uom_id', store=True)


    @api.depends('multi_uom_price_id')
    def _get_all_uom_id(self):
        for record in self:
            if record.multi_uom_price_id:
                record.selected_uom_ids = self.env['product.multi.uom.price'].browse(record.multi_uom_price_id.ids)
            else:
                record.selected_uom_ids = []



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    selected_uom_ids = fields.Many2many(string="Uom Ids", related='product_id.selected_uom_ids')

    sales_multi_uom_id = fields.Many2one("product.multi.uom.price", string="Cust UOM", domain="[('id', 'in', selected_uom_ids)]")

    @api.onchange('sales_multi_uom_id')
    def sales_multi_uom_id_change(self):
        self.ensure_one()
        if self.sales_multi_uom_id:
            domain = {'product_uom': [('id', '=', self.sales_multi_uom_id.uom_id.id)]}
            return {'domain': domain}

    @api.onchange('sales_multi_uom_id', 'product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.sales_multi_uom_id:
            if self.sales_multi_uom_id:
                values = {
                    "product_uom": self.sales_multi_uom_id.uom_id.id,
                }
            self.update(values)

