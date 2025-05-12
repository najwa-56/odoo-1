# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, models, _

class SHMailActivitySchedule(models.TransientModel):
    _inherit = 'mail.activity.schedule'
    
    @api.model
    def default_company_id(self):
        return self.env.company
    
    supervisor_id = fields.Many2one('res.users', string="Supervisor",domain=[('share','=',False)])
    sh_activity_tags = fields.Many2many(
        "sh.activity.tags", string='Activity Tags')
    sh_activity_alarm_ids = fields.Many2many('sh.activity.alarm',string = 'Reminders')
    
    company_id = fields.Many2one(
        'res.company', string='Company', default=default_company_id)
    
    sh_display_multi_user = fields.Boolean(
        compute='_compute_sh_display_multi_user')
    sh_user_ids = fields.Many2many('res.users', string="Assign Multi Users",domain=[('share','=',False)])
    sh_create_individual_activity = fields.Boolean(
        'Individual activities for multi users ?')
    sh_date_deadline = fields.Datetime('Reminder Due Date', default=lambda self: fields.Datetime.now())
    
    
    @api.depends('company_id')
    def _compute_sh_display_multi_user(self):
        if self:
            for rec in self:
                rec.sh_display_multi_user = False
                if rec.company_id and rec.company_id.sh_display_multi_user:
                    rec.sh_display_multi_user = True
                    
    def _action_schedule_activities(self):
        result = super()._action_schedule_activities()
        result.update({'company_id':self.company_id,
                       'sh_user_ids':self.sh_user_ids,
                       'sh_activity_alarm_ids':self.sh_activity_alarm_ids,
                       'sh_activity_tags':self.sh_activity_tags,
                       'sh_display_multi_user':self.sh_display_multi_user,
                       'supervisor_id':self.supervisor_id,
                       'sh_create_individual_activity':self.sh_create_individual_activity,
                       })
        return result