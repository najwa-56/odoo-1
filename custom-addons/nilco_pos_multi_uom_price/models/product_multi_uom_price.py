from odoo import models, fields, api, _


class multi_uom(models.Model):
    _name = 'product.multi.uom.price'
    _rec_name = 'uom_id'

    product_id = fields.Many2one('product.template',string= 'Product')#,required=True
    category_id = fields.Many2one(related='product_id.uom_id.category_id')
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", domain="[('category_id', '=', category_id)]")#,required=True
    price = fields.Float(string='Price',required=True,digits='Product Price')
    cost = fields.Float(string='Cost',required=True,digits='Product Cost')
    qty = fields.Float(string="Quantity")

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
class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule12(self, products, quantity, currency=None, uom=None, date=False, compute_price=True, pro_price=0.0, **kwargs):
        self.ensure_one()

        currency = currency or self.currency_id or self.env.company.currency_id
        currency.ensure_one()

        if not products:
            return {}

        if not date:
            date = fields.Datetime.now()

        rules = self._get_applicable_rules(products, date, **kwargs)

        results = {}
        price = pro_price
        for product in products:
            suitable_rule = self.env['product.pricelist.item']
            product_uom = product.uom_id
            target_uom = uom or product_uom

            if target_uom != product_uom:
                qty_in_product_uom = target_uom._compute_quantity(quantity, product_uom, raise_if_failure=False)
            else:
                qty_in_product_uom = quantity

            for rule in rules:
                if rule._is_applicable_for(product, qty_in_product_uom):
                    suitable_rule = rule
                    break

            if compute_price:
                price = suitable_rule._compute_price(product, quantity, target_uom, date=date, currency=currency)
            else:
                price = pro_price
            results[product.id] = (price, suitable_rule.id)
        return results

    def _get_product_price_rule12(self, product, *args, **kwargs):
        self.ensure_one()
        return self._compute_price_rule12(product, *args, **kwargs)[product.id]