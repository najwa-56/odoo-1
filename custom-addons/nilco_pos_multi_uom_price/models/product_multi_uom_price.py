from odoo import models, fields, api, _


class multi_uom(models.Model):
    _name = 'product.multi.uom.price'
    _rec_name = 'uom_id'

    product_id = fields.Many2one('product.template',string= 'Product', index=True)#,required=True
    category_id = fields.Many2one(related='product_id.uom_id.category_id', index=True)
    uom_id = fields.Many2one('uom.uom', string="الوحدة", domain="[('category_id', '=', category_id)]", index=True)#,required=True
    price = fields.Float(string='السعر',required=True,digits='Product Price')
    cost = fields.Float(string='التكلفة', required=True ,digits='Product Cost',compute="_compute_calculated_cost")
    qty = fields.Float(string="الكمية" )
    name_field = fields.Char(store=True, string="أسم الوحدة")
    ratio = fields.Float(related='uom_id.ratio', string="Ratio", store=True)

    @api.depends('ratio', 'product_id.standard_price')
    def _compute_calculated_cost(self):
        for record in self:
            if record.ratio and record.product_id.standard_price:
                record.cost = record.ratio * record.product_id.standard_price
            else:
                record.cost = 0.0

# _sql_constraints = [
     #   ('product_multi_uom_price_uniq',
      #   'UNIQUE (product_id,uom_id)',
        # _('UOM Product Must Be Unique !'))]


