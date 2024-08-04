# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)
    
class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    selected_uom_ids = fields.Many2many(string="Uom Ids", related='product_id.selected_uom_ids')
    pos_multi_uom_id = fields.Many2one("product.multi.uom.price", string="Cust UOM", domain="[('id', 'in', selected_uom_ids)]")
    uom_price = fields.Float(string="UOM price", related='pos_multi_uom_id.price')

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

    @api.onchange('qty', 'discount', 'price_unit', 'tax_ids', 'product_uom_id')
    def _onchange_qty(self):
        if self.product_id:
            # Use the stored UOM price if available
            price = self.uom_price or self.price_unit
            price = price * (1 - (self.discount or 0.0) / 100.0)
            self.price_subtotal = self.price_subtotal_incl = price * self.qty
            if self.tax_ids:
                taxes = self.tax_ids.compute_all(price, self.order_id.currency_id, self.qty, product=self.product_id,
                                                 partner=False)
                self.price_subtotal = taxes['total_excluded']
                self.price_subtotal_incl = taxes['total_included']

    @api.onchange('product_id', 'product_uom_id')
    def _onchange_product_id(self):
        if self.product_id:
            # Get the base price from the pricelist
            base_price = self.order_id.pricelist_id._get_product_price(
                self.product_id, self.qty or 1.0, currency=self.currency_id
            )

            # Check if a UOM is selected
            if self.product_uom_id:
                uom = self.env['uom.uom'].browse(self.product_uom_id.id)
                # Use UOM price if available
                self.price_unit = uom.price if uom.price else base_price
            else:
                self.price_unit = base_price

            # Update taxes based on the product and fiscal position
            self.tax_ids = self.product_id.taxes_id.filtered_domain(
                self.env['account.tax']._check_company_domain(self.company_id))
            tax_ids_after_fiscal_position = self.order_id.fiscal_position_id.map_tax(self.tax_ids)

            # Fix tax-included price based on the selected UOM or base price
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(
                self.price_unit, self.tax_ids, tax_ids_after_fiscal_position, self.company_id
            )

            # Trigger quantity-related recalculations
            self._onchange_qty()