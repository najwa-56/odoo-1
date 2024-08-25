# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class ShProductProduct(models.Model):
    _inherit = 'product.product'

    category_id = fields.Many2one(
        "uom.category",
        "Product UOM Category",
        related="uom_id.category_id"
    )


class ShProductTemplate(models.Model):
    _inherit = 'product.template'

    sh_secondary_uom = fields.Many2one('uom.uom', 'Secondary UOM')
    sh_secondary_uom_onhand = fields.Float(
        'On Hand',
        compute='_compute_secondary_unit_on_hand_qty'
    )
    sh_secondary_uom_forecasted = fields.Float(
        'Forecasted',
        compute='_compute_secondary_unit_forecasted_qty'
    )
    sh_uom_name = fields.Char(
        "Secondary UOM",
        related='sh_secondary_uom.name'
    )
    sh_is_secondary_unit = fields.Boolean("is Secondary Unit ?")
    category_id = fields.Many2one(
        "uom.category",
        "UOM Category",
        related="uom_id.category_id"
    )

    @api.onchange('sh_is_secondary_unit')
    def onchange_sh_is_secondary_unit(self):
        if not self.sh_is_secondary_unit:
            self.sh_secondary_uom = False

    def _compute_secondary_unit_on_hand_qty(self):
        if self:
            for rec in self:
                if rec.sh_secondary_uom:
                    rec.sh_secondary_uom_onhand = rec.uom_id._compute_quantity(
                        rec.qty_available,
                        rec.sh_secondary_uom
                    )
                else:
                    rec.sh_secondary_uom_onhand = 00

    def _compute_secondary_unit_forecasted_qty(self):
        if self:
            for rec in self:
                if rec.sh_secondary_uom:
                    rec.sh_secondary_uom_forecasted = rec.uom_id._compute_quantity(
                        rec.virtual_available,
                        rec.sh_secondary_uom
                    )
                else:
                    rec.sh_secondary_uom_forecasted = 00

    def action_open_sh_quants(self):
        if self:
            for data in self:
                products = data.mapped('product_variant_ids')
                action = data.env.ref('stock.product_open_quants').read()[0]
                action['domain'] = [('product_id', 'in', products.ids)]
                action['context'] = {'search_default_internal_loc': 1}
                return action
        else:
            return None

    '''test uom2'''
    sh_secondary_uom2 = fields.Many2one('uom.uom', 'Secondary UOM')
    sh_secondary_uom_onhand2 = fields.Float(
        'On Hand',
        compute='_compute_secondary_unit_on_hand_qty2'
    )
    def _compute_secondary_unit_on_hand_qty2(self):
        if self:
            for rec in self:
                if rec.sh_secondary_uom2:
                    rec.sh_secondary_uom_onhand2 = rec.uom_id._compute_quantity(
                        rec.qty_available,
                        rec.sh_secondary_uom2
                    )
                else:
                    rec.sh_secondary_uom_onhand2 = 00

    '''test'''

    '''test uom3'''
    sales_multi_uom_id = fields.Many2one("product.multi.uom.price", string="Cust UOM",
                                         domain="[('id', 'in', selected_uom_ids)]")

    '''test'''
class ShStockQuant(models.Model):
    _inherit = 'stock.quant'

    sh_secondary_unit_qty = fields.Float(
        'On Hand',
        compute='_compute_secondary_qty'
    )
    sh_secondary_unit = fields.Many2one(
        'uom.uom',
        'Secondary UOM',
        related='product_id.sh_secondary_uom'
    )

    @api.depends('quantity')
    def _compute_secondary_qty(self):
        for rec in self:
            rec.sh_secondary_unit_qty = 0.0
            if rec.quantity > 0.0 and rec.product_id.sh_secondary_uom:
                rec.sh_secondary_unit_qty = rec.product_uom_id._compute_quantity(
                    rec.quantity,
                    rec.product_id.sh_secondary_uom
                )
