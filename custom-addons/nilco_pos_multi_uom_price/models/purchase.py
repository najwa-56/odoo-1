from odoo import models, fields, api, _


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    selected_uom_ids = fields.Many2many(string="UOM Ids", related='product_id.selected_uom_ids')
    purchase_multi_uom_id = fields.Many2one("product.multi.uom.price", string="Custom UOM",
                                            domain="[('id', 'in', selected_uom_ids)]")
    purchase_multi_uom_cost = fields.Float(string="UOM Cost", related='purchase_multi_uom_id.cost')


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

    @api.onchange('purchase_multi_uom_id')
    def _onchange_purchase_multi_uom_id(self):
        for record in self:
            if record.purchase_multi_uom_cost:
                record.price_unit = record.purchase_multi_uom_cost

    @api.model
    def create(self, vals):
        if 'purchase_multi_uom_id' in vals:
            multi_uom = self.env['product.multi.uom.price'].browse(vals['purchase_multi_uom_id'])
            vals['price_unit'] = multi_uom.cost
        return super(PurchaseOrderLine, self).create(vals)

    def write(self, vals):
        if 'purchase_multi_uom_id' in vals:
            multi_uom = self.env['product.multi.uom.price'].browse(vals['purchase_multi_uom_id'])
            vals['price_unit'] = multi_uom.cost
        return super(PurchaseOrderLine, self).write(vals)