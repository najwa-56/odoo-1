from odoo import models, fields, api, _
from datetime import datetime,date

class DailyVisit( models.Model ):
    _name = 'daily.visit'
    _description = 'Daily Visit'
    _order = 'creation_date desc'
    _rec_name = 'reference'

    reference = fields.Char( string='الرقم المرجعي', copy=False, required=True, default='New', readonly=True )
    created_by = fields.Many2one( 'res.users', string='Created By', default=lambda self: self.env.user, readonly=True )
    creation_date = fields.Datetime( string='Creation Date', default=fields.Datetime.now, readonly=True )
    partner_id = fields.Many2one( 'res.partner', string='العميل' )
    is_it_sold = fields.Boolean( string='هل تم البيع' )
    reason_ifNotSold = fields.Char( string='السبب' )
    attachment_ifNotSold = fields.Binary( string='صورة' )
    order_id = fields.Many2many( comodel_name='sale.order', string="رقم الطلب", ondelete='cascade', index=True,
                                 copy=False )
    attachment_before = fields.Binary( string='صورة قبل' )
    attachment_after = fields.Binary( string='صورة بعد' )
    start_time = fields.Datetime( string='Start Time', readonly=True )
    end_time = fields.Datetime( string='End Time', readonly=True )

    # for display today orders
    @api.model
    def _get_today (self):
        return date.today()

    today_date = fields.Date( default=_get_today )



    #----------------------------------
    #calculate total_consumption_amount for all SO per customer
    #----------------------------------
    total_consumption_amount = fields.Float(
        string='المبلغ المستحق',
        compute='_compute_total_consumption_amount',
        store=False
    )

    @api.depends( 'partner_id' )
    def _compute_total_consumption_amount (self):
        for visit in self:
            if visit.partner_id:
                sale_orders = self.env['sale.order'].search( [('partner_id', '=', visit.partner_id.id)] )
                total_consumption = sum( s.total_consumption_amount_perSO for s in sale_orders )
                payments = self.env['account.payment'].search( [
                    ('partner_id', '=', visit.partner_id.id),
                    ('state', '=', 'posted'),
                    ('payment_type', '=', 'inbound')
                ] )
                total_paid = sum( p.amount for p in payments )
                visit.total_consumption_amount = total_consumption - total_paid
            else:
                visit.total_consumption_amount = 0.0




    #capture the starting time when the form is initialized and the ending time when the form is saved.
    #and also creatce refrence number
    #and link visit to partner
    @api.model_create_multi
    def create (self, vals_list):
        for vals in vals_list:
            # Generate reference number if not present
            if vals.get( 'reference', 'New' ) == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code( 'daily.visit' ) or 'New'

            # Set the end time for the visit
            vals['end_time'] = datetime.now()

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

    #The custom write method ensures that whenever a DailyVisit record is updated,
    # the status of the associated res.partner (partner) is also updated
    # based on the is_it_sold field of the visit.
    def write (self, vals):
        res = super().write( vals )
        for visit in self:
            if visit.partner_id:
                visit.partner_id._update_status_from_visit( visit.is_it_sold )
        return res


    #test
    weekly_route_id = fields.Many2one(
        'weekly.routs',
        string='Weekly Route',
        domain="[('user_id', '=', uid)]"
    )
    ref = fields.Char(string="الرقم المرجعي", copy=False, required=True,default="New", readonly=True)



