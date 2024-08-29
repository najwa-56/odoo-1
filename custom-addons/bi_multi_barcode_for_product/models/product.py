
from odoo.exceptions import UserError, ValidationError
import logging
import re
from odoo import api, fields, models, tools, _
from odoo.osv import expression
from odoo.http import request


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_barcode = fields.One2many('product.barcode', 'product_tmpl_id',string='Product Multi Barcodes')
    company_barcode_id = fields.Many2one('res.company', 'company', default=lambda self: self.env.user.company_id)
    multi_barcode_for_product = fields.Boolean(related='company_barcode_id.multi_barcode_for_product', string="Multi Barcode For Product")



class ProductInherit(models.Model):
    _inherit = 'product.product'

    product_barcode = fields.One2many('product.barcode', 'product_id',string='Product Multi Barcodes')


    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        active_model = self._context.get('active_model') or self._inherit
        company_id = self.env.user.company_id
        if company_id.multi_barcode_for_product == True:
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
                        sale_order_line_model = "sale.order.line"
                        purchase_order_line_model = "purchase.order.line"
                        account_move_line_model = "account.move.line"
                        stock_scrap_model ="stock.scrap"
                        stock_move_model = "stock.move"
                        stock_quant_model ="stock.quant"
                        stock_warhouse ="stock.warehouse.orderpoint"
                        model_name = self._context.get('create_date_model')
                        if self._context.get('create_date_model') == sale_order_line_model:
                            model_name = "Sales Order"

                        elif self._context.get('create_date_model') == purchase_order_line_model:
                            model_name = "Purchase Order"

                        elif self._context.get('create_date_model') == account_move_line_model:
                            model_name = "Account"

                        elif self._context.get('create_date_model') == stock_scrap_model:
                            model_name = "Scrap"

                        elif self._context.get('create_date_model') == stock_move_model:
                            model_name = "Transfer"

                        elif self._context.get('create_date_model') == stock_quant_model:
                            model_name = "Quants"

                        elif self._context.get('create_date_model') == stock_warhouse:
                            model_name = "Minimum Inventory Rule"


                        product_barcode_ids = self.env['product.barcode']._search([
                        ('barcode', operator, name), ('model_ids.name', "=", model_name)])

                        if product_barcode_ids:
                            product_ids = list(self._search(['|',('barcode', '=', name),('product_barcode.barcode', '=', name)] + domain, limit=limit, order=order))
                            if product_ids:
                                return product_ids
                if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                    # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                    # on a database with thousands of matching products, due to the huge merge+unique needed for the
                    # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                    # Performing a quick memory merge of ids in Python will give much better performance
                    product_ids = list(self._search(domain + [('default_code', operator, name)], limit=limit))
                    if not limit or len(product_ids) < limit:
                        # we may underrun the limit because of dupes in the results, that's fine
                        limit2 = (limit - len(product_ids)) if limit else False
                        product2_ids = self._search(domain + [('name', operator, name), ('id', 'not in', product_ids)], limit=limit2, order=order)
                        product_ids.extend(product2_ids)

                elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                    domain_add = expression.OR([
                        ['&', ('default_code', operator, name), ('name', operator, name)],
                        ['&', ('default_code', '=', False), ('name', operator, name)],
                    ])
                    domain_add = expression.AND([domain, domain_add])
                    product_ids = list(self._search(domain_add, limit=limit, order=order))
                if not product_ids and operator in positive_operators:
                    ptrn = re.compile('(\[(.*?)\])')
                    res = ptrn.search(name)
                    if res:
                        product_ids = list(self._search([('default_code', '=', res.group(2))] + domain, limit=limit, order=order))
                # still no results, partner in context: search on supplier info as last hope to find something
                if not product_ids and self._context.get('partner_id'):
                    suppliers_ids = self.env['product.supplierinfo']._search([
                        ('product_name', '=', self._context.get('partner_id')),
                        '|',
                        ('product_code', operator, name),
                        ('product_name', operator, name)])
                    if suppliers_ids:
                        product_ids = self._search([('product_tmpl_id.seller_ids', 'in', suppliers_ids)], limit=limit, order=order)
                
                # Search Record base on Multi Barcode
                product_barcode_ids = self.env['product.barcode']._search([
                ('barcode', operator, name), ('model_ids.name', "=", model_name)])
                if product_barcode_ids :
                    
                    product_ids = list(self._search([
                        '|',
                        ('product_barcode', 'in', product_barcode_ids),
                        ('product_tmpl_id.product_barcode', 'in', product_barcode_ids)], 
                        limit=limit, order=order))
            else:
                product_ids = self._search(domain, limit=limit, order=order)
            product_ids1= product_ids
            
            return product_ids1
        else:
            if not domain:
                domain = []
            if name:
                positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
                product_ids = []
                model_name = []
                if operator in positive_operators:
                    product_ids = list(self._search([('default_code', '=', name)] + domain, limit=limit, order=order))
                    if not product_ids:
                        product_ids = list(self._search(['|',('barcode', '=', name),('product_barcode.barcode', '=', name)] + domain, limit=limit, order=order))
                        if product_ids:
                                return product_ids
                if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                    # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                    # on a database with thousands of matching products, due to the huge merge+unique needed for the
                    # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                    # Performing a quick memory merge of ids in Python will give much better performance
                    product_ids = list(self._search(domain + [('default_code', operator, name)], limit=limit))
                    if not limit or len(product_ids) < limit:
                        # we may underrun the limit because of dupes in the results, that's fine
                        limit2 = (limit - len(product_ids)) if limit else False
                        product2_ids = self._search(domain + [('name', operator, name), ('id', 'not in', product_ids)], limit=limit2, order=order)
                        product_ids.extend(product2_ids)
                elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                    domain_add = expression.OR([
                        ['&', ('default_code', operator, name), ('name', operator, name)],
                        ['&', ('default_code', '=', False), ('name', operator, name)],
                    ])
                    domain_add = expression.AND([domain, domain_add])
                    product_ids = list(self._search(domain_add, limit=limit, order=order))

                if not product_ids and operator in positive_operators:
                    ptrn = re.compile('(\[(.*?)\])')
                    res = ptrn.search(name)
                    if res:
                        product_ids = list(self._search([('default_code', '=', res.group(2))] + domain, limit=limit, order=order))
                # still no results, partner in context: search on supplier info as last hope to find something
                
                if not product_ids and self._context.get('partner_id'):
                    
                    suppliers_ids = self.env['product.supplierinfo']._search([
                        ('product_name', '=', self._context.get('partner_id')),
                        '|',
                        ('product_code', operator, name),
                        ('product_name', operator, name)])
                    if suppliers_ids:
                        product_ids = self._search([('product_tmpl_id.seller_ids', 'in', suppliers_ids)], limit=limit, order=order)

                # Search Record base on Multi Barcode

                product_barcode_ids = self.env['product.barcode']._search([
                ('barcode', operator, name)])
                if product_barcode_ids:
                    
                    product_ids = list(self._search([
                        ('product_tmpl_id.product_barcode', 'in', product_barcode_ids)], 
                        limit=limit, order=order))

            else:
                product_ids = self._search(domain, limit=limit, order=order)
            return product_ids



class Barcode(models.Model):
    _name = 'product.barcode'
    _description = "Product Barcode"

    product_id = fields.Many2one('product.product')
    barcode = fields.Char(string='Barcode',required=True)
    product_tmpl_id = fields.Many2one('product.template')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    multi_barcode_for_product = fields.Boolean(related='company_id.multi_barcode_for_product', string="Multi Barcode For Product")
    model_ids = fields.Many2one('ir.model',string ='Used For')

    _sql_constraints = [
        ('uniq_barcode', 'unique(barcode)', "A barcode can only be assigned to one product !"),
    ]