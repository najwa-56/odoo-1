# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)
    
class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    product_uom_id = fields.Many2one('uom.uom', string='Product UoM', related='')
    Ratio = fields.Float("Ratio", compute="_compute_ratio",
                         store=False)  # Ratio field  # Related field to the ratio in uom.uom

    @api.depends('product_uom_id')
    def _compute_ratio(self):
        for record in self:
            record.Ratio = record.product_uom_id.ratio if record.product_uom_id else 1.0


    def _compute_total_cost(self, stock_moves=None):
        """
        Compute the total cost of the order lines and multiply by the ratio.
        :param stock_moves: recordset of `stock.move`, used for fifo/avco lines
        """
        super(PosOrderLine, self)._compute_total_cost(stock_moves)
        for line in self:
            line.total_cost = line.total_cost * line.Ratio if line.Ratio else line.total_cost


    @api.depends('price_subtotal', 'total_cost')
    def _compute_margin(self):
        for line in self:
            line.margin = line.price_subtotal - line.total_cost
            if line.product_uom_id.ratio != 0:
                line.margin = line.margin / line.product_uom_id.ratio
            line.margin_percent = not float_is_zero(line.price_subtotal, precision_rounding=line.currency_id.rounding) and line.margin / line.price_subtotal or 0

    def _export_for_ui(self, orderline):
        res = super()._export_for_ui(orderline)
        res.update({'product_uom_id': orderline.product_uom_id.id})

        return res



