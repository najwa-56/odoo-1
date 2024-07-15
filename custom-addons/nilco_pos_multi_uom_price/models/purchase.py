from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    selected_uom_ids = fields.Many2many(string="UOM Ids", related='product_id.selected_uom_ids')
    purchase_multi_uom_id = fields.Many2one("product.multi.uom.price", string="Custom UOM", domain="[('id', 'in', selected_uom_ids)]")

    @api.onchange('purchase_multi_uom_id')
    def purchase_multi_uom_id_change(self):
        self.ensure_one()
        if self.purchase_multi_uom_id:
            domain = {'product_uom': [('id', '=', self.purchase_multi_uom_id.uom_id.id)]}
            return {'domain': domain}

    @api.onchange('purchase_multi_uom_id', 'product_uom', 'product_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.purchase_multi_uom_id:
            values = {
                "product_uom": self.purchase_multi_uom_id.uom_id.id,
            }
            self.update(values)
            self.price_unit = self.purchase_multi_uom_id.cost  # Update price_unit with the cost from purchase_multi_uom_id
        