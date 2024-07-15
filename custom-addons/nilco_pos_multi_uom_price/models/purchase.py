from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')

    
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    selected_uom_ids = fields.Many2many(string="UOM Ids", related='product_id.selected_uom_ids')

    purchase_multi_uom_id = fields.Many2one("product.multi.uom.price", string="Custom UOM", domain="[('id', 'in', selected_uom_ids)]")

    @api.onchange('purchase_multi_uom_id')
    def purchase_multi_uom_id_change(self):
        self.ensure_one()
        if self.purchase_multi_uom_id:
            domain = {'product_uom': [('id', '=', self.purchase_multi_uom_id.uom_id.id)]}
            return {'domain': domain}

    @api.onchange('purchase_multi_uom_id', 'product_uom', 'product_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.purchase_multi_uom_id:
            values = {
                "product_uom": self.purchase_multi_uom_id.uom_id.id,
            }
            self.update(values)
            if self.order_id.partner_id:
                context_partner = dict(self.env.context, partner_id=self.order_id.partner_id.id)
                pricelist_context = dict(context_partner, uom=False, date=self.order_id.date_order)
                price, rule_id = self.order_id.pricelist_id.with_context(pricelist_context)._get_product_price_rule12(
                    product=self.product_id, quantity=1.0,
                    pro_price=self.purchase_multi_uom_id.price, compute_price=False)
                self.price_unit = self.env['account.tax']._fix_tax_included_price_company(price,
                                                                                          self.product_id.taxes_id,
                                                                                          self.taxes_id, self.company_id)
        else:
            if self.order_id.pricelist_id and self.order_id.partner_id:
                product = self.product_id.with_context(
                    lang=self.order_id.partner_id.lang,
                    partner=self.order_id.partner_id,
                    quantity=self.product_qty,
                    date=self.order_id.date_order,
                    pricelist=self.order_id.pricelist_id.id,
                    uom=self.product_uom.id,
                    fiscal_position=self.env.context.get('fiscal_position')
                )
                self.price_unit = self.env['account.tax']._fix_tax_included_price_company(
                    self._get_display_price(), product.taxes_id, self.taxes_id, self.company_id)


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule12(
            self, products, quantity, currency=None, uom=None, date=False, compute_price=True, pro_price=0.0,
            **kwargs
    ):
        self.ensure_one()  # self is at most one record

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

    def _get_product_price_rule12(self, product, *args, **kwargs):
        self.ensure_one()  # self is at most one record
        return self._compute_price_rule12(product, *args, **kwargs)[product.id]
