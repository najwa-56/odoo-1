from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression
import re



class Inheritmulti_uom(models.Model):
    _inherit = 'product.multi.uom.price'


    product_product_id = fields.Many2one('product.product')
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


class ProductInherit(models.Model):
    _inherit = 'product.product'

    product_barcode = fields.One2many('product.multi.uom.price', 'product_product_id', string='Product Multi Barcodes')

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        active_model = self._context.get('active_model') or self._inherit
        company_id = self.env.user.company_id
        if company_id.multi_barcode_for_product:
            if not domain:
                domain = []
            if name:
                positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
                product_ids = []
                model_name = []
                if operator in positive_operators:
                    product_ids = list(self._search([('default_code', '=', name)] + domain, limit=limit, order=order))
                    if not product_ids:
                        product_ids = list(self._search([('barcode', '=', name)] + domain, limit=limit, order=order))
                        if not product_ids:
                            product_barcode_ids = self.env['product.multi.uom.price']._search([
                                ('barcode', operator, name)])
                            if product_barcode_ids:
                                product_ids = list(self._search([
                                                                    '|', ('barcode', '=', name),
                                                                    ('product_barcode.barcode', '=', name)
                                                                ] + domain, limit=limit, order=order))
                                if product_ids:
                                    return product_ids

                            # Search in product.multi.uom.price barcodes
                            multi_uom_price_ids = self.env['product.multi.uom.price']._search([
                                ('barcode', operator, name)])
                            if multi_uom_price_ids:
                                product_ids = list(self._search([
                                                                    '|', (
                                    'id', 'in', [uom.product_product_id.id for uom in multi_uom_price_ids])
                                                                ] + domain, limit=limit, order=order))
                                if product_ids:
                                    return product_ids

                if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                    product_ids = list(self._search(domain + [('default_code', operator, name)], limit=limit))
                    if not limit or len(product_ids) < limit:
                        limit2 = (limit - len(product_ids)) if limit else False
                        product2_ids = self._search(domain + [('name', operator, name), ('id', 'not in', product_ids)],
                                                    limit=limit2, order=order)
                        product_ids.extend(product2_ids)
                elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                    domain_add = expression.OR([
                        ['&', ('default_code', operator, name), ('name', operator, name)],
                        ['&', ('default_code', '=', False), ('name', operator, name)],
                    ])
                    domain_add = expression.AND([domain, domain_add])
                    product_ids = list(self._search(domain_add, limit=limit, order=order))
                if not product_ids and operator in positive_operators:
                    ptrn = re.compile(r'(\[(.*?)\])')
                    res = ptrn.search(name)
                    if res:
                        product_ids = list(
                            self._search([('default_code', '=', res.group(2))] + domain, limit=limit, order=order))
                if not product_ids and self._context.get('partner_id'):
                    suppliers_ids = self.env['product.supplierinfo']._search([
                        ('product_name', '=', self._context.get('partner_id')),
                        '|', ('product_code', operator, name), ('product_name', operator, name)])
                    if suppliers_ids:
                        product_ids = self._search([('product_tmpl_id.seller_ids', 'in', suppliers_ids)], limit=limit,
                                                   order=order)

                # Search Record base on Multi Barcode
                product_barcode_ids = self.env['product.multi.uom.price']._search([
                    ('barcode', operator, name)])
                if product_barcode_ids:
                    product_ids = list(self._search([
                        '|', ('product_barcode', 'in', product_barcode_ids),
                        ('product_tmpl_id.product_barcode', 'in', product_barcode_ids)], limit=limit, order=order))

                # Search Record based on multi.uom.price barcode
                multi_uom_price_ids = self.env['product.multi.uom.price']._search([
                    ('barcode', operator, name)])
                if multi_uom_price_ids:
                    product_ids = list(self._search([
                                                        '|', (
                        'id', 'in', [uom.product_product_id.id for uom in multi_uom_price_ids])
                                                    ] + domain, limit=limit, order=order))

            else:
                product_ids = self._search(domain, limit=limit, order=order)
            return product_ids
        else:
            if not domain:
                domain = []
            if name:
                positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
                product_ids = []
                if operator in positive_operators:
                    product_ids = list(self._search([('default_code', '=', name)] + domain, limit=limit, order=order))
                    if not product_ids:
                        product_ids = list(
                            self._search(['|', ('barcode', '=', name), ('product_barcode.barcode', '=', name)] + domain,
                                         limit=limit, order=order))
                        if not product_ids:
                            multi_uom_price_ids = self.env['product.multi.uom.price']._search([
                                ('barcode', operator, name)])
                            if multi_uom_price_ids:
                                product_ids = list(self._search([
                                                                    '|', (
                                    'id', 'in', [uom.product_product_id.id for uom in multi_uom_price_ids])
                                                                ] + domain, limit=limit, order=order))
                                if product_ids:
                                    return product_ids
                if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                    product_ids = list(self._search(domain + [('default_code', operator, name)], limit=limit))
                    if not limit or len(product_ids) < limit:
                        limit2 = (limit - len(product_ids)) if limit else False
                        product2_ids = self._search(domain + [('name', operator, name), ('id', 'not in', product_ids)],
                                                    limit=limit2, order=order)
                        product_ids.extend(product2_ids)
                elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                    domain_add = expression.OR([
                        ['&', ('default_code', operator, name), ('name', operator, name)],
                        ['&', ('default_code', '=', False), ('name', operator, name)],
                    ])
                    domain_add = expression.AND([domain, domain_add])
                    product_ids = list(self._search(domain_add, limit=limit, order=order))
                if not product_ids and operator in positive_operators:
                    ptrn = re.compile(r'(\[(.*?)\])')
                    res = ptrn.search(name)
                    if res:
                        product_ids = list(
                            self._search([('default_code', '=', res.group(2))] + domain, limit=limit, order=order))
                if not product_ids and self._context.get('partner_id'):
                    suppliers_ids = self.env['product.supplierinfo']._search([
                        ('product_name', '=', self._context.get('partner_id')),
                        '|', ('product_code', operator, name), ('product_name', operator, name)])
                    if suppliers_ids:
                        product_ids = self._search([('product_tmpl_id.seller_ids', 'in', suppliers_ids)], limit=limit,
                                                   order=order)

                # Search Record based on multi.uom.price barcode
                multi_uom_price_ids = self.env['product.multi.uom.price']._search([
                    ('barcode', operator, name)])
                if multi_uom_price_ids:
                    product_ids = list(self._search([
                                                        '|', (
                        'id', 'in', [uom.product_product_id.id for uom in multi_uom_price_ids])
                                                    ] + domain, limit=limit, order=order))

            else:
                product_ids = self._search(domain, limit=limit, order=order)
            return product_ids
