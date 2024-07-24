from odoo import models, fields, api, _
from odoo.exceptions import UserError


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

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _filter_by_barcode(self, barcode):
        return self.env['product.template'].search([('multi_uom_price_barcode', 'ilike', barcode)])

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        barcode = self._context.get('barcode')
        if barcode:
            product_templates = self._filter_by_barcode(barcode)
            product_ids = product_templates.mapped('product_variant_ids').ids
            args.append(('product_id', 'in', product_ids))
        return super(PurchaseOrder, self).search(args, offset, limit, order, count)