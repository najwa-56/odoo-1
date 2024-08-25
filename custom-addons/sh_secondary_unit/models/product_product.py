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



    '''UOMs'''

    '''show uoms in column'''
    selected_uom_ids = fields.Many2many(
        comodel_name="product.multi.uom.price",
        string="Uom Ids",
        compute='_get_all_uom_id',
        store=True
    )

    uom_id_1 = fields.Many2one('product.multi.uom.price', string='UOM 1', compute='_compute_uom_columns')
    uom_id_2 = fields.Many2one('product.multi.uom.price', string='UOM 2', compute='_compute_uom_columns')
    uom_id_3 = fields.Many2one('product.multi.uom.price', string='UOM 3', compute='_compute_uom_columns')
    uom_id_4 = fields.Many2one('product.multi.uom.price', string='UOM 4', compute='_compute_uom_columns')
    uom_id_5 = fields.Many2one('product.multi.uom.price', string='UOM 5', compute='_compute_uom_columns')
    uom_id_6 = fields.Many2one('product.multi.uom.price', string='UOM 6', compute='_compute_uom_columns')
    @api.depends('selected_uom_ids')
    def _compute_uom_columns(self):
        for record in self:
            uoms = record.selected_uom_ids
            record.uom_id_1 = uoms[0] if len(uoms) > 0 else False
            record.uom_id_2 = uoms[1] if len(uoms) > 1 else False
            record.uom_id_3 = uoms[2] if len(uoms) > 2 else False
            record.uom_id_4 = uoms[3] if len(uoms) > 3 else False
            record.uom_id_5 = uoms[4] if len(uoms) > 4 else False
            record.uom_id_6 = uoms[5] if len(uoms) > 5 else False

    '''show uoms in column'''

    '''show uoms in qty'''
    uom_id_1_onhand1 = fields.Float('On Hand',compute='_compute_secondary_unit_on_hand_qty1')
    uom_id_2_onhand2 = fields.Float('On Hand', compute='_compute_secondary_unit_on_hand_qty2')
    uom_id_3_onhand3 = fields.Float('On Hand', compute='_compute_secondary_unit_on_hand_qty3')
    uom_id_4_onhand4 = fields.Float('On Hand', compute='_compute_secondary_unit_on_hand_qty4')
    uom_id_5_onhand5 = fields.Float('On Hand', compute='_compute_secondary_unit_on_hand_qty5')
    uom_id_6_onhand6 = fields.Float('On Hand', compute='_compute_secondary_unit_on_hand_qty6')
    def _compute_secondary_unit_on_hand_qty1(self):
        for rec in self:
            if rec.uom_id and rec.uom_id_1 and rec.uom_id_1.uom_id:
                # Assuming uom_id_1 has a field 'uom_id' that is of type 'uom.uom'
                rec.uom_id_1_onhand1 = rec.uom_id._compute_quantity(
                    rec.qty_available, rec.uom_id_1.uom_id)
            else:
                rec.uom_id_1_onhand1 = 0.0

    def _compute_secondary_unit_on_hand_qty2(self):
        for rec in self:
            if rec.uom_id and rec.uom_id_2 and rec.uom_id_2.uom_id:
                # Assuming uom_id_1 has a field 'uom_id' that is of type 'uom.uom'
                rec.uom_id_2_onhand2 = rec.uom_id._compute_quantity(
                    rec.qty_available, rec.uom_id_2.uom_id)
            else:
                rec.uom_id_2_onhand2 = 0.0
    def _compute_secondary_unit_on_hand_qty3(self):
        for rec in self:
            if rec.uom_id and rec.uom_id_3 and rec.uom_id_3.uom_id:
                # Assuming uom_id_1 has a field 'uom_id' that is of type 'uom.uom'
                rec.uom_id_3_onhand3 = rec.uom_id._compute_quantity(
                    rec.qty_available, rec.uom_id_3.uom_id)
            else:
                rec.uom_id_3_onhand3 = 0.0

    def _compute_secondary_unit_on_hand_qty4(self):
        for rec in self:
            if rec.uom_id and rec.uom_id_4 and rec.uom_id_4.uom_id:
                # Assuming uom_id_1 has a field 'uom_id' that is of type 'uom.uom'
                rec.uom_id_4_onhand4 = rec.uom_id._compute_quantity(
                    rec.qty_available, rec.uom_id_4.uom_id)
            else:
                rec.uom_id_4_onhand4 = 0.0

    def _compute_secondary_unit_on_hand_qty5(self):
        for rec in self:
            if rec.uom_id and rec.uom_id_5 and rec.uom_id_5.uom_id:
                # Assuming uom_id_1 has a field 'uom_id' that is of type 'uom.uom'
                rec.uom_id_5_onhand5 = rec.uom_id._compute_quantity(
                    rec.qty_available, rec.uom_id_5.uom_id)
            else:
                rec.uom_id_5_onhand5 = 0.0

    def _compute_secondary_unit_on_hand_qty5(self):
        for rec in self:
            if rec.uom_id and rec.uom_id_6 and rec.uom_id_6.uom_id:
                # Assuming uom_id_1 has a field 'uom_id' that is of type 'uom.uom'
                rec.uom_id_6_onhand6 = rec.uom_id._compute_quantity(
                    rec.qty_available, rec.uom_id_6.uom_id)
            else:
                rec.uom_id_6_onhand6 = 0.0

    '''UOMs'''
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
