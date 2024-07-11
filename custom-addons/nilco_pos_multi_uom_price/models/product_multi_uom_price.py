from odoo import models, fields, api, _


class multi_uom(models.Model):
    _name = 'product.multi.uom.price'
    _rec_name = 'uom_id'

    product_id = fields.Many2one('product.template',string= 'Product')#,required=True
    category_id = fields.Many2one(related='product_id.uom_id.category_id')
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", domain="[('category_id', '=', category_id)]")#,required=True
    price = fields.Float(string='Price',required=True,digits='Product Price')   
   # _sql_constraints = [
     #   ('product_multi_uom_price_uniq',
      #   'UNIQUE (product_id,uom_id)',
        # _('UOM Product Must Be Unique !'))]
    

#class SaleOrderLine(models.Model):
  #  _inherit = 'sale.order.line'

  #  multi_uom_price_id = fields.Many2one('product.multi.uom.price', string='Multi UOM Price')
   # multi_uom_id = fields.Many2one('uom.uom', string='Multi UOM', related='product_id.uom_id')

  #  @api.depends('multi_uom_price_id')
   # def _compute_multi_uom_id(self):
      #  for line in self:
         #   line.multi_uom_id = line.multi_uom_price_id.uom_id
