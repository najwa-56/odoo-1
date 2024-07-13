
from odoo import models, fields, _,api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    multi_uom_price_id = fields.One2many('product.multi.uom.price', 'product_id', string="UOM Price")
    category_id = fields.Many2one(related='uom_id.category_id')
    selected_uom_ids = fields.Many2many(comodel_name="product.multi.uom.price", string="Uom Ids", compute='_get_all_uom_id', store=True)


    @api.depends('multi_uom_price_id')
    def _get_all_uom_id(self):
        for record in self:
            if record.sales_multi_uom_id:
                record.selected_uom_ids = self.env['product.multi.uom.price'].browse(record.sales_multi_uom_id.ids)
            else:
                record.selected_uom_ids = []



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    selected_uom_ids = fields.Many2many(string="Uom Ids", related='product_id.selected_uom_ids')

    sales_multi_uom_id = fields.Many2one("product.multi.uom.price", string="Cust UOM", domain="[('id', 'in', selected_uom_ids)]")

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



