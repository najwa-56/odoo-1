from odoo import models, fields, api, _


class multi_uom(models.Model):
    _name = 'product.multi.uom.price'
    _rec_name = 'uom_id'

    product_id = fields.Many2one('product.template',string= 'Product')#,required=True
    category_id = fields.Many2one(related='product_id.uom_id.category_id')
    uom_id = fields.Many2one('uom.uom', string="الوحدة", domain="[('category_id', '=', category_id)]")#,required=True
    price = fields.Float(string='السعر',required=True,digits='Product Price')
    cost = fields.Float(string='التكلفة',required=True,digits='Product Cost')
    qty = fields.Float(string="الكمية" )
    name_field = fields.Char(string="أسم الوحدة")


   # _sql_constraints = [
     #   ('product_multi_uom_price_uniq',
      #   'UNIQUE (product_id,uom_id)',
        # _('UOM Product Must Be Unique !'))]
