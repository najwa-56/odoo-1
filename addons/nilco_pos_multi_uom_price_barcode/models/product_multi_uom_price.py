from odoo import models, fields, api, _
import re
from odoo.osv import expression
import json


class Inheritmulti_uom(models.Model):
    _inherit = 'product.multi.uom.price'

    barcode = fields.Char(store=True,string='الباركود')
    product_variant_id =fields.Many2one('product.product',related="product_id.product_variant_id",store=True)
    product_variant_count = fields.Integer('Product Variant Count')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    new_barcode = fields.Text("New Barcode", compute="_compute_new_barcode")

    def _compute_new_barcode(self):
        for record in self:
            if record.multi_uom_price_id:
                multi_uom_list = []
                for multi_uom in record.multi_uom_price_id:
                    multi_uom_list.append(multi_uom.barcode)
                record.new_barcode = json.dumps(multi_uom_list)
            else:
                record.new_barcode = json.dumps([])
                

    def get_barcode_val_batch(self, product_ids):
        """Return a list of tuples containing the barcode and product ID for all products."""
        products = self.browse(product_ids)
        result = []
        for product in products:
            for uom in product.multi_uom_price_id:
                if uom.barcode:
                    result.append((uom.barcode, product.id))
        return result
        
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



