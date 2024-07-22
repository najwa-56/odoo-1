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

    @api.model
    def search_product_by_barcode(self, barcode):
        # Search for the `product.multi.uom.price` record with the given barcode
        uom_price_records = self.env['product.multi.uom.price'].search([('barcode', '=', barcode)])
        if uom_price_records:
            # Return the product.template linked to the found `product.multi.uom.price` records
            return uom_price_records.mapped('product_id.product_tmpl_id')
        return self.env['product.template']


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    multi_uom_price_barcode = fields.Char(
        string='Barcodes',
        compute='_compute_multi_uom_price_barcode',
        store=True
    )

    @api.depends('order_line.product_id')
    def _compute_multi_uom_price_barcode(self):
        for order in self:
            barcodes = []
            for line in order.order_line:
                # Fetch barcode from product.template through product.product
                if line.product_id:
                    barcodes.extend(line.product_id.multi_uom_price_barcode.split(', '))
            order.multi_uom_price_barcode = ', '.join(set(barcodes))