from collections import Counter
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare, float_is_zero


class KsStockMoveLine(models.Model):
    _name = "multicompany.transfer.move.line"
    _description = "Product Moves (Stock Move Line)"
    _rec_name = "ks_product_id"

    ks_transfer_id = fields.Many2one(
        'multicompany.transfer.stock', 'Stock Transfer', auto_join=True,
        check_company=True,
        index=True,
        help='The stock operation where the packing has been made')
    ks_move_id = fields.Many2one('multicompany.transfer.stock.line', 'Stock Move', check_company=True,
                              help="Change to a better name", index=True)
    ks_company_id = fields.Many2one('res.company', string='Company', readonly=True, index=True)
    ks_product_id = fields.Many2one('product.product', 'Product', ondelete="cascade", check_company=True, domain="[('type', '!=', 'service'), '|', ('ks_company_id', '=', False), ('ks_company_id', '=', ks_company_id)]")
    ks_product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    ks_product_qty = fields.Float('Real Reserved Quantity', compute='ks_compute_product_qty', store=True)
    ks_product_uom_qty = fields.Float('Reserved', default=0.0, required=True)
    ks_qty_done = fields.Float('Done', default=0.0, copy=False)
    ks_lot_id = fields.Many2one('stock.lot', 'Lot/Serial Number', domain="[('product_id', '=', ks_product_id),('company_id', '=', ks_company_id)]")
    ks_location_id = fields.Many2one('stock.location', 'Source Location')
    ks_location_dest_id = fields.Many2one('stock.location', 'Destination Location')

    @api.depends('ks_product_id', 'ks_product_uom_id', 'ks_product_uom_qty')
    def ks_compute_product_qty(self):
        for ks_line in self:
            ks_line.ks_product_qty = ks_line.ks_product_uom_id._compute_quantity(ks_line.ks_product_uom_qty, ks_line.ks_product_id.uom_id,
                                                                     rounding_method='HALF-UP')

    @api.onchange('ks_product_id', 'ks_product_uom_id')
    def ks_onchange_product_id(self):
        if self.ks_product_id:
            if not self.ks_product_uom_id or self.ks_product_uom_id.category_id != self.ks_product_id.uom_id.category_id:
                if self.ks_move_id.ks_product_uom_type:
                    self.ks_product_uom_id = self.ks_move_id.ks_product_uom_type.id
                else:
                    self.ks_product_uom_id = self.ks_product_id.uom_id.id
            res = {'domain': {'ks_product_uom_id': [('category_id', '=', self.ks_product_uom_id.category_id.id)]}}
        else:
            res = {'domain': {'ks_product_uom_id': []}}
        return res

    @api.onchange('ks_lot_id')
    def ks_onchange_lot_serial_number(self):
        res = {}
        if self.ks_product_id.tracking == 'serial':
            if not self.ks_qty_done:
                self.ks_qty_done = 1
            if self.ks_lot_id:
                ks_move_lines_to_check = self.ks_get_similar_move_lines()
                if self.ks_lot_id:
                    counter = Counter([line.ks_lot_id.id for line in ks_move_lines_to_check])
                    if counter.get(self.ks_lot_id.id) and counter[self.ks_lot_id.id] > 1:
                        self.ks_lot_id = False
                        raise ValidationError(_('You cannot use the same serial number twice. '
                                    'Please Use different serial numbers.'))
                    if self.ks_product_id.tracking == 'serial':
                        if len(ks_move_lines_to_check.filtered(lambda move: move.ks_lot_id.id == self.ks_lot_id.id and move.ks_location_id.id != False))>1:
                            self.ks_lot_id = False
                            raise ValidationError(_('You cannot use the same serial number twice. '
                                        'Please Use different serial numbers.'))
        return res

    @api.onchange('ks_qty_done')
    def ks_onchange_qty_done(self):
        res = {}
        if self.ks_qty_done and self.ks_product_id.tracking == 'serial':
            if float_compare(self.ks_qty_done, 1.0, precision_rounding=self.ks_product_id.uom_id.rounding) != 0:
                raise ValidationError(_(
                    'You can only process 1.0 %s of products with unique serial number.' % self.ks_product_id.uom_id.name))
        return res

    @api.constrains('ks_qty_done')
    def _check_positive_qty_done(self):
        if any([ks_move_line.ks_qty_done < 0 for ks_move_line in self]):
            raise ValidationError(_('You can not enter negative quantities.'))

    def _reservation_is_updatable(self, quantity, reserved_quant):
        self.ensure_one()
        if (self.ks_product_id.tracking != 'serial' and
                self.ks_location_id.id == reserved_quant.location_id.id and
                self.ks_lot_id.id == reserved_quant.lot_id.id):
            return True
        return False

    def ks_get_similar_move_lines(self):
        self.ensure_one()
        lines = self.env['multicompany.transfer.move.line']
        ks_transfer_id = self.ks_move_id
        if ks_transfer_id:
            lines |= ks_transfer_id.ks_move_line_ids.filtered(lambda ks_move_line: ks_move_line.ks_product_id == self.ks_product_id and (ks_move_line.ks_lot_id))
        return lines

    @api.model
    def create(self, vals_list):
        if vals_list:
            if vals_list.get('ks_move_id'):
                move_record = self.env['multicompany.transfer.stock.line'].browse(vals_list['ks_move_id'])
                if move_record.exists():
                    if not vals_list.get('ks_location_id', False):
                        vals_list['ks_location_id'] = move_record.ks_location_id.id if move_record.ks_location_id else False
                    vals_list['ks_company_id'] = move_record.ks_company_id.id if move_record.ks_location_id.company_id else False
                    vals_list['ks_product_id'] = move_record.ks_product_id.id if move_record.ks_product_id else False
                    vals_list['ks_product_uom_id'] = move_record.ks_product_uom_type.id if move_record.ks_product_uom_type else False
                    vals_list['ks_transfer_id'] = move_record.ks_multicompany_transfer_id.id if move_record.ks_multicompany_transfer_id else False
                    vals_list['ks_location_dest_id'] = move_record.ks_location_dest_id.id if move_record.ks_location_dest_id else False
        ks_move_lines = super(KsStockMoveLine, self).create(vals_list)
        return ks_move_lines

    def _should_bypass_reservation(self, location):
        self.ensure_one()
        if location:
            return location.should_bypass_reservation() or self.ks_product_id.type != 'product'

    def unlink(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for ks_move_line in self:
            # Unlinking a move line should unreserve.
            if ks_move_line.ks_product_id.type == 'product' and not ks_move_line._should_bypass_reservation(ks_move_line.ks_location_id) and not float_is_zero(ks_move_line.ks_product_qty, precision_digits=precision):
                try:
                    self.env['stock.quant']._update_reserved_quantity(ks_move_line.ks_product_id, ks_move_line.ks_location_id, -ks_move_line.ks_product_qty, lot_id=ks_move_line.ks_lot_id, strict=True)
                except UserError:
                    if ks_move_line.ks_lot_id:
                        self.env['stock.quant']._update_reserved_quantity(ks_move_line.ks_product_id, ks_move_line.ks_location_id, -ks_move_line.ks_product_qty, lot_id=False, strict=True)
                    else:
                        raise
        res = super(KsStockMoveLine, self).unlink()
        return res

