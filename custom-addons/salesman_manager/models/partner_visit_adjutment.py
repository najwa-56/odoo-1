from odoo import models, fields, api, _
from odoo.exceptions import UserError , ValidationError
class VisitPartnerAdjustment(models.Model):
    _name = 'visit.partner.adjustment'
    _description = 'Partner Adjustment'
    _order = 'create_date desc'

    visit_id = fields.Many2one('daily.visit', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', related='visit_id.partner_id', store=True)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], default='draft')

    line_ids = fields.One2many('visit.partner.adjustment.line', 'adjustment_id', string="Adjustment Lines")
    amount_total = fields.Float(compute='_compute_total', store=True)
    computed_difference = fields.Float(string="Adjustment - Payments",compute='_compute_difference',store=False,)

    @api.depends('line_ids.total')
    def _compute_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('total'))
    #-------------------------------------------------------------------------------------
    #(sum all amount_total's) - (sum all amount in account.payment model)
    #-------------------------------------------------------------------------------------
    @api.depends( 'partner_id' )
    def _compute_difference (self):
        for rec in self:
            if not rec.partner_id:
                rec.computed_difference = 0.0
                continue

            total_adjustments = sum(
                self.env['visit.partner.adjustment'].search( [
                    ('state', '=', 'confirmed'),
                    ('partner_id', '=', rec.partner_id.id)
                ] ).mapped( 'amount_total' )
            )

            total_payments = sum(
                self.env['account.payment'].search( [
                    ('state', '=', 'posted'),
                    ('partner_id', '=', rec.partner_id.id)
                ] ).mapped( 'amount' )
            )

            rec.computed_difference = total_adjustments - total_payments

    def action_confirm(self):
        self.write({'state':'confirmed'})

    #-------------------------------------------------------------------------------------
    #inside adjusment , user click on action_create_payment button to payment registration
    #-------------------------------------------------------------------------------------

    payment_id = fields.Many2one('account.payment', string='customer payment')

    def action_create_payment (self):
        self.ensure_one()

        if not self.partner_id:
            raise UserError( "Partner must be set to create a payment." )
        if self.amount_total <= 0:
            raise UserError( "Amount must be greater than zero." )
        if self.payment_id:
            raise UserError( "Payment already exists for this record." )

        # Get payment method and journal
        journal = self.env['account.journal'].search( [
            ('type', '=', 'bank'),
            ('company_id', '=', self.env.company.id)
        ], limit=1 )
        if not journal:
            raise UserError( "No bank journal found for the current company." )


        payment_method_line = journal.inbound_payment_method_line_ids[:1]
        if not payment_method_line:
            raise ValidationError( _( "No inbound payment method found on the selected journal." ) )

        # Create payment
        payment_vals = {
            'partner_id': self.partner_id.id,
            'amount': self.amount_total,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'payment_method_line_id': payment_method_line.id,
            'journal_id': journal.id,
        }

        payment = self.env['account.payment'].create( payment_vals )
        payment.action_post()

        # Link to current record
        self.payment_id = payment.id

        # Return payment receipt report
        return {
            'type': 'ir.actions.report',
            'report_name': 'account.report_payment_receipt',
            'report_type': 'qweb-pdf',
            'res_id': payment.id,
            'context': {'active_model': 'account.payment', 'active_ids': [payment.id]},

        }




class VisitPartnerAdjustmentLine(models.Model):
    _name = 'visit.partner.adjustment.line'
    _description = 'Adjustment Line'

    adjustment_id = fields.Many2one('visit.partner.adjustment', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', required=True)
    delivered_qty = fields.Float()
    returned_qty = fields.Float()

    counted_qty = fields.Float() # شدات
    counted_qty_by_uom = fields.Float() #حبات

    uom_id = fields.Many2one('uom.uom', string='Uom')
    last_counted_qty = fields.Float()
    total_counted_qty = fields.Float(compute='_compute_total_counted', store=True)

    sold_qty = fields.Float(compute='_compute_sold', store=True)
    price_unit = fields.Float()
    total = fields.Float(compute='_compute_total', store=True)

    @api.depends('delivered_qty', 'returned_qty', 'total_counted_qty','last_counted_qty')
    def _compute_sold(self):
        for rec in self:
            rec.sold_qty = ((rec.delivered_qty - rec.returned_qty) + rec.last_counted_qty) - rec.total_counted_qty

    '''@api.depends('sold_qty', 'price_unit')
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.sold_qty) * rec.price_unit'''

    @api.depends( 'sold_qty', 'product_id', 'uom_id' )
    def _compute_total (self):
        for rec in self:
            price = 0.0
            if rec.product_id and rec.uom_id:
                price_record = self.env['product.multi.uom.price'].search( [
                    ('product_id', '=', rec.product_id.product_tmpl_id.id),
                    ('uom_id', '=', rec.uom_id.id)
                ], limit=1 )
                price = price_record.price if price_record else 0.0

            rec.price_unit = price/rec.uom_id.ratio
            rec.total = rec.sold_qty * rec.price_unit

    @api.depends('counted_qty', 'counted_qty_by_uom','uom_id')
    def _compute_total_counted(self):
        for rec in self:
            rec.total_counted_qty = (rec.counted_qty * rec.uom_id.ratio) + rec.counted_qty_by_uom


