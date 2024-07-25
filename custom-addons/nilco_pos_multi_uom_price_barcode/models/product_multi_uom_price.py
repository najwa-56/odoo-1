from odoo import models, fields, api, _
import re
from odoo.osv import expression

class Inheritmulti_uom(models.Model):
    _inherit = 'product.multi.uom.price'

    product_product_id = fields.Many2one('product.product')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    multi_barcode_for_product = fields.Boolean(related='company_id.multi_barcode_for_product',
                                               string="Multi Barcode For Product")
    model_ids = fields.Many2one('ir.model', string='Used For')
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


class ProductInherit(models.Model):
    _inherit = 'product.product'

    multi_uom_price_id = fields.One2many('product.multi.uom.price', 'product_product_id',string='Product Multi Barcodes')
    selected_uom_ids = fields.Many2many(comodel_name="product.multi.uom.price", string="Uom Ids",
                                        compute='_get_all_uom_id', store=True)
    barcode_multi_uom_id = fields.Many2one("product.multi.uom.price", string="Cust UOM", domain="[('id', 'in', selected_uom_ids)]")
    barcode_multi_uom_barcode = fields.Float(string="UOM Cost", related='barcode_multi_uom_id.barcode')

    @api.depends('multi_uom_price_id')
    def _get_all_uom_id(self):
        for record in self:
            if record.multi_uom_price_id:
                record.selected_uom_ids = self.env['product.multi.uom.price'].browse(record.multi_uom_price_id.ids)
            else:
                record.selected_uom_ids = []

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        active_model = self._context.get('active_model') or self._inherit
        company_id = self.env.user.company_id
        if company_id.multi_barcode_for_product == True:
            if not domain:
                domain = []
            if name:
                positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
                product_ids = []
                model_name = []
                if operator in positive_operators:
                    product_ids = list(self._search([('default_code', '=', name)] + domain, limit=limit, order=order))
                    if not product_ids:
                        product_ids = list(self._search([('barcode', '=', name)] + domain, limit=limit, order=order))
                        sale_order_line_model = "sale.order.line"
                        purchase_order_line_model = "purchase.order.line"
                        account_move_line_model = "account.move.line"
                        stock_scrap_model = "stock.scrap"
                        stock_move_model = "stock.move"
                        stock_quant_model = "stock.quant"
                        stock_warhouse = "stock.warehouse.orderpoint"
                        model_name = self._context.get('create_date_model')
                        if self._context.get('create_date_model') == sale_order_line_model:
                            model_name = "Sales Order"

                        elif self._context.get('create_date_model') == purchase_order_line_model:
                            model_name = "Purchase Order"

                        elif self._context.get('create_date_model') == account_move_line_model:
                            model_name = "Account"

                        elif self._context.get('create_date_model') == stock_scrap_model:
                            model_name = "Scrap"

                        elif self._context.get('create_date_model') == stock_move_model:
                            model_name = "Transfer"

                        elif self._context.get('create_date_model') == stock_quant_model:
                            model_name = "Quants"

                        elif self._context.get('create_date_model') == stock_warhouse:
                            model_name = "Minimum Inventory Rule"

                        product_barcode_ids = self.env['product.multi.uom.price']._search([
                            ('barcode', operator, name), ('model_ids.name', "=", model_name)])

                        if product_barcode_ids:
                            product_ids = list(self._search(
                                ['|', ('barcode', '=', name), ('barcode_multi_uom_barcode', '=', name)] + domain,
                                limit=limit, order=order))
                            if product_ids:
                                return product_ids

