
# Copyright (c) 2023 Sayed Hassan (sh-odoo@hotmail.com)

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang

class AccountMove(models.Model):
    _inherit = "account.move"

    discount_type = fields.Selection([('line', 'Order Line'), ('global', 'Global')],string='Discount Applies to',default='line')
    total_lines_discount = fields.Float(string='Total Discount', digits='Discount', default=0.000,compute="_calculate_total_discount")

    discount = fields.Float(string='Discount', digits='Discount', default=0.000,)

    discount_amount = fields.Float(string='Amount', digits='Discount', default=0.000,compute="_calculate_discount",readonly=True)
    
    discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')], 'Discount Method',default='fix')


    

    @api.depends('discount','discount_method','amount_untaxed')
    def _calculate_discount(self):
        for order in self:
            if order.discount_method == 'fix':
                order.discount_amount = order.discount
            else:
                if order.discount > 0:
                    order.discount_amount = (order.amount_untaxed ) * (order.discount / 100.0)
                else:
                    order.discount_amount = 0



   

    @api.depends('invoice_line_ids.fixed_discount','discount_type')
    def _calculate_total_discount(self):
        total_lines_discount = 0
        for order in self:
            for line in order.invoice_line_ids:
                total_lines_discount = total_lines_discount + line.fixed_discount

        order.total_lines_discount = order.discount_amount if order.discount_type == 'global' else total_lines_discount


 




class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    fixed_discount = fields.Float(string="Fixed Disc.", digits="Discount", default=0.000)

    discount = fields.Float(string='% Disc.', digits='Discount', default=0.000)


    amount_before_discount = fields.Float("Amount Before Discount",compute="_calculate_amount_before_discount",readonly=True)

   
    @api.depends('quantity','price_unit')
    def _calculate_amount_before_discount(self):
        for line in self:
           line.amount_before_discount = line.quantity * line.price_unit

   