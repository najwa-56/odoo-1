from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression
import re



class Inheritmulti_uom(models.Model):
    _inherit = 'product.multi.uom.price'


    product_product_id = fields.Many2one('product.product')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    multi_barcode_for_product = fields.Boolean(related='company_id.multi_barcode_for_product',
                                               string="Multi Barcode For Product")
    model_ids = fields.Many2one('ir.model', string='Used For')
    barcode = fields.Char('Barcode')
    product_variant_id =fields.Many2one('product.product',related="product_id.product_variant_id",store=True)
    product_variant_count = fields.Integer('Product Variant Count')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    company_barcode_id = fields.Many2one('res.company', 'Company_barcod', default=lambda self: self.env.user.company_id)
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



class ProductInherit(models.Model):
    _inherit = 'product.product'

    product_barcode = fields.One2many('product.multi.uom.price', 'product_id', string='Product Multi Barcodes')

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        if not domain:
            domain = []

        # Example corrected domain usage
        if name:
            product_ids = self._search([
                                           '|',
                                           ('default_code', operator, name),
                                           ('product_barcode', operator, name)
                                       ] + domain, limit=limit, order=order)

            if not product_ids:
                product_barcode_ids = self.env['product.multi.uom.price']._search([
                    ('barcode', operator, name)
                ])
                if product_barcode_ids:
                    product_ids = self._search([
                                                   '|',
                                                   ('product_barcode', 'in', product_barcode_ids),
                                                   ('product_tmpl_id.product_barcode', 'in', product_barcode_ids)
                                               ] + domain, limit=limit, order=order)

        return product_ids
