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
        compute='search_product_by_barcode',
        store=True
    )

    @api.model
    def search_product_by_barcode(self, barcode):
        # Search for the `product.multi.uom.price` record with the given barcode
        uom_price_records = self.env['product.multi.uom.price'].search([('barcode', '=', barcode)])
        if uom_price_records:
            # Return the product.template linked to the found `product.multi.uom.price` records
            return uom_price_records.mapped('product_id.product_tmpl_id')
        return self.env['product.template']

