# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from odoo.tools import float_is_zero, float_round, float_repr, float_compare

_logger = logging.getLogger(__name__)
    
class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    product_uom_id = fields.Many2one('uom.uom', string='Product UoM', related='')
    #add field Ratio#####
    Ratio = fields.Float("Ratio", compute="_compute_ratio",
                         store=False)  # Ratio field  # Related field to the ratio in uom.uom

    name_field = fields.Char(string="Name Field", store=True)



    @api.model
    def _prepare_account_move_line(self, pos_order_line, move):
        res = super(PosOrderLine, self)._prepare_account_move_line(pos_order_line, move)
        # Add the name_field to the account move line
        _logger.info(f"Copying name_field to account.move.line: {self.name_field}")

        res['pos_name_field'] = pos_order_line.name_field
        return res
    #Edit----#

    @api.depends('product_uom_id')
    def _compute_price(self):
        for line in self:
            if line.product_uom_id:
                uom_price = self.env['product.multi.uom.price'].search([
                    ('product_id', '=', line.product_id.id),
                    ('uom_id', '=', line.product_uom_id.id)
                ], limit=1)
                if uom_price:
                    line.price_unit = uom_price.price


#Edit cost ------########
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

###################################

    @api.depends('price_subtotal', 'total_cost')
    def _compute_margin(self):
        for line in self:
            line.margin = line.price_subtotal - line.total_cost
            if line.product_uom_id.ratio != 0:
                line.margin = line.margin / line.product_uom_id.ratio
            line.margin_percent = not float_is_zero(line.price_subtotal, precision_rounding=line.currency_id.rounding) and line.margin / line.price_subtotal or 0

    def _export_for_ui(self, orderline):
        res = super()._export_for_ui(orderline)
        res.update({'product_uom_id': orderline.product_uom_id.id,'name_field': orderline.name_field})

        return res

class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _get_invoice_lines_values(self, line_values, pos_order_line):
        return {

            'name_field': line_values['name_field'],

        }

    def _prepare_invoice_lines(self):
        """ Prepare a list of orm commands containing the dictionaries to fill the
        'invoice_line_ids' field when creating an invoice.

        :return: A list of Command.create to fill 'invoice_line_ids' when calling account.move.create.
        """
        sign = 1 if self.amount_total >= 0 else -1
        line_values_list = self._prepare_tax_base_line_values(sign=sign)
        invoice_lines = []
        for line_values in line_values_list:
            line = line_values['record']
            invoice_lines_values = self._get_invoice_lines_values(line_values, line)
            invoice_lines.append((0, None, invoice_lines_values))
            if line.order_id.pricelist_id.discount_policy == 'without_discount' and float_compare(
                    line.price_subtotal_incl, line.product_id.lst_price * line.qty,
                    precision_rounding=self.currency_id.rounding) < 0:
                invoice_lines.append((0, None, {
                    'name': _('Price discount from %s -> %s',
                              float_repr(line.product_id.lst_price * line.qty, self.currency_id.decimal_places),
                              float_repr(line.price_subtotal_incl, self.currency_id.decimal_places)),
                    'display_type': 'line_note',
                }))
            if line.customer_note:
                invoice_lines.append((0, None, {
                    'name': line.customer_note,
                    'display_type': 'line_note',
                }))

        return invoice_lines


class AccountMove(models.Model):
    _inherit = 'account.move'



def _get_invoiced_lot_values(self):
        self.ensure_one()

        lot_values = super(AccountMove, self)._get_invoiced_lot_values()

        if self.state == 'draft':
            return lot_values

        # user may not have access to POS orders, but it's ok if they have
        # access to the invoice
        for order in self.sudo().pos_order_ids:
            for line in order.lines:
                lots = line.pack_lot_ids or False
                if lots:
                    for lot in lots:
                        lot_values.append({

                            'name_field': line.name_field,

                        })

        return lot_values
