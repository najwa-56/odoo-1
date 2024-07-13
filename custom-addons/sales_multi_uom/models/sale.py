# -*- coding: utf-8 -*-


from itertools import chain

from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class wv_sales_multi_uom(models.Model):
    _name = 'wv.sales.multi.uom'
    _description = 'Sales Multi UOM'

    name = fields.Char("Name", required=True)
    qty = fields.Float("Quantity", required=True)
    price = fields.Float("Price Unit", required=True)
    unit = fields.Many2one("uom.uom", string="Product Unit of Measure", required=True)
    product_id = fields.Many2one("product.product", string="Product")

    @api.onchange('unit')
    def unit_id_change(self):
        domain = {'unit': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        return {'domain': domain}


class product_product(models.Model):
    _inherit = 'product.product'

    sales_multi_uom_id = fields.One2many('wv.sales.multi.uom', 'product_id', string='Sales multi UOM')
    selected_uom_ids = fields.Many2many(comodel_name="wv.sales.multi.uom", string="Uom Ids", compute='_get_all_uom_id', store=True)

    @api.depends('sales_multi_uom_id')
    def _get_all_uom_id(self):
        for record in self:
            if record.sales_multi_uom_id:
                record.selected_uom_ids = self.env['wv.sales.multi.uom'].browse(record.sales_multi_uom_id.ids)
            else:
                record.selected_uom_ids = []


class sale_order_line(models.Model):
    _inherit = "sale.order.line"

    selected_uom_ids = fields.Many2many(string="Uom Ids", related='product_id.selected_uom_ids')
    sales_multi_uom_id = fields.Many2one("wv.sales.multi.uom", string="Cust UOM", domain="[('id', 'in', selected_uom_ids)]")
    

    @api.onchange('sales_multi_uom_id')
    def sales_multi_uom_id_change(self):
        self.ensure_one()
        if self.sales_multi_uom_id:
            self.update({"product_uom_qty": self.sales_multi_uom_id.qty})
            domain = {'product_uom': [('id', '=', self.sales_multi_uom_id.unit.id)]}
            return {'domain': domain}

    @api.onchange('sales_multi_uom_id','product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.sales_multi_uom_id:
            if self.sales_multi_uom_id:
                values = {
                    "product_uom": self.sales_multi_uom_id.unit.id,
                }
            self.update(values)
            if self.order_id.partner_id:
                context_partner = dict(self.env.context, partner_id=self.order_id.partner_id.id)
                pricelist_context = dict(context_partner, uom=False, date=self.order_id.date_order)
                price, rule_id = self.order_id.pricelist_id.with_context(pricelist_context)._get_product_price_rule12(
                    product=self.product_id, quantity=self.sales_multi_uom_id.qty or 1.0,
                    pro_price=self.sales_multi_uom_id.price, compute_price=False)
                self.price_unit = self.env['account.tax']._fix_tax_included_price_company(price,
                                                                                          self.product_id.taxes_id,
                                                                                          self.tax_id, self.company_id)
        else:
            if self.order_id.pricelist_id and self.order_id.partner_id:
                product = self.product_id.with_context(
                    lang=self.order_id.partner_id.lang,
                    partner=self.order_id.partner_id,
                    quantity=self.product_uom_qty,
                    date=self.order_id.date_order,
                    pricelist=self.order_id.pricelist_id.id,
                    uom=self.product_uom.id,
                    fiscal_position=self.env.context.get('fiscal_position')
                )
                self.price_unit = self.env['account.tax']._fix_tax_included_price_company(
                    self._get_display_price(), product.taxes_id, self.tax_id, self.company_id)


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule12(
            self, products, quantity, currency=None, uom=None, date=False, compute_price=True, pro_price=0.0,
            **kwargs
    ):
        self and self.ensure_one()  # self is at most one record

        currency = currency or self.currency_id or self.env.company.currency_id
        currency.ensure_one()

        if not products:
            return {}

        if not date:
            # Used to fetch pricelist rules and currency rates
            date = fields.Datetime.now()

        # Fetch all rules potentially matching specified products/templates/categories and date
        rules = self._get_applicable_rules(products, date, **kwargs)

        results = {}
        price = pro_price
        for product in products:
            suitable_rule = self.env['product.pricelist.item']

            product_uom = product.uom_id
            target_uom = uom or product_uom  # If no uom is specified, fall back on the product uom

            # Compute quantity in product uom because pricelist rules are specified
            # w.r.t product default UoM (min_quantity, price_surchage, ...)
            if target_uom != product_uom:
                qty_in_product_uom = target_uom._compute_quantity(
                    quantity, product_uom, raise_if_failure=False
                )
            else:
                qty_in_product_uom = quantity

            for rule in rules:
                if rule._is_applicable_for(product, qty_in_product_uom):
                    suitable_rule = rule
                    break

            if compute_price:
                price = suitable_rule._compute_price(
                    product, quantity, target_uom, date=date, currency=currency)
            else:
                # Skip price computation when only the rule is requested.
                price = pro_price
            results[product.id] = (price, suitable_rule.id)
        return results


    def _get_product_price_rule12(self,product,*args, **kwargs):

        self and self.ensure_one()  # self is at most one record
        return self._compute_price_rule12(product,*args, **kwargs)[product.id]
