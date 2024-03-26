# -*- coding: utf-8 -*-


from itertools import chain

from odoo import api, fields, models, tools
from odoo.exceptions import UserError



#testttttttt

class product_template(models.Model):
    _inherit = 'sale.order.template.line'


    selected_uom_ids = fields.Many2many(string="Uom Ids", related='product_id.selected_uom_ids')
    sales_multi_uom_id = fields.Many2one("wv.sales.multi.uom", string="Cust UOM", domain="[('id', '=', selected_uom_ids)]")

    def _prepare_order_line_values(self):
        """ Give the values to create the corresponding order line.

        :return: `sale.order.line` create values
        :rtype: dict
        """
        self.ensure_one()
        return {
            'display_type': self.display_type,
            'name': self.name,
            'product_id': self.product_id.id,
            'sales_multi_uom_id': self.sales_multi_uom_id,
            'product_uom_qty': self.product_uom_qty,
            'product_uom': self.product_uom_id.id,
        }
#testttttttt
