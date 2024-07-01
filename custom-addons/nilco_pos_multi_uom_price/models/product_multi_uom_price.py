from odoo import models, fields, api, _


class multi_uom(models.Model):
    _name = 'product.multi.uom.price'

    product_id = fields.Many2one('product.template',string= 'Product',required=True)
    category_id = fields.Many2one(related='product_id.uom_id.category_id')
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", domain="[('category_id', '=', category_id)]",required=True)
    price = fields.Float(string='Price',required=True,digits='Product Price')   
    _sql_constraints = [
        ('product_multi_uom_price_uniq',
         'UNIQUE (product_id,uom_id)',
         _('UOM Product Must Be Unique !'))]
    
