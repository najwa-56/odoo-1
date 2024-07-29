from odoo import models, fields, api, _
import re
from odoo.osv import expression

class Inheritmulti_uom(models.Model):
    _inherit = 'product.multi.uom.price'

    barcode = fields.Char('Barcode')
    product_variant_id =fields.Many2one('product.product',related="product_id.product_variant_id",store=True)
    product_variant_count = fields.Integer('Product Variant Count')


            #we add the calsses down to add Scan Barcode to multi uom######

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

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    barcode = fields.Char('Barcode')

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            # Search for the product by barcode
            product = self.env['product.product'].search([('multi_uom_price_id.barcode', '=', self.barcode)], limit=1)
            if product:
                self.product_id = product
                self.name = product.name

                # Set default quantity to 1 and update other fields
                self.product_uom_qty = 1
                self.price_unit = product.list_price
            else:
                # Clear product_id and other fields if barcode is not found
                self.product_id = False
                self.name = ''
                self.product_uom_qty = 0.0
                self.price_unit = 0.0


