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

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.update({
                'product_uom': self.product_id.uom_po_id,
                'price_unit': self.product_id.standard_price,
                'date_planned': self.order_id.date_order
            })
            result = {
                'domain': {'purchase_multi_uom_id': [('product_id', '=', self.product_id.id)]},
            }
            return result

    @api.onchange('product_uom', 'product_qty', 'purchase_multi_uom_id')
    def _onchange_uom_id(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return

        if self.purchase_multi_uom_id:
            self.product_uom = self.purchase_multi_uom_id.uom_id
            self.price_unit = self.purchase_multi_uom_id.cost
        else:
            # Update the price_unit based on the default UOM if purchase_multi_uom_id is not set
            self.price_unit = self.product_id.standard_price

        # Additional validation logic for UOM category
        if self.product_id and self.product_uom:
            if self.product_id.uom_id.category_id.id != self.product_uom.category_id.id:
                warning = {
                    'title': _('Warning!'),
                    'message': _(
                        'The selected unit of measure is not compatible with the unit of measure of the product.'),
                }
                self.product_uom = self.product_id.uom_id
                return {'warning': warning}

        return

