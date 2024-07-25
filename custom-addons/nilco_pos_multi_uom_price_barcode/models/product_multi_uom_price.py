from odoo import models, fields, api, _

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
                # Set quantity to 1 as default
                self.product_qty = 1

                # Set purchase_multi_uom_id based on barcode
                multi_uom = self.env['product.multi.uom.price'].search([('barcode', '=', self.barcode)], limit=1)
                if multi_uom:
                    self.purchase_multi_uom_id = multi_uom.id
                    self.product_uom = multi_uom.uom_id.id
                    self.price_unit = product.multi_uom.id.cost

            else:
                # Clear product_id and related fields if barcode is not found
                self.product_id = False
                self.name = ''
                self.price_unit = 0.0
                self.product_qty = 0.0
                self.product_uom = False
