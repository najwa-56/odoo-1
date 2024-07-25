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

    selected_uom_ids = fields.Many2many(string="Uom Ids", related='product_id.selected_uom_ids')
    sales_multi_uom_id = fields.Many2one("product.multi.uom.price", string="Cust UOM",
                                         domain="[('id', 'in', selected_uom_ids)]")

    barcode_multi_uom_barcode = fields.Float(string="UOM Cost", related=' sales_multi_uom_id.barcode')
    @api.model
    def _search_by_barcode(self, barcode, domain=None, operator='ilike'):
        if not domain:
            domain = []
        if barcode:
            product_ids = self.env['product.product'].search([
                '|',
                ('default_code', operator, barcode),
                ('barcode_multi_uom_barcode', operator, barcode),
                ('multi_uom_price_barcode', operator, barcode)
            ])
            if product_ids:
                return self.search([('product_id', 'in', product_ids.ids)] + domain)
        return super(SaleOrderLine, self)._search_by_barcode(barcode, domain, operator)
