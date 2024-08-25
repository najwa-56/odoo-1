# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api
from odoo.tools.float_utils import float_is_zero

class ShStockMove(models.Model):
    _inherit = "stock.move"

    sh_sec_qty = fields.Float(
        "Secondary Qty",
        digits='Product Unit of Measure',
        compute="_compute_sh_sec_qty",
        store=True,
        copy=False
    )
    sh_sec_done_qty = fields.Float(
        "Secondary Done Qty",
        digits='Product Unit of Measure',
        compute="_compute_sh_sec_done_qty",
        store=True,
        copy=False
    )
    sh_sec_uom = fields.Many2one(
        "uom.uom",
        'Secondary UOM',
        related="product_id.sh_secondary_uom",
        store=True,
        copy=False
    )
    sh_is_secondary_unit = fields.Boolean(
        "Related Sec Unit",
        related="product_id.sh_is_secondary_unit",
        store=True,
        copy=False
    )
    from_sec_qty = fields.Boolean(default=False)
    from_product_qty = fields.Boolean(default=False)

    from_sec_qty_done = fields.Boolean(default=False)
    from_qty_done = fields.Boolean(default=False)

    # @api.depends('quantity_done')
    @api.depends('quantity')
    def _compute_sh_sec_done_qty(self):
        for rec in self:
            if rec.sh_is_secondary_unit and rec.sh_sec_uom and rec.quantity != 0 and not rec.from_sec_qty_done:
                rec.from_qty_done = True
                rec.sh_sec_done_qty = rec.product_uom._compute_quantity(
                    rec.quantity, rec.sh_sec_uom
                )
                rec.sh_sec_qty = rec.product_uom._compute_quantity(
                    rec.quantity, rec.sh_sec_uom
                )
            # if rec.sh_is_secondary_unit and rec.sh_sec_uom and rec.quantity_done != 0 and not rec.from_sec_qty_done:
            #     rec.from_qty_done = True
            #     rec.sh_sec_done_qty = rec.product_uom._compute_quantity(
            #         rec.quantity_done, rec.sh_sec_uom
            #     )
            #     rec.sh_sec_qty = rec.product_uom._compute_quantity(
            #         rec.quantity_done, rec.sh_sec_uom
            #     )

    # @api.onchange('quantity_done')
    @api.onchange('quantity')
    def onchange_product_uom_done_qty_sh(self):
        if self and self.sh_is_secondary_unit and self.sh_sec_uom and not self.from_sec_qty_done:
            self.from_qty_done = True
            self.sh_sec_done_qty = self.product_uom._compute_quantity(
                self.quantity,
                # self.quantity_done,
                self.sh_sec_uom
            )
            self.sh_sec_qty = self.sh_sec_done_qty

    @api.onchange('sh_sec_done_qty')
    def onchange_sh_sec_done_qty_sh(self):
        if self and self.sh_is_secondary_unit and self.product_uom and not self.from_qty_done:
            self.from_sec_qty_done = True
            self.quantity = self.sh_sec_uom._compute_quantity(
                self.sh_sec_done_qty,
                self.product_uom
            )
            # self.quantity_done = self.sh_sec_uom._compute_quantity(
            #     self.sh_sec_done_qty,
            #     self.product_uom
            # )

    @api.depends('product_uom_qty', 'product_uom')
    def _compute_sh_sec_qty(self):
        for rec in self:
            if rec and rec.sh_is_secondary_unit and rec.sh_sec_uom and not rec.from_sec_qty:
                rec.from_product_qty = True
                rec.sh_sec_qty = rec.product_uom._compute_quantity(
                    rec.product_uom_qty, rec.sh_sec_uom
                )

    @api.onchange('sh_sec_qty', 'sh_sec_uom')
    def onchange_sh_sec_qty_sh(self):
        if self and self.sh_is_secondary_unit and self.product_uom and not self.from_product_qty:
            self.from_sec_qty = True
            self.product_uom_qty = self.sh_sec_uom._compute_quantity(
                self.sh_sec_qty,
                self.product_uom
            )

    @api.model
    def create(self, vals):
        res = super(ShStockMove, self).create(vals)
        if res.sale_line_id and res.sale_line_id.sh_is_secondary_unit and res.sale_line_id.sh_sec_uom:
            res.update({
                'sh_sec_uom': res.sale_line_id.sh_sec_uom.id,
                'sh_sec_qty': res.sale_line_id.sh_sec_qty
            })
        elif res.purchase_line_id and res.purchase_line_id.sh_is_secondary_unit and res.purchase_line_id.sh_sec_uom:
            res.update({
                'sh_sec_uom': res.purchase_line_id.sh_sec_uom.id,
                'sh_sec_qty': res.purchase_line_id.sh_sec_qty
            })
        return res


class ShStockMoveLine(models.Model):
    _inherit = "stock.move.line"

    sh_sec_qty = fields.Float(
        "Secondary Qty",
        digits='Product Unit of Measure',
        compute="_compute_sh_sec_qty",
    )
    sh_sec_uom = fields.Many2one(
        "uom.uom",
        'Secondary UOM',
        related="move_id.sh_sec_uom"
    )
    sh_is_secondary_unit = fields.Boolean(
        "Related Sec Unit",
        related="move_id.product_id.sh_is_secondary_unit"
    )
    from_sec_qty = fields.Boolean(default=False)
    from_qty_done = fields.Boolean(default=False)

    @api.depends('quantity')
    # @api.depends('qty_done')
    def _compute_sh_sec_qty(self):
        for rec in self:
            if rec and rec.sh_is_secondary_unit and rec.sh_sec_uom and not rec.from_sec_qty:
                rec.from_qty_done = True
                if rec.quantity > 0:
                    rec.sh_sec_qty = rec.product_uom_id._compute_quantity(
                        rec.quantity, rec.sh_sec_uom
                    )
                else:
                    rec.sh_sec_qty = 0
            else:
                rec.sh_sec_qty = 0

    @api.onchange('sh_sec_qty')
    def onchange_product_sec_done_qty_sh_move_line(self):
        if self and self.sh_is_secondary_unit and self.sh_sec_uom and not self.from_qty_done:
            self.from_sec_qty = True
            self.quantity = self.sh_sec_uom._compute_quantity(
                self.sh_sec_qty,
                self.product_uom_id
            )
            self.move_id.quantity = self.sh_sec_qty
            # self.move_id.quantity_done = self.sh_sec_qty

    def _get_aggregated_product_quantities(self, **kwargs):
        """ Returns a dictionary of products (key = id+name+description+uom+packaging) and corresponding values of interest.

        Allows aggregation of data across separate move lines for the same product. This is expected to be useful
        in things such as delivery reports. Dict key is made as a combination of values we expect to want to group
        the products by (i.e. so data is not lost). This function purposely ignores lots/SNs because these are
        expected to already be properly grouped by line.

        returns: dictionary {product_id+name+description+uom+packaging: {product, name, description, qty_done, product_uom, packaging}, ...}
        """
        aggregated_move_lines = {}

        def get_aggregated_properties(move_line=False, move=False):
            move = move or move_line.move_id
            uom = move.product_uom or move_line.product_uom_id
            name = move.product_id.display_name
            description = move.description_picking
            if description in [name, move.product_id.name]:
                description = False
            product = move.product_id
            line_key = f'{product.id}_{product.display_name}_{description or ""}_{uom.id}_{move.product_packaging_id or ""}'
            return (line_key, name, description, uom, move.product_packaging_id)

        def _compute_packaging_qtys(aggregated_move_lines):
            # Needs to be computed after aggregation of line qtys
            for line in aggregated_move_lines.values():
                if line['packaging']:
                    line['packaging_qty'] = line['packaging']._compute_qty(line['qty_ordered'], line['product_uom'])
                    line['packaging_quantity'] = line['packaging']._compute_qty(line['quantity'], line['product_uom'])
            return aggregated_move_lines

        # Loops to get backorders, backorders' backorders, and so and so...
        backorders = self.env['stock.picking']
        pickings = self.picking_id
        while pickings.backorder_ids:
            backorders |= pickings.backorder_ids
            pickings = pickings.backorder_ids

        for move_line in self:
            if kwargs.get('except_package') and move_line.result_package_id:
                continue
            line_key, name, description, uom, packaging = get_aggregated_properties(move_line=move_line)
            qty_done = move_line.product_uom_id._compute_quantity(move_line.quantity, uom)
            if line_key not in aggregated_move_lines:
                qty_ordered = None
                if backorders and not kwargs.get('strict'):
                    qty_ordered = move_line.move_id.product_uom_qty
                    # Filters on the aggregation key (product, description and uom) to add the
                    # quantities delayed to backorders to retrieve the original ordered qty.
                    following_move_lines = backorders.move_line_ids.filtered(
                        lambda ml: get_aggregated_properties(move=ml.move_id)[0] == line_key
                    )
                    qty_ordered += sum(following_move_lines.move_id.mapped('product_uom_qty'))
                    # Remove the done quantities of the other move lines of the stock move
                    previous_move_lines = move_line.move_id.move_line_ids.filtered(
                        lambda ml: get_aggregated_properties(move=ml.move_id)[0] == line_key and ml.id != move_line.id
                    )
                    qty_ordered -= sum(map(lambda m: m.product_uom_id._compute_quantity(m.quantity, uom), previous_move_lines))
                aggregated_move_lines[line_key] = {
                    'name': name,
                    'description': description,
                    'quantity': qty_done,
                    'qty_ordered': qty_ordered or qty_done,
                    'product_uom': uom,
                    'product': move_line.product_id,
                    'packaging': packaging,
                    'sh_sec_qty':move_line.move_id.sh_sec_qty,
                    'sh_sec_uom':move_line.move_id.sh_sec_uom.name,
                }
            else:
                aggregated_move_lines[line_key]['qty_ordered'] += qty_done
                aggregated_move_lines[line_key]['quantity'] += qty_done

        # Does the same for empty move line to retrieve the ordered qty. for partially done moves
        # (as they are splitted when the transfer is done and empty moves don't have move lines).
        if kwargs.get('strict'):
            return _compute_packaging_qtys(aggregated_move_lines)
        pickings = (self.picking_id | backorders)
        for empty_move in pickings.move_ids:
            if not (empty_move.state == "cancel" and empty_move.product_uom_qty
                    and float_is_zero(empty_move.quantity, precision_rounding=empty_move.product_uom.rounding)):
                continue
            line_key, name, description, uom, packaging = get_aggregated_properties(move=empty_move)

            if line_key not in aggregated_move_lines:
                qty_ordered = empty_move.product_uom_qty
                aggregated_move_lines[line_key] = {
                    'name': name,
                    'description': description,
                    'quantity': False,
                    'qty_ordered': qty_ordered,
                    'product_uom': uom,
                    'product': empty_move.product_id,
                    'packaging': packaging,
                }
            else:
                aggregated_move_lines[line_key]['qty_ordered'] += empty_move.product_uom_qty

        return _compute_packaging_qtys(aggregated_move_lines)

# class ShStockImmediateTransfer(models.TransientModel):
#     _inherit = 'stock.immediate.transfer'

#     def process(self):
#         res = super(ShStockImmediateTransfer, self).process()
#         for picking_ids in self.pick_ids:
#             for moves in picking_ids.move_ids_without_package:
#                 if moves.sh_sec_uom:
#                     moves.sh_sec_done_qty = moves.product_uom._compute_quantity(
#                         moves.product_uom_qty,
#                         moves.sh_sec_uom
#                     )
#                 for move_lines in moves.move_line_ids:
#                     if move_lines.sh_sec_uom:
#                         move_lines.sh_sec_qty = move_lines.product_uom_id._compute_quantity(
#                             move_lines.qty_done,
#                             moves.sh_sec_uom
#                         )
#         return res
