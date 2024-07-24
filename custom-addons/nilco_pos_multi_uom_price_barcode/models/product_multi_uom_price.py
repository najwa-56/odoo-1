from odoo import models, fields, api, _


class Inheritmulti_uom(models.Model):

    _inherit = 'product.multi.uom.price'
    barcode = fields.Char('Barcode')
    product_variant_id =fields.Many2one('product.product',related="product_id.product_variant_id",store=True)
    product_variant_count = fields.Integer('Product Variant Count')


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["barcodes.barcode_events_mixin", "product.template"]

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

    def on_barcode_scanned(self, barcode):
        # Search for the product.multi.uom.price record with the scanned barcode
        uom_price_record = self.env['product.multi.uom.price'].search([('barcode', '=', barcode)], limit=1)
        if uom_price_record:
            # Find the product.template associated with the found product.multi.uom.price record
            product_template = uom_price_record.product_id.product_tmpl_id
            if product_template:
                # Optionally, do something with the found product template, like posting a message
                self.message_post(
                    body=_("Barcode %s scanned and linked to product %s.") % (barcode, product_template.name))
                # Optionally, update some field or take some action on the found product template
                product_template.multi_uom_price_barcode = barcode
        else:
            self.message_post(body=_("Barcode %s scanned but no matching product found.") % (barcode))

    @api.model
    def search_product_by_barcode(self, barcode):
        # Search for the `product.multi.uom.price` record with the given barcode
        uom_price_records = self.env['product.multi.uom.price'].search([('barcode', '=', barcode)])
        if uom_price_records:
            # Return the product.template linked to the found `product.multi.uom.price` records
            return uom_price_records.mapped('product_id.product_tmpl_id')
        return self.env['product.template']

