from odoo import models, fields, api, _


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    selected_uom_ids = fields.Many2many(string="UOM Ids", related='product_id.selected_uom_ids')
    purchase_multi_uom_id = fields.Many2one("product.multi.uom.price", string="Custom UOM",
                                            domain="[('id', 'in', selected_uom_ids)]")
    purchase_multi_uom_cost = fields.Float(string="UOM Cost", related='purchase_multi_uom_id.cost')


    @api.onchange('purchase_multi_uom_id')
    def purchase_multi_uom_id_change(self):
        if self.purchase_multi_uom_id:
            self.product_uom = self.purchase_multi_uom_id.uom_id
            self.price_unit = self.purchase_multi_uom_id.cost


    @api.onchange('purchase_multi_uom_id', 'product_uom', 'product_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return

        if self.purchase_multi_uom_id:
            self.product_uom = self.purchase_multi_uom_id.uom_id
            self.price_unit = self.purchase_multi_uom_id.cost
        else:
            # Update the price_unit based on the default UOM if purchase_multi_uom_id is not set
            self.price_unit = self.product_id.standard_price