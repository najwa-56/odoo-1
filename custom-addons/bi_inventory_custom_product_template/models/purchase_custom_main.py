# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from pickle import TRUE
import string
from odoo import models, fields, api, _
from datetime import datetime

class inventory_custom(models.Model):
    _name = 'inventory.custom.product'
    _description = 'inventory Custom Product'

    name = fields.Char("Template",required=True)
    check_active = fields.Boolean("Active")
    inventory_custom_line_ids = fields.One2many("inventory.custom.lines","inventory_custom_id")

class inventory_custom_lines(models.Model):
    _name = 'inventory.custom.lines'

    _description = 'inventory Custom lines'

    inventory_custom_id = fields.Many2one("inventory.custom.product")

    product_id = fields.Many2one("product.product",string = "Product",required=True)
    uom = fields.Many2one("uom.uom",string="UOM",required=True)
    

    @api.onchange("product_id")
    def onchnange_product(self):
        for i in self:
            if i.product_id:
                i.desc_name = i.product_id.display_name	



class inherit_inventory(models.Model):
    _inherit = "stock.picking"

    product_template_id = fields.Many2one("inventory.custom.product",string="Product Template",domain=[('check_active', '=', True)])

    @api.onchange('product_template_id')
    def onchange_product_template(self): 
        template_list= []
        
        for t in self.order_line:
            if not t.custom :
                template_list.append((0,0,{
                        "custom":False,
                        "product_id":t.product_id,
                        "name":t.name,
                        "product_uom":t.product_uom,
                    }))		
        if self.product_template_id:	
            product_list = []
            for i in self.product_template_id:
                for j in i.inventory_custom_line_ids:
                    product_list.append((0,0,{
                        "date_planned":datetime.now(),
                        "product_id":j.product_id.id,
                        "name":j.desc_name,
                        "product_uom":j.uom.id,
                        "custom":True,
                    }))


                self.write({'order_line': False}) 
                self.update({"order_line":template_list})
                self.update({"order_line":product_list})

    '''
    @api.depends('order_line.taxes_id', 'order_line.price_subtotal', 'amount_total', 'amount_untaxed')
    def _compute_tax_totals(self):
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            order.tax_totals = self.env['account.tax']._prepare_tax_totals(
                [x._convert_to_tax_base_line_dict() for x in order_lines],
                order.currency_id or order.company_id.currency_id,
            )
                        
            order.tax_totals['amount_untaxed']=sum(order_lines.mapped('price_subtotal'))
            


class inherit_inventory_order_line(models.Model):
    _inherit = "inventory.order.line"
    
    custom =fields.Boolean()


    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount')
    def _compute_amount(self):
        for line in self:
            tax_results = self.env['account.tax']._compute_taxes([line._convert_to_tax_base_line_dict()])
            totals = list(tax_results['totals'].values())[0]
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']

            if line.custom:
                custom_unit_price = 0.0  
                for rec in line:
                    for vals in rec.order_id.product_template_id.inventory_custom_line_ids:
                        if vals.product_id.id == line.product_id.id:
                            custom_unit_price += vals.unit_price
                            

                line.update({
                    'price_unit': custom_unit_price,
                    'price_subtotal': custom_unit_price * line.product_qty,
                    'price_tax': amount_tax,
                    'price_total': (custom_unit_price * line.product_qty),
                })
            
            else:
                line.update({
                    'price_subtotal': amount_untaxed,
                    'price_tax': amount_tax,
                    'price_total': amount_untaxed + amount_tax,
                })			
'''