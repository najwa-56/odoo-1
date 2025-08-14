from odoo import models, fields, api, _
from datetime import datetime,date
from collections import defaultdict
from odoo.exceptions import UserError


class DailyVisit( models.Model ):
    _name = 'daily.visit'
    _description = 'Daily Visit'
    _order = 'creation_date desc'
    _rec_name = 'reference'


    #----------------------------------------------------------
    #adjustment
    #----------------------------------------------------------
    adjustment_ids = fields.One2many('visit.partner.adjustment', 'visit_id', string="Partner Adjustments")
    amount_due = fields.Float(string="Amount To Collect", compute='_compute_amount_due', store=True)

    @api.depends('adjustment_ids.state', 'adjustment_ids.amount_total')
    def _compute_amount_due(self):
        for rec in self:
            rec.amount_due = sum(rec.adjustment_ids.mapped('amount_total'))


    def _build_partner_adjustment(self):
        """Create a new adjustment (state=draft) and fill its lines."""
        adjustment = self.env['visit.partner.adjustment'].create({
            'visit_id': self.id,
            'state': 'draft',
        })
        self._build_partner_adjustment_lines(adjustment)
        return adjustment

    def _build_partner_adjustment_lines(self, adjustment):
        self.ensure_one()
        partner = self.partner_id
        StockMove = self.env['stock.move']
        StockPicking = self.env['stock.picking']

        # Clear any previous draft lines first
        adjustment.line_ids.unlink()
      

        # ---- gather data ---------------------------------------------------
        pickings = self.env['stock.picking'].search([
            ('partner_id', '=', partner.id),
            ('picking_type_id.code', '=', 'outgoing'),
            ('state', '=', 'done'),
        ],order='date_done desc', limit=1)
        pdata = defaultdict(lambda: {
            'product_id': False,
            'delivered_qty': 0.0,
            'returned_qty': 0.0,
            'counted_qty': 0.0,
            'price_unit': 0.0,
        })

        StockMove = self.env['stock.move']
        for picking in pickings:
            for move in picking.move_ids:
                prod_id = move.product_id.id
                rec = pdata[prod_id]
                rec['product_id'] = prod_id
                rec['delivered_qty'] += move.quantity
                rec['price_unit'] = (
                    (move.sale_line_id.price_unit) / (move.sale_line_id.product_uom.ratio)
                    if move.sale_line_id else move.product_id.list_price
                )

                rec['uom_id'] = move.sale_line_id.product_uom and move.sale_line_id.product_uom.id or False

                rtn_qty = sum(StockMove.search([
                    ('origin_returned_move_id', '=', move.id),
                    ('state', '=', 'done')
                ]).mapped('quantity'))
                rec['returned_qty'] += rtn_qty

      

        prev_adjustment = self.env['visit.partner.adjustment'].search([
            ('visit_id.partner_id', '=', self.partner_id.id),
            ('state', '=', 'confirmed'),
        ], order='create_date desc', limit=1)


        last_counted_map = {
            line.product_id.id: line.total_counted_qty
            for line in prev_adjustment.line_ids
        } if prev_adjustment else {}

        line_cmds = []
        for vals in pdata.values():
            vals['last_counted_qty'] = last_counted_map.get(vals['product_id'], 0.0)
            line_cmds.append((0, 0, vals))

        adjustment.write({'line_ids': line_cmds})

        return adjustment


    def action_open_partner_adjustment(self):
       
        self.ensure_one()
        if not (self.partner_id and self.partner_id.is_later):
            raise UserError("Partner is not marked as Pay Later.")

        Adjustment = self.env['visit.partner.adjustment']

        adjustment = Adjustment.search([
            ('visit_id', '=', self.id),
           
        ], limit=1)

        if adjustment:
            self._build_partner_adjustment_lines(adjustment)
        else:
            adjustment = self._build_partner_adjustment() 

        return {
            'type': 'ir.actions.act_window',
            'name': 'Partner Adjustment',
            'res_model': 'visit.partner.adjustment',
            'view_mode': 'form',
            'res_id': adjustment.id,
            'target': 'current',
        }


    def action_open_adjustmen(self):
        return {
            'name': 'Partner Adjustments',
            'type': 'ir.actions.act_window',
            'res_model': 'visit.partner.adjustment',
           'view_mode': 'list,form',
            'domain': [('visit_id', '=', self.id),
                       ],
            'views': [[False, "list"], [False, "kanban"], [False, "form"]],
                'view_mode': 'list, kanban, form',
        }





    reference = fields.Char( string='reference number', copy=False, required=True, default='New', readonly=True )
    created_by = fields.Many2one( 'res.users', string='Created By', default=lambda self: self.env.user, readonly=True )
    creation_date = fields.Datetime( string='Creation Date', default=fields.Datetime.now, readonly=True )
    partner_id = fields.Many2one( 'res.partner', string='customer' )
    is_it_sold = fields.Boolean( string='is it sold' )
    reason_ifNotSold = fields.Char( string='reason' )
    attachment_ifNotSold = fields.Binary( string='picture' )
    order_id = fields.Many2many( comodel_name='sale.order', string="order number", ondelete='cascade', index=True,
                                 copy=False )
    attachment_before = fields.Binary( string='picture before' )
    attachment_after = fields.Binary( string='picture after' )
    start_time = fields.Datetime( string='Start Time', readonly=True )
    end_time = fields.Datetime( string='End Time', readonly=True )
    check_out_time = fields.Datetime(string='Check out Time', readonly=True)
    status = fields.Selection( [('new', 'New'),('', '')], string="Status", default='new' )  #used for daily.realtime.report

    #used to link weekly.routs reference to daily.visit
    weekly_route_id = fields.Many2one('weekly.routs',string='Weekly Route' ,)
    # ref = fields.Char(string="reference number WK", copy=False, required=False,default="New", readonly=True)
    is_later = fields.Boolean(related='partner_id.is_later')

    #----------------------------------------------------------
    #visit status
    #----------------------------------------------------------
    decision_state = fields.Selection( [
        ('accept', 'قبول'),
        ('reject', 'رفض '),
    ], string="حالة قرار", default=False )

    def action_accept_sale (self):
        for rec in self:
            rec.is_it_sold = True
            rec.decision_state = 'accept'

    def action_reject_sale (self):
        for rec in self:
            rec.is_it_sold = False
            rec.decision_state = 'reject'
    #----------------------------------------------------------
    #for capture check out time
    #----------------------------------------------------------
    def action_check_out (self):
        for record in self:
            now = fields.Datetime.now()
            record.check_out_time = now
            record.end_time = now  # Set end_time when user checks out

    # -------------------------------------------------------------------
    # sale order creation action , pass customer name and visit reference
    # -------------------------------------------------------------------
    '''
    def action_create_sale_order (self):
        self.ensure_one()
        # ✅ Check if customer status is 'waiting' or 'rejected'
        if self.partner_id.status_contact in ['waiting', 'rejected']:
            raise UserError('This customer needs to be approved by the accountant.')

        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Sale Order',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.partner_id.id if self.partner_id else False,
                'default_visit_id': self.id,
            }
        }'''

    def action_create_sale_order (self):
        self.ensure_one()

        # # you cant sale if the customer status waiting or rejected
        #if self.partner_id.status_contact in ['waiting', 'rejected']:
        #    raise UserError( _( 'You cannot create a sale order. This customer must be approved by the accountant.' ) )

        adjustment = self.env['visit.partner.adjustment'].search( [
            ('visit_id', '=', self.id),
            ('state', '=', 'confirmed')
        ], limit=1 )

        previous_orders = self.env['sale.order'].search_count( [
            ('partner_id', '=', self.partner_id.id),
            ('state', 'in', ['sale', 'done'])
        ], limit=1 )

        # # you cant sale the salesman doesn't create adjustment and this not the first time visit
        # # which means he can skip adjustment if this is the first time visit to this customer
        if self.partner_id.status_contact in ['accepted']:
          if not adjustment and previous_orders  :
              raise UserError( _( "You cannot create a sale order. No adjustment is linked to this visit." ) )

        # # you cant sale if there is computed_difference
          if adjustment.computed_difference != 0:
              raise UserError( _( "You cannot create a sale order. Customer balance is not cleared (difference ≠ 0)." ) )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Sale Order',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_visit_id': self.id,
            }
        }




    # -------------------------------------------------------------------
    # show sale orders related to specific visit
    # -------------------------------------------------------------------
    def action_view_related_sale_orders (self):
        return {
            'name': 'Related Sale Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'domain': [('visit_id', '=', self.id)],
            'views': [[False, 'list'], [False, 'kanban'], [False, 'form']],
            'view_mode': 'list,kanban,form',
        }

    #----------------------------------------------------------
    #for display today orders
    #----------------------------------------------------------
    @api.model
    def _get_today (self):
        return date.today()

    today_date = fields.Date( default=_get_today )


    #----------------------------------------------------------
    # capture the starting time when the form is initialized and the ending time when the form is saved.
    # and also creatce refrence number
    # and link visit to partner
    #----------------------------------------------------------
    @api.model_create_multi
    def create (self, vals_list):
        for vals in vals_list:
            # Generate reference number if not present
            if vals.get( 'reference', 'New' ) == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code( 'daily.visit' ) or 'New'

            # Set the end time for the visit

            vals['start_time'] = datetime.now()
            vals['end_time'] = vals.get('check_out_time')

        # Create the visit record
        visits = super( DailyVisit, self ).create( vals_list )

        for visit in visits:
            # Link the visit to the partner's Many2many field
            if visit.partner_id:
                visit.partner_id.visit = [(4, visit.id)]  # Add the visit to the M2M field

            # Update the status from the visit
            if visit.partner_id:
                visit.partner_id._update_status_from_visit( visit.is_it_sold )

        
        

        return visits
    


    #----------------------------------------------------------
    #The custom write method ensures that whenever a DailyVisit record is updated,
    # the status of the associated res.partner (partner) is also updated
    # based on the is_it_sold field of the visit.
    #----------------------------------------------------------
    def write (self, vals):
        res = super().write( vals )
        for visit in self:
            if visit.partner_id:
                visit.partner_id._update_status_from_visit( visit.is_it_sold )
        return res




