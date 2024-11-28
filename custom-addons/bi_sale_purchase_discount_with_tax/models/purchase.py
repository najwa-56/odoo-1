## -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero
from itertools import groupby
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang, _logger
import logging

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
                    if order.discount_method == 'fix':
                        discount = order.discount_amount
                        res = discount
                    elif order.discount_method == 'per':
                        total_amount_untax = sum(order.order_line.mapped('price_subtotal'))
                        discount = (total_amount_untax + order.amount_tax) * (order.discount_amount/ 100)
                        res = discount
                    else:
                        res = discount

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
            applied_discount = 0.0                    
            applied_discount = line_discount = sums = order_discount =  amount_untaxed = amount_tax = amount_after_discount =  0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                applied_discount += line.discount_amt
            
                if line.discount_method == 'fix':
                    line_discount += line.discount_amount
                elif line.discount_method == 'per':
                    tax = line.com_tax()
                    line_discount += (line.price_subtotal + tax) * (line.discount_amount/ 100)            

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
                            order_discount = (amount_untaxed + amount_tax) * (order.discount_amount / 100)  
                            order.update({
                                'amount_untaxed': amount_untaxed - order_discount,
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
    discount_amount = fields.Float('Discount Amount',digits=dp.get_precision('Discount'),default=0.0)
    discount_amt = fields.Monetary(compute='_amount_all',store=True,string='- Discount',readonly=True)
    discount_type = fields.Selection([('line', 'Order Line'), ('global', 'Global')],string='Discount Applies to',default='global')
    discount_amt_line = fields.Monetary(compute='_amount_all', string='- Line Discount',store=True, readonly=True)


    config_tax = fields.Monetary(string="total disc tax",compute="_amount_all",store=True)
    report_total = fields.Monetary("Report Untaxed Amount",compute="_calculate_report_total",readonly=True)



    @api.depends('order_line.taxes_id','order_line.price_unit', 'amount_total', 'amount_untaxed','discount_amount')
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
                    format_tax_total = tax_totals['amount_untaxed']
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
            [('fix', 'Fixed'), ('per', 'Percentage')], 'Discount Method')
    discount_type = fields.Selection(related='order_id.discount_type', string="Discount Applies to")
    discount_amount = fields.Float('Discount Amount', store=True)
    discount_amt = fields.Float('Discount Final Amount')


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
        res.update({'discount_method':self.discount_method,'discount_amount':self.discount_amount,'quantity':self.qty_to_invoice,'discount_amt':self.discount_amt,"fixed_discount": self.fixed_discount,"discount1":self.discount1,"total_with_discount":self.total_with_discount,})
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
                                'price_total': taxes['total_included'] + line.discount_amount,
                                'price_subtotal': taxes['total_excluded'],
                                'discount_amt' : line.discount_amount,
                            })

                        elif line.discount_method == 'per':
                            price = (line.price_unit * line.product_qty) * (1 - (line.discount_amount or 0.0) / 100.0)
                            price_x = ((line.price_unit * line.product_qty) - (line.price_unit * line.product_qty) * (1 - (line.discount_amount or 0.0) / 100.0))
                            taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, 1, product=line.product_id)
                            line.update({
                                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                                'price_total': taxes['total_included'] + price_x,
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
                        taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id)

                        if line.discount_method == 'fix':
                            price_x = (taxes['total_included']) - ( taxes['total_included'] - line.discount_amount)
                        elif line.discount_method == 'per':
                            price_x = (taxes['total_included']) - (taxes['total_included'] * (1 - (line.discount_amount or 0.0) / 100.0))
                        else:
                            price_x = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                
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


    fixed_discount = fields.Float(string="Fixed Disc.", digits="Product Price", default=0.000)

    discount1 = fields.Float(string=' % Disc %.', digits='Discount', default=0.000)
    total_with_discount=fields.Float(string="Total_with_Disc")
    discount = fields.Float(string='% Disc.', digits='Discount', default=0.000)


    @api.onchange("discount_amount")
    def _onchange_discount(self):
        res_config= self.env.company

        for line in self:
            if line.discount_method == 'per' and line.discount_amount != 0:
                self.fixed_discount = 0.0
                self.discount = 0.0
                discount1 = line.discount_amount
                discount = line.discount1
                line.update({"discount1": discount1 , "discount": discount})
                if res_config.tax_discount_policy == 'tax':
                 fixed_discount = (line.price_total) - (
                            line.price_total * (1 - (line.discount_amount or 0.0) / 100.0))
                 total_with_discount=line.price_subtotal-fixed_discount
                 line.update({"fixed_discount": fixed_discount,"total_with_discount":total_with_discount})

                elif res_config.tax_discount_policy == 'untax':

                 fixed_discount = (line.price_unit * line.product_qty) * (line.discount1 / 100.0)
                 total_with_discount = line.price_subtotal
                 line.update({"fixed_discount": fixed_discount,"total_with_discount":total_with_discount})

            if line.discount_amount == 0:
                 discount1 = 0.000
                 line.update({"discount1": discount1})


    @api.onchange("discount_amount")
    def _onchange_fixed_discount(self):
        res_config = self.env.company
        for line in self:
            if line.discount_method == 'fix' and line.discount_amount != 0:
                self.discount1 = 0.0
                self.discount = 0.0
                fixed_discount = line.discount_amount
                line.update({"fixed_discount": fixed_discount})
                if res_config.tax_discount_policy == 'tax':
                 discount1 = ((self.product_qty * self.price_unit) - (
                            (self.product_qty * self.price_unit) - self.fixed_discount)) / (
                                       self.product_qty * self.price_unit) * 100 or 0.0
                 discount = discount1
                 total_with_discount = line.price_subtotal - fixed_discount
                 line.update({"discount1": discount1,"total_with_discount":total_with_discount, "discount": discount})
                elif res_config.tax_discount_policy == 'untax':
                    discount1 = ((self.product_qty * self.price_unit) - (
                            (self.product_qty * self.price_unit) - self.fixed_discount)) / (
                                        self.product_qty * self.price_unit) * 100 or 0.0
                    discount = discount1
                    total_with_discount = line.price_subtotal
                    line.update({"discount1": discount1, "total_with_discount": total_with_discount, "discount": discount})

            if line.discount_amount == 0:
                fixed_discount = 0.0
                line.update({"fixed_discount": fixed_discount})




class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tax_discount_policy = fields.Selection(string='Discount Applies On',related='company_id.tax_discount_policy', readonly=False)
    sale_account_id = fields.Many2one('account.account',string='Sale Discount Account',check_company=True,domain=[('account_type','=','income'), ('discount_account','=',True)],readonly=False,related='company_id.sale_account_id')
    purchase_account_id = fields.Many2one('account.account',string='Purchase Discount Account',check_company=True,domain=[('account_type','=','expense'), ('discount_account','=',True)],readonly=False,related='company_id.purchase_account_id')

class Company(models.Model):
    _inherit = 'res.company'

    tax_discount_policy = fields.Selection([('tax', 'Taxed Amount'), ('untax', 'Untaxed Amount')],string='Discount Applies On',
                                           default='tax'
                                           )
    sale_account_id = fields.Many2one('account.account',domain=[('account_type', '=', 'income'), ('discount_account','=',True)])
    purchase_account_id = fields.Many2one('account.account',domain=[('account_type','=','expense'), ('discount_account','=',True)])
 
