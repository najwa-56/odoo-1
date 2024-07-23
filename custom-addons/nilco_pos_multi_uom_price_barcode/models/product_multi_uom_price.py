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

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def _search_product_by_barcode(self, barcode):
        # Search for the `product.multi.uom.price` record with the given barcode
        uom_price_records = self.env['product.multi.uom.price'].search([('barcode', '=', barcode)])
        if uom_price_records:
            # Return the product.product linked to the found `product.multi.uom.price` records
            return uom_price_records.mapped('product_variant_id')
        return self.env['product.product']

    @api.onchange('product_id')
    def _onchange_product_id(self):
        # Custom logic for onchange product_id
        if self.product_id:
            pass

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            products = self._search_product_by_barcode(self.barcode)
            if products:
                self.product_id = products[0]
            else:
                self.product_id = False
                return {
                    'warning': {
                        'title': _("Warning"),
                        'message': _("No product found for the given barcode."),
                    }
                }
