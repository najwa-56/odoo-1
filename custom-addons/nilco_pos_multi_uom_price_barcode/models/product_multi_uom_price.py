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
            record.multi_uom_price_barcode = record.multi_uom_price_id.barcode if record.multi_uom_price_id else ''