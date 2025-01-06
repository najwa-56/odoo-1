# Copyright (c) 2023 Sayed Hassan (sh-odoo@hotmail.com)

from odoo import api, fields, models

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

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



   

    @api.depends('order_line.fixed_discount','discount_type')
    def _calculate_total_discount(self):
        total_lines_discount = 0
        for order in self:
            for line in order.order_line:
                total_lines_discount = total_lines_discount + line.fixed_discount

        order.total_lines_discount = order.discount_amount if order.discount_type == 'global' else total_lines_discount


    @api.onchange('discount_type')
    def _onchange_discount_type(self):
        for order in self:
            if order.discount_type == 'global':
                for line in order.order_line:
                    line.discount = 0 
                    line.fixed_discount = 0
            else:
                order.discount = 0

    @api.depends('order_line.taxes_id', 'order_line.price_unit', 'amount_total', 'amount_untaxed', 'discount_amount',)
    def _compute_tax_totals(self):
        res_config= self.env.company
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            order.tax_totals = self.env['account.tax']._prepare_tax_totals(
                [x._convert_to_tax_base_line_dict() for x in order_lines],
                order.currency_id or order.company_id.currency_id,
            )    
            if order.tax_totals.get('amount_untaxed'):
                order.tax_totals['amount_untaxed'] = order.tax_totals['amount_untaxed'] - order.discount_amount



    def _prepare_invoice(self):
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        invoice_vals.update({
            'discount_method' : self.discount_method , 
            'discount_amount' : self.discount_amount ,
            'discount' : self.discount_amount ,
            'discount_type' : self.discount_type,
            'total_lines_discount' : self.total_lines_discount,
            })
        return invoice_vals

            
        
class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    fixed_discount = fields.Float(string="Fixed Disc.", digits="Discount", default=0.000)

    discount = fields.Float(string='% Disc.', digits='Discount', default=0.000)


    amount_before_discount = fields.Float("Amount Before Discount",compute="_calculate_amount_before_discount",readonly=True)

   
    @api.depends('product_qty','price_unit')
    def _calculate_amount_before_discount(self):
        for line in self:
           line.amount_before_discount = line.product_qty * line.price_unit

    @api.onchange("discount")
    def _onchange_discount(self):
        for line in self:
            if line.discount != 0:
                self.fixed_discount = 0.0
                fixed_discount = (line.price_unit * line.product_qty) * (line.discount / 100.0)
                line.update({"fixed_discount": fixed_discount})
            if line.discount == 0:
                fixed_discount = 0.000
                line.update({"fixed_discount": fixed_discount})
            line._compute_amount()

    @api.onchange("fixed_discount")
    def _onchange_fixed_discount(self):
        for line in self:
            if line.fixed_discount != 0:
                self.discount = 0.0
                discount = ((self.product_qty * self.price_unit) - ((self.product_qty * self.price_unit) - self.fixed_discount)) / (self.product_qty * self.price_unit) * 100 or 0.0
                line.update({"discount": discount})
            if line.fixed_discount == 0:
                discount = 0.0
                line.update({"discount": discount})
            line._compute_amount()

    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.order_id.partner_id,
            currency=self.order_id.currency_id,
            product=self.product_id,
            taxes=self.taxes_id,
            price_unit=self.price_unit,
            discount=self.discount,
            quantity=self.product_qty,
            price_subtotal=self.price_subtotal,
        )

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        aml_currency = move and move.currency_id or self.currency_id
        date = move and move.date or fields.Date.today()
        res = {
            'display_type': self.display_type or 'product',
            'name': '%s: %s' % (self.order_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.currency_id._convert(self.price_unit, aml_currency, self.company_id, date, round=False),
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'purchase_line_id': self.id,
            'fixed_discount':self.fixed_discount,
            'amount_before_discount':self.amount_before_discount
        }
        if self.analytic_distribution and not self.display_type:
            res['analytic_distribution'] = self.analytic_distribution
        return res
