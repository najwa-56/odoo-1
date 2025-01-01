## -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero,float_round
from itertools import groupby
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, get_lang
from odoo import api, fields, tools, models, _



class purchase_order(models.Model):
    _inherit = 'purchase.order'


    @api.depends('discount_amount','discount_method','discount_type')
    def _calculate_discount(self):
        res_config= self.env.company
        cur_obj = self.env['res.currency']
        res=0.0
        discount = 0.0
        applied_discount = 0.0
        for order in self:
            applied_discount = line_discount = sums = order_discount =  amount_untaxed = amount_tax = amount_after_discount =  0.0
            if res_config.tax_discount_policy:
                if res_config.tax_discount_policy == 'tax':
                    if order.discount_type == 'line':
                        for line in order.order_line:
                            amount_untaxed += line.price_subtotal
                            amount_tax += line.price_tax
                            applied_discount += line.discount_amt
                
                            if line.discount_method == 'fix':
                                line_discount += line.discount_amount
                                res = line_discount
                            elif line.discount_method == 'per':
                                tax = line.com_tax()
                                line_discount +=(line.price_subtotal+tax) * (line.discount_amount/ 100)
                                
                                res = line_discount

                    if order.discount_type == 'global':
                        if order.discount_method == 'fix':
                            discount = order.discount_amount
                            res = discount
                        elif order.discount_method == 'per':
                            total_amount_untax = sum(order.order_line.mapped('price_subtotal'))
                            discount = (total_amount_untax + order.amount_tax) * (order.discount_amount/ 100)
                            res = discount
                else:
                    for line in order.order_line:
                        amount_untaxed += line.price_subtotal
                        amount_tax += line.price_tax
                        applied_discount += line.discount_amt
                        res = applied_discount
            
                        if line.discount_method == 'fix':
                            line_discount += line.discount_amount
                            res = line_discount
                        elif line.discount_method == 'per':
                            # tax = line.com_tax()
                            line_discount += line.price_subtotal * (line.discount_amount/ 100)
                            res = line_discount

                    if order.discount_type == 'global':
                        if order.discount_method == 'fix':
                            order_discount = order.discount_amount
                            res = order_discount
                            if order.order_line:
                                for line in order.order_line:
                                    if line.taxes_id:
                                        final_discount = 0.0
                                        try:
                                            final_discount = ((order.discount_amount*line.price_subtotal)/amount_untaxed)
                                        except ZeroDivisionError:
                                            pass
                                        discount = line.price_subtotal - final_discount

                                        taxes = line.taxes_id.compute_all(discount, \
                                                            line.order_id.currency_id,1.0, product=line.product_id, \
                                                            partner=order.partner_id)
                             
                                        sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                        else:
                            order.discount_amt_line = 0.00
                            order_discount = amount_untaxed * (order.discount_amount / 100)

                            res = order_discount
                            if order.order_line:
                                for line in order.order_line:
                                    if line.taxes_id:
                                        final_discount = 0.0
                                        try:
                                            final_discount = ((order.discount_amount*line.price_subtotal)/100.0)
                                        except ZeroDivisionError:
                                            pass
                                        discount = line.price_subtotal - final_discount
                                        taxes = line.taxes_id.compute_all(discount, \
                                                            order.currency_id,1.0, product=line.product_id, \
                                                            partner=order.partner_id)
                                        sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                    else:
                        if order.order_line:
                            for line in order.order_line:
                                if line.taxes_id:
                                    final_discount = 0.0
                                    try:
                                        test = order.order_line.mapped('discount_method')
                                        if test == 'fix':
                                            final_discount = ((order.order_line.discount_amount*line.price_subtotal)/amount_untaxed)
                                    except ZeroDivisionError:
                                        pass
                                    discount = line.price_subtotal - final_discount

                                    taxes = line.taxes_id.compute_all(discount, \
                                                        order.currency_id,1.0, product=line.product_id, \
                                                        partner=order.partner_id)
                                    sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))

        return res

    @api.depends('order_line','order_line.price_total','order_line.price_subtotal',\
    'order_line.product_qty','discount_amount',\
    'discount_method','discount_type' ,'order_line.discount_amount',\
    'order_line.discount_method','order_line.discount_amt')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        res_config= self.env.company
        cur_obj = self.env['res.currency']
        for order in self:  
            applied_discount = line_discount = sums = order_discount =  amount_untaxed = amount_tax = amount_after_discount =  0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                applied_discount += line.discount_amt

                if line.discount_method == 'fix':
                    line_discount += line.discount_amount
                elif line.discount_method == 'per':
                    tax = line.com_tax()
                    line_discount += (line.price_subtotal+tax) * (line.discount_amount/ 100)           

            if res_config.tax_discount_policy:
                if res_config.tax_discount_policy == 'tax':
                    if order.discount_type == 'line':
                        order.discount_amt = 0.00
                        order.update({
                            'amount_untaxed': amount_untaxed - line_discount,
                            'amount_tax': amount_tax,
                            'amount_total': amount_untaxed + amount_tax - line_discount,
                            'discount_amt_line' : line_discount,
                        })

                    elif order.discount_type == 'global':
                        order.discount_amt_line = 0.00
                        
                        if order.discount_method == 'per':
                            order_discount = (amount_untaxed + amount_tax)* (order.discount_amount / 100)
                            order.update({
                                'amount_untaxed': order.amount_untaxed -order_discount,
                                'amount_tax': amount_tax,
                                'amount_total': amount_untaxed + amount_tax - order_discount,
                                'discount_amt' : order_discount,
                            })
                        elif order.discount_method == 'fix':
                            order_discount = order.discount_amount
                            order.update({
                                'amount_untaxed': amount_untaxed - order_discount,
                                'amount_tax': amount_tax,
                                'amount_total': amount_untaxed + amount_tax - order_discount,
                                'discount_amt' : order_discount,
                            })
                        else:
                            order.update({
                                'amount_untaxed': amount_untaxed,
                                'amount_tax': amount_tax,
                                'amount_total': amount_untaxed + amount_tax ,
                            })
                    else:
                        order.update({
                            'amount_untaxed': amount_untaxed,
                            'amount_tax': amount_tax,
                            'amount_total': amount_untaxed + amount_tax ,
                            })
                elif res_config.tax_discount_policy == 'untax':
                    if order.discount_type == 'line':
                        order.discount_amt = 0.00 
                        order.update({
                            'amount_untaxed': amount_untaxed ,
                            'amount_tax':  amount_tax,
                            'amount_total': amount_untaxed + amount_tax ,
                            'discount_amt_line' : applied_discount,
                        })
                    elif order.discount_type == 'global':
                        order.discount_amt_line = 0.00
                        if order.discount_method == 'per':
                            order_discount = amount_untaxed * (order.discount_amount / 100)
                            res = order_discount
                            if order.order_line:
                                for line in order.order_line:
                                    if line.taxes_id:
                                        final_discount = 0.0
                                        try:
                                            final_discount = ((order.discount_amount*line.price_subtotal)/100.0)
                                        except ZeroDivisionError:
                                            pass
                                        discount = line.price_subtotal - final_discount
                                        taxes = line.taxes_id.compute_all(discount, \
                                                            order.currency_id,1.0, product=line.product_id, \
                                                            partner=order.partner_id)
                                        sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                            order.update({
                                'amount_untaxed': amount_untaxed - order_discount,
                                'amount_tax': sums,
                                'amount_total': amount_untaxed + sums - order_discount,
                                'discount_amt' : order_discount,
                                'config_tax': sums,
                            })
                        else:
                            order.discount_method == 'fix'
                            order_discount = order.discount_amount
                            if order.order_line:
                                for line in order.order_line:
                                    if line.taxes_id:
                                        final_discount = 0.0
                                        try:

                                            final_discount = ((order.discount_amount*line.price_subtotal)/amount_untaxed)

                                        except ZeroDivisionError:
                                            pass
                                        discount = line.price_subtotal - final_discount

                                        taxes = line.taxes_id.compute_all(discount, \
                                                            order.currency_id,1.0, product=line.product_id, \
                                                            partner=order.partner_id)
                                        sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                                        
                            order.update({
                                'amount_untaxed': amount_untaxed - order_discount,
                                'amount_tax': sums,
                                'amount_total': amount_untaxed + sums - order_discount,
                                'discount_amt' : order_discount,
                                'config_tax': sums,
                            })

                    else:
                        order.update({
                            'amount_untaxed': amount_untaxed,
                            'amount_tax': amount_tax,
                            'amount_total': amount_untaxed + amount_tax ,
                            })
                else:
                    order.update({
                            'amount_untaxed': amount_untaxed,
                            'amount_tax': amount_tax,
                            'amount_total': amount_untaxed + amount_tax ,
                            })         
            else:
                order.update({
                    'amount_untaxed': amount_untaxed,
                    'amount_tax': amount_tax,
                    'amount_total': amount_untaxed + amount_tax ,
                    })

    def _prepare_invoice(self):
        invoice_vals = super(purchase_order, self)._prepare_invoice()
        invoice_vals.update({
            'discount_method' : self.discount_method , 
            'discount_amt' : self.discount_amt,
            'discount_amount' : self.discount_amount ,
            'discount_type' : self.discount_type,
            'discount_amt_line' : self.discount_amt_line,
            'amount_untaxed' : self.amount_untaxed,
            'amount_total': self.amount_total,
            })
        return invoice_vals

    def action_create_invoices(self, grouped=False, final=False):
        res = super(purchase_order,self).action_create_invoices(grouped=grouped, final=final)
        res.update({'discount_type': self.discount_type})
        invoice_vals = []
        line = res.invoice_line_ids.filtered(lambda x: x.name == _('Down Payments'))
        if not line or final == False:
            res.update({'discount_method': self.discount_method,
                    'discount_amount': self.discount_amount,
                    'discount_amt': self.discount_amt,
                    'discount_amt_line' : self.discount_amt_line,
                    })
        else:
            for line in res.invoice_line_ids:
                line.update({'discount': 0.0,
                    'discount_method':None,
                    'discount_amount':0.0,
                    'discount_amt' : 0.0,})

        return res

    @api.depends('discount_type','discount_amt','discount_amt_line')
    def _calculate_report_total(self):

        for order in self:
            res_config= self.env.company
            if order.discount_type == 'global':
                order.update({
                    'report_total' : order.amount_untaxed - order.discount_amt
                })
            else:
                order.update({
                    'report_total' : order.amount_untaxed - order.discount_amt_line
                })

    discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')], 'Discount Method',default='fix')
    discount_amount = fields.Float('Discount Amount',default=0.0)
    discount_amt = fields.Monetary(compute='_amount_all',store=True,string='- Discount',readonly=True)
    discount_type = fields.Selection([('line', 'Order Line'), ('global', 'Global')],string='Discount Applies to',default='global')
    discount_amt_line = fields.Monetary(compute='_amount_all', string='- Line Discount',store=True, readonly=True)
    config_tax = fields.Monetary(string="total disc tax",compute="_amount_all",store=True)
    report_total = fields.Monetary("Report Untaxed Amount",compute="_calculate_report_total",readonly=True)

    @api.depends('order_line.taxes_id', 'order_line.price_unit', 'amount_total', 'amount_untaxed', 'discount_amount', 'config_tax')
    def _compute_tax_totals(self):
        res_config= self.env.company
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            tax_totals = self.env['account.tax']._prepare_tax_totals(
                [x._convert_to_tax_base_line_dict() for x in order_lines],
                order.currency_id,
            )

            res = self._calculate_discount()

            if res_config.tax_discount_policy == 'tax':
                
                if tax_totals.get('amount_untaxed'):
                    tax_totals['amount_untaxed'] = tax_totals['amount_untaxed'] - res
                if tax_totals.get('formatted_amount_total'):
                    format_tax_total = tax_totals['amount_untaxed'] + order.amount_tax
                    tax_totals['formatted_amount_total'] = formatLang(self.env, format_tax_total, currency_obj=self.currency_id)
            if res_config.tax_discount_policy == 'untax' and order.discount_type =="global":
                if res_config.tax_discount_policy == 'untax':
                    if tax_totals.get('amount_untaxed'):
                        tax_totals['amount_untaxed'] = tax_totals['amount_untaxed'] -res
                if tax_totals.get('amount_total'):
                    if order.config_tax :
                        format_tax_total = tax_totals['amount_untaxed'] + order.config_tax
                    else:
                        format_tax_total = tax_totals['amount_untaxed'] + order.config_tax
                    tax_totals['amount_total'] = formatLang(self.env, format_tax_total, currency_obj=self.currency_id)
                    tax_totals['formatted_amount_total'] = formatLang(self.env, format_tax_total, currency_obj=self.currency_id)
              
            if res_config.tax_discount_policy == 'untax' and order.discount_type =="line":
                if res_config.tax_discount_policy == 'untax':
                    if tax_totals.get('amount_untaxed'):
                        tax_totals['amount_untaxed'] = tax_totals['amount_untaxed'] 

                    if tax_totals.get('formatted_amount_untaxed'):
                        format_total = tax_totals['amount_untaxed']
                        tax_totals['formatted_amount_untaxed'] = formatLang(self.env, format_total, currency_obj=self.currency_id)

            groups_by_subtotal = tax_totals.get('groups_by_subtotal', {})
            if bool(groups_by_subtotal):
                _untax_amount = groups_by_subtotal.get('Untaxed Amount', [])
                if bool(_untax_amount):
                    if res_config.tax_discount_policy == 'tax':
                        for _tax in range(len(_untax_amount)):
                            
                            if _untax_amount[_tax].get('tax_group_base_amount'):
                                tax_totals.get('groups_by_subtotal', {}).get('Untaxed Amount', [])[_tax].update({
                                    'tax_group_base_amount' : _untax_amount[_tax]['tax_group_base_amount'] - res 
                                })
                            if _untax_amount[_tax].get('formatted_tax_group_base_amount'):
                                format_total = _untax_amount[_tax]['tax_group_base_amount'] - res
                                tax_totals.get('groups_by_subtotal', {}).get('Untaxed Amount', [])[_tax].update({
                                    'formatted_tax_group_base_amount' : formatLang(self.env, format_total, currency_obj=self.currency_id)
                                })

                    if res_config.tax_discount_policy == 'untax' and order.discount_type =="global":
                        for _tax in range(len(_untax_amount)):
                            if _untax_amount[_tax].get('tax_group_base_amount'):
                              tax_totals.get('groups_by_subtotal', {}).get('Untaxed Amount', [])[_tax].update({
                                  'tax_group_base_amount' : order.config_tax
                              })
                            if _untax_amount[_tax].get('formatted_tax_group_base_amount'):
                              format_total = order.config_tax
                              tax_totals.get('groups_by_subtotal', {}).get('Untaxed Amount', [])[_tax].update({
                                  'formatted_tax_group_base_amount' : formatLang(self.env, format_total, currency_obj=self.currency_id)
                              })

                            if _untax_amount[_tax].get('formatted_tax_group_amount'):
                              tax_totals.get('groups_by_subtotal', {}).get('Untaxed Amount', [])[_tax].update({
                                  'formatted_tax_group_amount' :  order.config_tax
                              })

                            if _untax_amount[_tax].get('tax_group_amount'):
                              tax_totals.get('groups_by_subtotal', {}).get('Untaxed Amount', [])[_tax].update({
                                  'tax_group_amount' :  order.config_tax
                              })

            subtotals = tax_totals.get('subtotals', {})
            if bool(subtotals):
                for _tax in range(len(subtotals)):

                    if res_config.tax_discount_policy == 'untax' and order.discount_type =="line":
                        if subtotals[_tax].get('amount'):
                            tax_totals.get('subtotals', {})[_tax].update({
                                'amount' : subtotals[_tax]['amount'] 
                            })
                    else:
                        if subtotals[_tax].get('amount'):
                            tax_totals.get('subtotals', {})[_tax].update({
                                'amount' : subtotals[_tax]['amount'] - res
                            })
                    if subtotals[_tax].get('amount_tax'):
                        tax_totals.get('subtotals', {})[_tax].update({
                            'amount_tax' : res
                        })
                    if subtotals[_tax].get('formatted_amount'):
                        format_total = subtotals[_tax]['amount']
                        tax_totals.get('subtotals', {})[_tax].update({
                            'formatted_amount' : formatLang(self.env, format_total, currency_obj=self.currency_id)
                        })
            order.tax_totals = tax_totals


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'
    
    discount_method = fields.Selection(
            [('fix', 'Fixed'), ('per', 'Percentage')], 'Discount Method',default='fix')
    discount_type = fields.Selection(related='order_id.discount_type', string="Discount Applies to")
    discount_amount = fields.Float('Discount Amount')
    discount_amt = fields.Float('Discount Final Amount')

    amount_before_discount = fields.Float("Amount Before Discount",compute="_calculate_amount_before_discount",readonly=True)
    fixed_discount = fields.Float("Fixed Discount",compute="_calculate_fixed_discount",readonly=True)

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


    @api.depends('product_qty','price_unit','taxes_id','discount_amount')
    def com_tax(self):
        tax_total = 0.0
        tax = 0.0
        for line in self:
            for tax in line.taxes_id:
                tax_total += (tax.amount/100)*line.price_subtotal
            tax = tax_total
            return tax

    def _prepare_account_move_line(self, move=False):

        res =super(purchase_order_line,self)._prepare_account_move_line(move)
        res.update({'discount_method':self.discount_method,'discount_amount':self.discount_amount,'quantity':self.qty_to_invoice,'discount_amt':self.discount_amt})
        return res 

    @api.depends('product_qty', 'discount', 'price_unit', 'taxes_id','discount_method','discount_amount')
    def _compute_amount(self):
        """
        Compute the amounts of the PO line.
        """
        res_config= self.env.company
        for line in self:
            if res_config.tax_discount_policy:
                if res_config.tax_discount_policy == 'untax':
                    if line.discount_type == 'line':
                        if line.discount_method == 'fix':
                            price = (line.price_unit * line.product_qty) - line.discount_amount
                            taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, 1, product=line.product_id)
                            line.update({
                                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                                'price_total': taxes['total_included'],
                                'price_subtotal': taxes['total_excluded'],
                                'discount_amt' : line.discount_amount,
                            })

                        elif line.discount_method == 'per':
                            price = (line.price_unit * line.product_qty) * (1 - (line.discount_amount or 0.0) / 100.0)
                            price_x = ((line.price_unit * line.product_qty) - (line.price_unit * line.product_qty) * (1 - (line.discount_amount or 0.0) / 100.0))
                            taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, 1, product=line.product_id)
                            line.update({
                                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                                'price_total': taxes['total_included'],
                                'price_subtotal': taxes['total_excluded'],
                                'discount_amt' : price_x,
                            })
                    
                        else:
                            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                            taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id)
                            line.update({
                                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                                'price_total': taxes['total_included'],
                                'price_subtotal': taxes['total_excluded'],
                            })
                    else:
                        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                        taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id)
                        line.update({
                            'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                            'price_total': taxes['total_included'],
                            'price_subtotal': taxes['total_excluded'],
                        })
                elif res_config.tax_discount_policy == 'tax':
                    if line.discount_type == 'line':
                        price_x = 0.0
                        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                        taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)

                        if line.discount_method == 'fix':
                            price_x = (taxes['total_included']) - ( taxes['total_included'] - line.discount_amount)
                        elif line.discount_method == 'per':
                            price_x = (taxes['total_included']) - (taxes['total_included'] * (1 - (line.discount_amount or 0.0) / 100.0))
                        else:
                            price_x = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                
                        line.update({
                            'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                            'price_total': taxes['total_included'] - price_x,
                            'price_subtotal': taxes['total_excluded'],
                            'discount_amt' : price_x,
                        })
                    else:
                        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                        taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
                        line.update({
                            'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                            'price_total': taxes['total_included'],
                            'price_subtotal': taxes['total_excluded'],
                        })
                else:
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id)
                    
                    line.update({
                        'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                        'price_total': taxes['total_included'],
                        'price_subtotal': taxes['total_excluded'],
                    })
            else:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id)
                
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })

    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.


        """
        self.ensure_one()
        discount = 0
        if self.env.company.tax_discount_policy == 'untax': 
            if self.discount_method == 'fix':
                if self.price_unit != 0 :
                    discount = (self.discount_amount / self.price_unit) * 100 or 0.00
            if self.discount_method == 'per':
                if self.price_unit != 0:
                   discount = self.discount_amount

        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.order_id.partner_id,
            currency=self.order_id.currency_id,
            product=self.product_id,
            taxes=self.taxes_id,
            price_unit=self.price_unit,
            quantity=self.product_qty,
            discount=discount,
            price_subtotal=self.price_subtotal,
        )

    @api.depends('product_qty', 'product_uom', 'company_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        for line in self:
            if not line.product_id or line.invoice_lines or not line.company_id:
                continue
            params = {'order_id': line.order_id}
            seller = line.product_id._select_seller(
                partner_id=line.partner_id,
                quantity=line.product_qty,
                date=line.order_id.date_order and line.order_id.date_order.date() or fields.Date.context_today(line),
                uom_id=line.product_uom,
                params=params)

            if seller or not line.date_planned:
                line.date_planned = line._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            # If not seller, use the standard price. It needs a proper currency conversion.
            if not seller:
                line.discount = 0
                unavailable_seller = line.product_id.seller_ids.filtered(
                    lambda s: s.partner_id == line.order_id.partner_id)
                if not unavailable_seller and line.price_unit and line.product_uom == line._origin.product_uom:
                    # Avoid to modify the price unit if there is no price list for this partner and
                    # the line has already one to avoid to override unit price set manually.
                    continue
                po_line_uom = line.product_uom or line.product_id.uom_po_id
                price_unit = line.env['account.tax']._fix_tax_included_price_company(
                    line.product_id.uom_id._compute_price(line.product_id.standard_price, po_line_uom),
                    line.product_id.supplier_taxes_id,
                    line.taxes_id,
                    line.company_id,
                )
                price_unit = line.product_id.cost_currency_id._convert(
                    price_unit,
                    line.currency_id,
                    line.company_id,
                    line.date_order or fields.Date.context_today(line),
                    False
                )
                line.price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))

            elif seller:
                price_unit = line.env['account.tax']._fix_tax_included_price_company(seller.price, line.product_id.supplier_taxes_id, line.taxes_id, line.company_id) if seller else 0.0
                price_unit = seller.currency_id._convert(price_unit, line.currency_id, line.company_id, line.date_order or fields.Date.context_today(line), False)
                price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
                line.price_unit = seller.product_uom._compute_price(price_unit, line.product_uom)
                if self.env.company.tax_discount_policy == 'untax' or self.env.company.tax_discount_policy == 'tax': 
                    line.discount = 0.0
                else:
                    line.discount = seller.discount or 0.0

            # record product names to avoid resetting custom descriptions
            default_names = []
            vendors = line.product_id._prepare_sellers({})
            product_ctx = {'seller_id': None, 'partner_id': None, 'lang': get_lang(line.env, line.partner_id.lang).code}
            default_names.append(line._get_product_purchase_description(line.product_id.with_context(product_ctx)))
            for vendor in vendors:
                product_ctx = {'seller_id': vendor.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                default_names.append(line._get_product_purchase_description(line.product_id.with_context(product_ctx)))
            if not line.name or line.name in default_names:
                product_ctx = {'seller_id': seller.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                line.name = line._get_product_purchase_description(line.product_id.with_context(product_ctx))


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tax_discount_policy = fields.Selection(string='Discount Applies On',related='company_id.tax_discount_policy', readonly=False)
    sale_account_id = fields.Many2one('account.account',string='Sale Discount Account',check_company=True,domain=[('account_type','=','income'), ('discount_account','=',True)],readonly=False,related='company_id.sale_account_id')
    purchase_account_id = fields.Many2one('account.account',string='Purchase Discount Account',check_company=True,domain=[('account_type','=','expense'), ('discount_account','=',True)],readonly=False,related='company_id.purchase_account_id')


class Company(models.Model):
    _inherit = 'res.company'

    tax_discount_policy = fields.Selection([('tax', 'Taxed Amount'), ('untax', 'Untaxed Amount')],string='Discount Applies On',
        default_model='sale.order')
    sale_account_id = fields.Many2one('account.account',domain=[('account_type', '=', 'income'), ('discount_account','=',True)])
    purchase_account_id = fields.Many2one('account.account',domain=[('account_type','=','expense'), ('discount_account','=',True)])





class UoM(models.Model):
    _inherit = 'uom.uom'

    def _compute_quantity(self, qty, to_unit, round=True, rounding_method='UP', raise_if_failure=True):
        
        if self.env.context.get('params'):
            params = self.env.context.get('params')
            model = params.get('model')  # Get the model from the context
            quotation_only = self.env.context.get('quotation_only')  # Check if 'quotation_only' is in the context

            if model in ['purchase.order'] or quotation_only:
                if not self or not qty:
                    return qty
                self.ensure_one()

                if self != to_unit and self.category_id.id != to_unit.category_id.id:
                    if raise_if_failure:
                        raise UserError(_(
                            'The unit of measure %s defined on the order line doesn\'t belong to the same category as the unit of measure %s defined on the product. Please correct the unit of measure defined on the order line or on the product, they should belong to the same category.',
                            self.name, to_unit.name))
                    else:
                        return qty

                if self == to_unit:
                    amount = qty
                else:
                    amount = qty / self.factor
                    if to_unit:
                        amount = amount

                if to_unit and round:
                    amount = tools.float_round(amount, precision_rounding=to_unit.rounding, rounding_method=rounding_method)

                return amount
            
        else:
            return super()._compute_quantity(qty = qty, to_unit= to_unit, round=round, rounding_method=rounding_method, raise_if_failure=raise_if_failure)

     