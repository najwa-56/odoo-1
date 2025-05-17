from odoo import models, fields, api
from datetime import datetime,date


class WeeklyRouts(models.Model):
    _name = 'weekly.routs'
    _description = 'Weekly Routes'
    _rec_name = 'reference' # This makes the reference field be used as display name in the header of the for view near to new button
    _order = 'creation_date desc, id desc'

    reference = fields.Char(string="reference number", copy=False, required=True,default="New", readonly=True)
    creation_date = fields.Date(string="creation date", default=lambda self: fields.Date.today())
    route_lines = fields.One2many('weekly.routs.line', 'weekly_route_id', string="خطوط المسارات") #One record is linked to many records in another model
    user_id = fields.Many2one('res.users',string='User',required=True)
    Starting_date = fields.Date(string="Starting date") # the record should be showun in this date
    Ending_date = fields.Date(string="Ending date")   # the record should be disapear in this date


    #---------------------------------------------------------------------------------------------------------
    # used to generate reference number
    #---------------------------------------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate reference number"""
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code('weekly.routs') or 'New'

        return super(WeeklyRouts, self).create(vals_list)


    #---------------------------------------------------------------------------------------------------------
    #we create this field with computed method to filter the content based on today
    #filter the content of route_lines () based  on day = today and display the conter to salesman screen
    #---------------------------------------------------------------------------------------------------------
    today_route_lines = fields.One2many('weekly.routs.line',compute='_compute_today_route_lines',string="Today's Routes",store=False,)
    @api.depends('route_lines.day','route_lines')
    def _compute_today_route_lines(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.today_route_lines = rec.route_lines.filtered(lambda line: line.day == today)

