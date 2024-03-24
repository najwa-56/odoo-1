# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    sales_multi_uom_id = fields.Many2one("wv.sales.multi.uom", string="Cust UOM")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super(AccountInvoiceLine, self)._onchange_product_id()
        # result['domain']['sales_multi_uom_id'] = [('product_id', '=', self.product_id.id)]
        # return result
        result = {}

        result.update({
            'domain': {'sales_multi_uom_id': [('product_id', '=', self.product_id.id)]},
        })
        print("Result", result)
        return result

    @api.onchange('sales_multi_uom_id')
    def sales_multi_uom_id_change(self):
        self.ensure_one()
        if self.sales_multi_uom_id:
            self.update({"quantity": self.sales_multi_uom_id.qty})
            domain = {'product_uom_id': [('id', '=', self.sales_multi_uom_id.unit.id)]}
            return {'domain': domain}

    @api.onchange('product_uom_id', 'quantity')
    def _onchange_uom_id(self):
        warning = {}
        result = {}
        values = {}
        if not self.product_uom_id:
            self.price_unit = 0.0
        if self.sales_multi_uom_id:
            if self.sales_multi_uom_id:
                values = {
                    "product_uom_id": self.sales_multi_uom_id.unit.id,
                }
            self.update(values)
            self.price_unit = self.sales_multi_uom_id.price
            # if self.invoice_id.partner_id:
            #     context_partner = dict(self.env.context, partner_id=self.invoice_id.partner_id.id)
            #     pricelist_context = dict(context_partner, uom=False, date=self.invoice_id.date_order)
            #     price, rule_id = self.invoice_id.pricelist_id.with_context(pricelist_context).get_product_price_rule12(self.product_id, self.sales_multi_uom_id.qty or 1.0, self.invoice_id.partner_id.id,pro_price=self.sales_multi_uom_id.price)
            #     self.price_unit = self.env['account.tax']._fix_tax_included_price(price, self.product_id.taxes_id, self.tax_id)

        if self.product_id and self.product_uom_id:
            if self.product_id.uom_id.category_id.id != self.product_uom_id.category_id.id:
                warning = {
                    'title': _('Warning!'),
                    'message': _(
                        'The selected unit of measure is not compatible with the unit of measure of the product.'),
                }
                self.product_uom_id = self.product_id.uom_id.id
        if warning:
            result['warning'] = warning
        return result
