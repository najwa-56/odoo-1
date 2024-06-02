from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError, UserError
from collections import defaultdict


class KsStockTransferMultiCompanyLines(models.Model):
    _name = 'multicompany.transfer.stock.line'
    _description = "Multi Company Inventory Transfer"

    ks_product_id = fields.Many2one('product.product', string="Product", required=True)
    ks_tracking = fields.Selection(related='ks_product_id.tracking', readonly=True, copy=False)
    ks_multicompany_transfer_id = fields.Many2one('multicompany.transfer.stock')
    state = fields.Selection(related='ks_multicompany_transfer_id.state', readonly=True, copy=False)
    ks_qty_available = fields.Float('Qty available', compute="ks_get_location_quantity")
    ks_qty_transfer = fields.Float('Qty to Transfer', required=True)
    ks_product_uom_type = fields.Many2one('uom.uom', string='Unit of measurement', related='ks_product_id.uom_id',
                                          required=True, store=True)
    ks_quantity_done = fields.Float('Qty Done', compute='ks_quantity_done_compute',
                                    inverse='ks_quantity_done_set', readonly=True)
    ks_reserved_availability = fields.Float('Qty Reserved', compute='ks_compute_reserved_availability',
                                            readonly=True, help='Quantity that has already been reserved for this move')
    ks_location_id = fields.Many2one('stock.location', 'Source Location', related='ks_multicompany_transfer_id.ks_transfer_from_location')

    ks_location_dest_id = fields.Many2one('stock.location', 'Destination Location', related='ks_multicompany_transfer_id.ks_transfer_to_location')
    ks_move_line_ids = fields.One2many('multicompany.transfer.move.line', 'ks_move_id')

    ks_company_id = fields.Many2one('res.company', related='ks_multicompany_transfer_id.ks_transfer_from')

    @api.depends('ks_product_id', 'ks_multicompany_transfer_id.ks_transfer_from_location')
    def ks_get_location_quantity(self):
        for rec in self:
            rec.ks_qty_available = 0
            if rec.ks_multicompany_transfer_id.ks_transfer_from_location and rec.ks_product_id:
                rec.ks_qty_available = rec.env['stock.quant']._get_available_quantity(rec.ks_product_id,
                                                                                      rec.ks_multicompany_transfer_id.ks_transfer_from_location)

    def ks_quantity_done_set(self):
        quantity_done = self[0].ks_quantity_done  # any call to create will invalidate `move.quantity_done`
        for move in self:
            move_lines = move.ks_get_move_lines()
            if not move_lines:
                if quantity_done:
                    move_line = self.env['multicompany.transfer.move.line'].create(
                        dict(move.ks_prepare_move_line_vals(), ks_qty_done=quantity_done))
                    move.write({'move_line_ids': [(4, move_line.id)]})
            elif len(move_lines) == 1:
                move_lines[0].ks_qty_done = quantity_done
            else:
                raise UserError(
                    _("Cannot set the done quantity from this stock move, work directly with the move lines."))

    @api.depends('ks_move_line_ids.ks_product_qty')
    def ks_compute_reserved_availability(self):

        result = {data['ks_move_id'][0]: data['ks_product_qty'] for data in
                  self.env['multicompany.transfer.move.line'].read_group(
                      [('ks_move_id', 'in', self.ids)],
                      ['ks_move_id', 'ks_product_qty'],
                      ['ks_move_id'])}
        for rec in self:
            rec.ks_reserved_availability = rec.ks_product_id.uom_id._compute_quantity(result.get(rec.id, 0.0),
                                                                                   rec.ks_product_uom_type,
                                                                                   rounding_method='HALF-UP')

    @api.depends('ks_move_line_ids.ks_qty_done', 'ks_move_line_ids.ks_product_uom_id')
    def ks_quantity_done_compute(self):
        move_lines = self.env['multicompany.transfer.move.line']
        for move in self:
            move_lines |= move.ks_get_move_lines()

        data = self.env['multicompany.transfer.move.line'].read_group(
            [('id', 'in', move_lines.ids)],
            ['ks_move_id', 'ks_product_uom_id', 'ks_qty_done'], ['ks_move_id', 'ks_product_uom_id'],
            lazy=False
        )

        rec = defaultdict(list)
        for d in data:
            rec[d['ks_move_id'][0]] += [(d['ks_product_uom_id'][0], d['ks_qty_done'])]

        for move in self:
            uom = move.ks_product_uom_type
            move.ks_quantity_done = sum(
                self.env['uom.uom'].browse(line_uom_id)._compute_quantity(qty, uom, round=False)
                for line_uom_id, qty in rec.get(move.ids[0] if move.ids else move.id, [])
            )
            if move.ks_product_id.tracking == 'none':
                move.ks_quantity_done = move.ks_reserved_availability

    def ks_action_assign(self):
        assigned_moves = self.env['multicompany.transfer.stock.line']
        partially_available_moves = self.env['multicompany.transfer.stock.line']

        ks_reserved_availability = {move: move.ks_reserved_availability for move in self}
        roundings = {move: move.ks_product_id.uom_id.rounding for move in self}
        move_line_vals_list = []
        for move in self:
            rounding = roundings[move]
            missing_reserved_uom_quantity = move.ks_qty_transfer - ks_reserved_availability[move]
            missing_reserved_quantity = move.ks_product_uom_type._compute_quantity(missing_reserved_uom_quantity,
                                                                                   move.ks_product_id.uom_id,
                                                                                   rounding_method='HALF-UP')
            if move._should_bypass_reservation():
                # create the move line(s) but do not impact quants
                if move.ks_product_id.tracking == 'serial':
                    for i in range(0, int(missing_reserved_quantity)):
                        move_line_vals_list.append(move.ks_prepare_move_line_vals(quantity=1))
                else:
                    to_update = move.ks_move_line_ids.filtered(lambda move_line: move_line.ks_product_uom_id == move.product_uom and
                                                                       move_line.ks_transfer_id == move.ks_multicompany_transfer_id and
                                                                       not move_line.ks_lot_id )
                    if to_update:
                        to_update[0].ks_product_uom_qty += missing_reserved_uom_quantity
                    else:
                        move_line_vals_list.append(move.ks_prepare_move_line_vals(quantity=missing_reserved_quantity))
                assigned_moves |= move
            else:
                if float_is_zero(move.ks_qty_transfer, precision_rounding=move.ks_product_uom_type.rounding):
                    assigned_moves |= move
                else:
                    need = missing_reserved_quantity
                    if float_is_zero(need, precision_rounding=rounding):
                        assigned_moves |= move
                        continue
                    # Reserve new quants and create move lines accordingly.
                    forced_package_id = None
                    available_quantity = self.env['stock.quant']._get_available_quantity(move.ks_product_id,
                                                                                         move.ks_location_id,
                                                                                         package_id=forced_package_id)
                    if available_quantity <= 0:
                        continue
                    taken_quantity = move._update_reserved_quantity(need, available_quantity, move.ks_location_id,
                                                                    package_id=forced_package_id, strict=False)
                    if float_is_zero(taken_quantity, precision_rounding=rounding):
                        continue
                    if float_compare(need, taken_quantity, precision_rounding=rounding) == 0:
                        assigned_moves |= move
                    else:
                        partially_available_moves |= move
        if not move_line_vals_list:
            move_lines = self.env['multicompany.transfer.move.line'].search([('ks_move_id', 'in', self.ids)])
        else:
            move_lines = self.env['multicompany.transfer.move.line'].create(move_line_vals_list)
        if move_lines:
            return True
        else:
            False

    def _should_bypass_reservation(self):
        self.ensure_one()
        return self.ks_multicompany_transfer_id.ks_transfer_from_location.should_bypass_reservation() or self.ks_product_id.type != 'product'

    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        self.ensure_one()

        if not lot_id:
            lot_id = self.env['stock.lot']
        if not package_id:
            package_id = self.env['stock.quant.package']
        if not owner_id:
            owner_id = self.env['res.partner']

        taken_quantity = min(available_quantity, need)

        if not strict:
            taken_quantity_move_uom = self.ks_product_id.uom_id._compute_quantity(taken_quantity, self.ks_product_uom_type, rounding_method='DOWN')
            taken_quantity = self.ks_product_uom_type._compute_quantity(taken_quantity_move_uom, self.ks_product_id.uom_id, rounding_method='HALF-UP')

        quants = []

        if self.ks_product_id.tracking == 'serial':
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(taken_quantity, int(taken_quantity), precision_digits=rounding) != 0:
                taken_quantity = 0

        try:
            if not float_is_zero(taken_quantity, precision_rounding=self.ks_product_id.uom_id.rounding):
                quants = self.env['stock.quant']._get_reserve_quantity(
                    self.ks_product_id, location_id, taken_quantity, lot_id=lot_id,
                    package_id=package_id, owner_id=owner_id, strict=strict
                )
                if self.ks_tracking == 'lot' or self.ks_tracking == 'serial':
                    quantity_reserve = self.env['stock.quant']._gather(self.ks_product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                                          strict=strict)
                    for rec in quantity_reserve:
                        rec.reserved_quantity = need
                        break

        except UserError:
            taken_quantity = 0

        # Find a candidate move line to update or create a new one.
        for reserved_quant, quantity in quants:
            reserved_quant._update_reserved_quantity(reserved_quant.product_id, location_id, quantity=quantity,
                                                     lot_id=None)
            to_update = self.ks_move_line_ids.filtered(lambda move_line: move_line._reservation_is_updatable(quantity, reserved_quant))
            if to_update:
                to_update[0].with_context(bypass_reservation_update=True).ks_product_uom_qty += self.ks_product_id.uom_id._compute_quantity(quantity, to_update[0].ks_product_uom_id, rounding_method='HALF-UP')
            else:
                if self.ks_product_id.tracking == 'serial':
                    for i in range(0, int(quantity)):
                        self.env['multicompany.transfer.move.line'].create(self.ks_prepare_move_line_vals(quantity=1, reserved_quant=reserved_quant))
                else:
                    self.env['multicompany.transfer.move.line'].create(self.ks_prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant))

        return taken_quantity

    def ks_prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        self.ensure_one()
        vals = {
            'ks_move_id': self.id,
            'ks_product_id': self.ks_product_id.id,
            'ks_product_uom_id': self.ks_product_uom_type.id,
            'ks_transfer_id': self.ks_multicompany_transfer_id.id,
        }
        if quantity:
            uom_quantity = self.ks_product_id.uom_id._compute_quantity(quantity, self.ks_product_uom_type,
                                                                       rounding_method='HALF-UP')
            uom_quantity_back_to_product_uom = self.ks_product_uom_type._compute_quantity(uom_quantity,
                                                                                          self.ks_product_id.uom_id,
                                                                                          rounding_method='HALF-UP')
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(quantity, uom_quantity_back_to_product_uom, precision_digits=rounding) == 0:
                vals = dict(vals, ks_product_uom_qty=uom_quantity)
            else:
                vals = dict(vals, ks_product_uom_qty=quantity, ks_product_uom_id=self.ks_product_id.uom_id.id)
        if reserved_quant:
            vals = dict(
                vals,
                ks_location_id=reserved_quant.location_id.id,
                ks_lot_id=reserved_quant.lot_id.id or False,
            )
        return vals

    def ks_do_unreserve_lines(self):
        moves_to_unreserve = self.env['multicompany.transfer.stock.line']
        for move in self:
            if move.ks_multicompany_transfer_id:
                if move.ks_multicompany_transfer_id.state == 'posted':
                    raise UserError(_('You cannot unreserve a stock tranfer that has been set to \'posted\'.'))
                moves_to_unreserve |= move
        moves_to_unreserve.with_context(prefetch_fields=False).mapped('ks_move_line_ids').unlink()
        return True

    def ks_action_show_move_line_details(self):

        self.ensure_one()
        view = self.env.ref('ks_multi_company_inventory_transfer.ks_view_stock_move_line_details')
        return {
            'name': _('Detailed Operations'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'multicompany.transfer.stock.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context),
        }

    def ks_get_move_lines(self):
        self.ensure_one()
        return self.ks_move_line_ids

    def ks_merge_same_move_lines(self, move, stock_line):
        ks_moves_to_merge = []
        ks_moves_to_remove = self.env['multicompany.transfer.stock.line']
        for ks_move in move:
            moves = stock_line.filtered(lambda m: m.ks_product_id.id == ks_move.ks_product_id.id)
            if len(moves) > 1:
                ks_moves_to_merge.append(moves)
        for ks_move_line in ks_moves_to_merge:
            qty = sum([move.ks_qty_transfer for move in ks_move_line])
            ks_move_line[0].write({'ks_qty_transfer': qty})
            ks_moves_to_remove |= ks_move_line[1:]
        if ks_moves_to_remove:
            ks_moves_to_remove.sudo().unlink()
        return (self | self.env['multicompany.transfer.stock.line'].concat(*ks_moves_to_merge)) - ks_moves_to_remove
