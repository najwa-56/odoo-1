# -*- coding: utf-8 -*-


from itertools import chain

from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class wv_sales_multi_uom(models.Model):
    _name = 'wv.sales.multi.uom'
    _description = 'Sales Multi UOM'

    name = fields.Char("Name", required=True)
    qty = fields.Float("Quantity", required=True)
    price = fields.Float("Price Unit", required=True)
    unit = fields.Many2one("uom.uom", string="Product Unit of Measure", required=True)
    product_id = fields.Many2one("product.product", string="Product")

    @api.onchange('unit')
    def unit_id_change(self):
        domain = {'unit': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        return {'domain': domain}


class product_product(models.Model):
    _inherit = 'product.product'

    sales_multi_uom_id = fields.One2many('wv.sales.multi.uom', 'product_id', string='Sales multi UOM')
    selected_uom_ids = fields.Many2many(comodel_name="wv.sales.multi.uom", string="Uom Ids", compute='_get_all_uom_id', store=True)

    @api.depends('sales_multi_uom_id')
    def _get_all_uom_id(self):
        for record in self:
            if record.sales_multi_uom_id:
                record.selected_uom_ids = self.env['wv.sales.multi.uom'].browse(record.sales_multi_uom_id.ids)
            else:
                record.selected_uom_ids = []


class sale_order_line(models.Model):
    _inherit = "sale.order.line"

    selected_uom_ids = fields.Many2many(string="Uom Ids", related='product_id.selected_uom_ids')
    sales_multi_uom_id = fields.Many2one("wv.sales.multi.uom", string="Cust UOM", domain="[('id', 'in', selected_uom_ids)]")
    

    @api.onchange('sales_multi_uom_id')
    def sales_multi_uom_id_change(self):
        self.ensure_one()
        if self.sales_multi_uom_id:
            self.update({"product_uom_qty": self.sales_multi_uom_id.qty})
            domain = {'product_uom': [('id', '=', self.sales_multi_uom_id.unit.id)]}
            return {'domain': domain}
