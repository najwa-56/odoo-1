# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create_from_ui(self, orders, draft=False):
        res = super(PosOrder, self).create_from_ui(orders, draft)
        for order_data in res:
            order = self.browse(order_data['id'])
            for line in order.lines:
                if not line.name_field:  # If name_field is not set (empty or falsy)
                    uom_id = line.product_id.multi_uom_price_id.filtered(
                        lambda m: m.uom_id.id == line.product_uom_id.id
                    )

                    if uom_id:
                        line.name_field = uom_id[0].name_field

        return res

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    product_uom_id = fields.Many2one('uom.uom', string='Product UoM', related='')

        
    def _export_for_ui(self, orderline):
        res = super()._export_for_ui(orderline)
        res.update({'product_uom_id': orderline.product_uom_id.id or False})
        return res
