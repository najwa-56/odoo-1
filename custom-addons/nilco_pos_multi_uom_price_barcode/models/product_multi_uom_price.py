from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Inheritmulti_uom(models.Model):
    _inherit = 'product.multi.uom.price'


    product_product_id = fields.Many2one('product.product')
    barcode = fields.Char('Barcode')
    product_variant_id =fields.Many2one('product.product',related="product_id.product_variant_id",store=True)
    product_variant_count = fields.Integer('Product Variant Count')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    company_barcode_id = fields.Many2one('res.company', 'company', default=lambda self: self.env.user.company_id)
    multi_barcode_for_product = fields.Boolean(related='company_barcode_id.multi_barcode_for_product',
                                               string="Multi Barcode For Product")

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


