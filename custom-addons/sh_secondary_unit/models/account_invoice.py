# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api

class ShAccountInvoice(models.Model):
    _inherit = 'account.move'

    def _prepare_invoice_line_from_po_line(self, line):
        res = super(ShAccountInvoice,
                    self)._prepare_invoice_line_from_po_line(line)
        res.update({
            'sh_sec_qty': line.sh_sec_qty,
            'sh_sec_uom': line.sh_sec_uom.id,
        })
        return res


class ShAccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    sh_sec_qty = fields.Float(
        "Secondary Qty",
        digits='Product Unit of Measure',
        compute="_compute_sh_sec_qty",
        store=True
    )
    sh_sec_uom = fields.Many2one(
        "uom.uom",
        'Secondary UOM',
        compute="_compute_secondary_uom",
        readonly=False,
        store=True
    )
    sh_is_secondary_unit = fields.Boolean(
        "Related Sec Unit",
        related="product_id.sh_is_secondary_unit"
    )
    category_id = fields.Many2one(
        "uom.category",
        "Account UOM Category",
        related="product_uom_id.category_id"
    )

    from_sec_qty = fields.Boolean(default=False)
    from_product_qty = fields.Boolean(default=False)

    @api.depends('quantity', 'product_uom_id')
    def _compute_sh_sec_qty(self):
        for rec in self:
            if rec and rec.sh_is_secondary_unit and rec.sh_sec_uom and not rec.from_sec_qty:
                rec.from_product_qty = True
                rec.sh_sec_qty = rec.product_uom_id._compute_quantity(
                    rec.quantity, rec.sh_sec_uom
                )

    @api.onchange('sh_sec_qty', 'sh_sec_uom')
    def onchange_sh_sec_qty_sh(self):
        if self:
            for rec in self:
                if rec.sh_is_secondary_unit and rec.product_uom_id and not rec.from_product_qty:
                    rec.from_sec_qty = True
                    rec.quantity = rec.sh_sec_uom._compute_quantity(
                        rec.sh_sec_qty,
                        rec.product_uom_id
                    )

    @api.depends('product_id', 'product_uom_id')
    def _compute_secondary_uom(self):
        if self:
            for rec in self:
                if rec.product_id and rec.product_id.sh_is_secondary_unit and rec.product_id.uom_id:
                    rec.sh_sec_uom = rec.product_id.sh_secondary_uom.id
                elif not rec.product_id.sh_is_secondary_unit:
                    rec.sh_sec_uom = False
                    rec.sh_sec_qty = 0.0

    @api.model_create_multi
    def create(self, values):
        res = super(ShAccountInvoiceLine, self).create(values)
        for each_move_line in res:
            if each_move_line.from_sec_qty:
                each_move_line.from_sec_qty = False
            if each_move_line.from_product_qty:
                each_move_line.from_product_qty = False
        return res

    def write(self, values):
        res = super(ShAccountInvoiceLine, self).write(values)
        for rec in self:
            if rec.from_product_qty:
                rec.from_product_qty = False
            if rec.from_sec_qty:
                rec.from_sec_qty = False
        return res
