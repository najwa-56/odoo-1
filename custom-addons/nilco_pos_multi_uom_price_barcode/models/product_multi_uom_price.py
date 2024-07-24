from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression
import re

class InheritMultiUOM(models.Model):
    _inherit = 'product.multi.uom.price'

    product_product_id = fields.Many2one('product.product')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    multi_barcode_for_product = fields.Boolean(related='company_id.multi_barcode_for_product', string="Multi Barcode For Product")
    model_ids = fields.Many2many('ir.model', string='Used For')  # Changed to
    barcode = fields.Char('Barcode')
    product_variant_id = fields.Many2one('product.product', related="product_product_id.product_variant_id", store=True)
    product_variant_count = fields.Integer('Product Variant Count')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    company_barcode_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    multi_barcode_for_product = fields.Boolean(related='company_barcode_id.multi_barcode_for_product', string="Multi Barcode For Product")
    multi_uom_price_barcode = fields.Char(string='Barcode', compute='_compute_multi_uom_price_barcode', store=True)

    @api.depends('multi_uom_price_id')
    def _compute_multi_uom_price_barcode(self):
        for record in self:
            if record.multi_uom_price_id:
                barcodes = record.multi_uom_price_id.mapped('barcode')
                record.multi_uom_price_barcode = ', '.join(filter(None, barcodes))
            else:
                record.multi_uom_price_barcode = ''

class ProductInherit(models.Model):
    _inherit = 'product.product'

    multi_uom_price_id = fields.One2many('product.multi.uom.price', 'product_product_id', string='Product Multi Barcodes')

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        company_id = self.env.user.company_id
        if not domain:
            domain = []

        if company_id.multi_barcode_for_product:
            if name:
                positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
                product_ids = []

                if operator in positive_operators:
                    # Search by default code or barcode
                    product_ids = self._search([('default_code', '=', name)] + domain, limit=limit, order=order)
                    if not product_ids:
                        product_ids = self._search([('barcode', '=', name)] + domain, limit=limit, order=order)
                        model_name = self._context.get('create_date_model')
                        model_name_dict = {
                            "sale.order.line": "Sales Order",
                            "purchase.order.line": "Purchase Order",
                            "account.move.line": "Account",
                            "stock.scrap": "Scrap",
                            "stock.move": "Transfer",
                            "stock.quant": "Quants",
                            "stock.warehouse.orderpoint": "Minimum Inventory Rule"
                        }
                        model_name = model_name_dict.get(model_name, model_name)

                        product_barcode_ids = self.env['product.multi.uom.price']._search([
                            ('barcode', operator, name), ('model_ids.name', "=", model_name)
                        ])

                        if product_barcode_ids:
                            product_ids = self._search([
                                '|',
                                ('multi_uom_price_id', 'in', product_barcode_ids),
                                ('product_id.multi_uom_price_id', 'in', product_barcode_ids)
                            ], limit=limit, order=order)
                else:
                    # Handle other operators
                    domain_add = expression.AND([
                        domain,
                        expression.OR([
                            ['&', ('default_code', operator, name), ('name', operator, name)],
                            ['&', ('default_code', '=', False), ('name', operator, name)],
                        ])
                    ])
                    product_ids = self._search(domain_add, limit=limit, order=order)
                    if not product_ids:
                        ptrn = re.compile('(\[(.*?)\])')
                        res = ptrn.search(name)
                        if res:
                            product_ids = self._search([('default_code', '=', res.group(2))] + domain, limit=limit, order=order)

                if not product_ids and self._context.get('partner_id'):
                    suppliers_ids = self.env['product.supplierinfo']._search([
                        ('product_name', '=', self._context.get('partner_id')),
                        '|',
                        ('product_code', operator, name),
                        ('product_name', operator, name)
                    ])
                    if suppliers_ids:
                        product_ids = self._search([('product_id.seller_ids', 'in', suppliers_ids)], limit=limit, order=order)

                # Search Record base on Multi Barcode
                product_barcode_ids = self.env['product.multi.uom.price']._search([
                    ('barcode', operator, name), ('model_ids.name', "=", model_name)
                ])
                if product_barcode_ids:
                    product_ids = self._search([
                        '|',
                        ('multi_uom_price_id', 'in', product_barcode_ids),
                        ('product_id.multi_uom_price_id', 'in', product_barcode_ids)
                    ], limit=limit, order=order)

            else:
                product_ids = self._search(domain, limit=limit, order=order)
        else:
            product_ids = self._search(domain, limit=limit, order=order)

        return product_ids