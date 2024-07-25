from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, get_lang

class Inheritmulti_uom(models.Model):
    _inherit = 'product.multi.uom.price'

    barcode = fields.Char('Barcode')
    product_variant_id =fields.Many2one('product.product',related="product_id.product_variant_id",store=True)
    product_variant_count = fields.Integer('Product Variant Count')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    multi_uom_price_barcode = fields.Char(
        string='Barcode',
        compute='_compute_multi_uom_price_barcode',
        store=True
    )

    @api.depends('multi_uom_price_id')
    def _compute_multi_uom_price_barcode(self):
        for record in self:
            if record.multi_uom_price_id:
                # If you want to concatenate all barcodes into one string
                barcodes = record.multi_uom_price_id.mapped('barcode')
                record.multi_uom_price_barcode = ', '.join(filter(None, barcodes))
            else:
                record.multi_uom_price_barcode = ''


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    barcode = fields.Char('Barcode')

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            # Search for the product by barcode
            product = self.env['product.product'].search([('multi_uom_price_id.barcode', '=', self.barcode)], limit=1)
            if product:
                self.product_id = product
                self.name = product.name

                self.price_unit = product.list_price
                # Set quantity to 1 as default
                self.product_uom_qty = 1
            else:
                # Clear product_id if barcode is not found
                self.product_id = False
                self.name = ''
                self.price_unit = 0.0
                self.product_uom_qty = 0.0


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    barcode = fields.Char('Barcode')

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            # Search for the product by barcode
            product = self.env['product.product'].search([('multi_uom_price_id.barcode', '=', self.barcode)], limit=1)
            if product:
                self.product_id = product
                self.name = product.name
                self.price_unit = product.list_price
                # Set quantity to 1 as default
                self.product_qty = 1

                # Set purchase_multi_uom_id based on barcode
                multi_uom = self.env['product.multi.uom.price'].search([('barcode', '=', self.barcode)], limit=1)
                if multi_uom:
                    self.purchase_multi_uom_id = multi_uom.id
                    self.product_uom = multi_uom.uom_id.id
            else:
                # Clear product_id and related fields if barcode is not found
                self.product_id = False
                self.name = ''
                self.price_unit = 0.0
                self.product_qty = 0.0
                self.product_uom = False
    selected_uom_ids = fields.Many2many(string="UOM Ids", related='product_id.selected_uom_ids')
    purchase_multi_uom_id = fields.Many2one("product.multi.uom.price", string="Custom UOM",
                                            domain="[('id', 'in', selected_uom_ids)]")
    purchase_multi_uom_cost = fields.Float(string="UOM Cost", related='purchase_multi_uom_id.cost')
    price_unit = fields.Float(string='Unit Price', compute='_compute_price_unit_and_date_planned_and_name', store=True)

    @api.depends('product_qty', 'product_uom', 'company_id', 'purchase_multi_uom_cost')
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

            if line.purchase_multi_uom_cost:
                line.price_unit = (line.purchase_multi_uom_cost) *.85
                continue

            # Original logic for computing price_unit when purchase_multi_uom_cost is not set
            if not seller:
                unavailable_seller = line.product_id.seller_ids.filtered(
                    lambda s: s.partner_id == line.order_id.partner_id)
                if not unavailable_seller and line.price_unit and line.product_uom == line._origin.product_uom:
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
                line.price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places,
                                                                               self.env[
                                                                                   'decimal.precision'].precision_get(
                                                                                   'Product Price')))
                continue

            price_unit = line.env['account.tax']._fix_tax_included_price_company(seller.price,
                                                                                 line.product_id.supplier_taxes_id,
                                                                                 line.taxes_id,
                                                                                 line.company_id) if seller else 0.0
            price_unit = seller.currency_id._convert(price_unit, line.currency_id, line.company_id,
                                                     line.date_order or fields.Date.context_today(line), False)
            price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places,
                                                                      self.env['decimal.precision'].precision_get(
                                                                          'Product Price')))
            line.price_unit = seller.product_uom._compute_price(price_unit, line.product_uom)
            line.discount = seller.discount or 0.0

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

