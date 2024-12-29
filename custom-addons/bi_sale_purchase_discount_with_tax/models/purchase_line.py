
## -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero,float_round
from itertools import groupby
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, get_lang


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'


    amount_before_discount = fields.Monetary("Amount Before Discount",compute="_calculate_amount_before_discount",readonly=True)
    fixed_discount = fields.Monetary("Fixed/Percentage Discount",compute="_calculate_fixed_discount",readonly=True)

    @api.depends('product_qty','price_unit')
    def _calculate_amount_before_discount(self):
        for line in self:
           line.amount_before_discount = line.product_qty * line.price_unit

    
    @api.depends('discount_method','price_subtotal','discount_type','discount_amount','price_total')
    def _calculate_fixed_discount(self):
        res_config= self.env.company
        self.fixed_discount = 0
        for line in self:
            if line.discount_amount > 0 :
                if line.discount_method == 'per':
                    if res_config.tax_discount_policy == 'untax':
                        line.fixed_discount = (line.price_subtotal * line.discount_amount) / (100 - line.discount_amount)
                    else:
                        line.fixed_discount = (line.price_total * line.discount_amount) / (100 - line.discount_amount)

                elif line.discount_method == 'fix':
                    if res_config.tax_discount_policy == 'untax':
                        line.fixed_discount = (line.discount_amount * 100) / (line.price_subtotal + line.discount_amount)
                    else:
                        line.fixed_discount = (line.discount_amount * 100) / (line.price_total + line.discount_amount)
                else:
                    line.fixed_discount = 0
                


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    amount_before_discount = fields.Monetary("Amount Before Discount",compute="_calculate_amount_before_discount",readonly=True)
    fixed_discount = fields.Monetary("Fixed/Percentage Discount",compute="_calculate_fixed_discount",readonly=True)

    @api.depends('quantity','price_unit')
    def _calculate_amount_before_discount(self):
        for line in self:
           line.amount_before_discount = line.quantity * line.price_unit

    
    @api.depends('discount_method','price_subtotal','discount_type','discount_amount','price_total')
    def _calculate_fixed_discount(self):
        res_config= self.env.company
        self.fixed_discount = 0
        for line in self:
            if line.discount_amount > 0 :
                if line.discount_method == 'per':
                    if res_config.tax_discount_policy == 'untax':
                        line.fixed_discount = (line.price_subtotal * line.discount_amount) / (100 - line.discount_amount)
                    else:
                        line.fixed_discount = (line.price_total * line.discount_amount) / (100 - line.discount_amount)

                elif line.discount_method == 'fix':
                    if res_config.tax_discount_policy == 'untax':
                        line.fixed_discount = (line.discount_amount * 100) / (line.price_subtotal + line.discount_amount)
                    else:
                        line.fixed_discount = (line.discount_amount * 100) / (line.price_total + line.discount_amount)
                else:
                    line.fixed_discount = 0