# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    sh_planned_table = fields.Integer(default=10,string="Planned Activities Table Limit")
    sh_all_table = fields.Integer(default=10,string="All Activities Table Limit")
    sh_completed_table = fields.Integer(default=10,string="Complated Activities Table Limit")
    sh_due_table = fields.Integer(default=10,string="Overdue Activities Table Limit")
    sh_cancel_table = fields.Integer(default=10,string="Cancelled Activities Table Limit")
    sh_display_multi_user = fields.Boolean(string="Display Multi User")
    sh_display_all_activities_counter = fields.Boolean(default=True,string="Display All Activities Counter")
    sh_display_planned_activities_counter = fields.Boolean(default=True,string="Display Planned Activities Counter")
    sh_display_completed_activities_counter = fields.Boolean(default=True,string="Display Completed Activities Counter")
    sh_display_overdue_activities_counter = fields.Boolean(default=True,string="Display Overude Activities Counter")
    sh_display_cancelled_activities_counter = fields.Boolean(default=True,string="Display Cancelled Activities Counter")
    sh_display_all_activities_table = fields.Boolean(default=True,string="Display All Activities Table")
    sh_display_planned_activities_table = fields.Boolean(default=True,string="Display Planned Activities Table")
    sh_display_completed_activities_table = fields.Boolean(default=True,string="Display Completed Activities Table")
    sh_display_overdue_activities_table = fields.Boolean(default=True,string="Display Overdue Activities Table")
    sh_display_cancelled_activities_table = fields.Boolean(default=True,string="Display Cancelled Activities Table")
    sh_display_activity_reminder = fields.Boolean(default=True,string="Activity Reminder")
    sh_document_model = fields.Boolean(string="Display document model wise activity?")
    sh_document_model_ids = fields.Many2many('ir.model',string="Document Models ")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sh_planned_table = fields.Integer(related='company_id.sh_planned_table',readonly=False,string="Planned Activities Table Limit")
    sh_all_table = fields.Integer(related='company_id.sh_all_table',readonly=False,string="All Activities Table Limit")
    sh_completed_table = fields.Integer(related='company_id.sh_completed_table',readonly=False,string="Complated Activities Table Limit")
    sh_due_table = fields.Integer(related='company_id.sh_due_table',readonly=False,string="Overdue Activities Table Limit")
    sh_cancel_table = fields.Integer(related='company_id.sh_cancel_table',readonly=False,string="Cancelled Activities Table Limit")
    sh_display_multi_user = fields.Boolean(related='company_id.sh_display_multi_user',readonly=False,string="Display Multi User")
    sh_display_all_activities_counter = fields.Boolean(related='company_id.sh_display_all_activities_counter',readonly=False,string="Display All Activities Counter")
    sh_display_planned_activities_counter = fields.Boolean(related='company_id.sh_display_planned_activities_counter',readonly=False,string="Display Planned Activities Counter")
    sh_display_completed_activities_counter = fields.Boolean(related='company_id.sh_display_completed_activities_counter',readonly=False,string="Display Completed Activities Counter")
    sh_display_overdue_activities_counter = fields.Boolean(related='company_id.sh_display_overdue_activities_counter',readonly=False,string="Display Overude Activities Counter")
    sh_display_cancelled_activities_counter = fields.Boolean(related='company_id.sh_display_cancelled_activities_counter',readonly=False,string="Display Cancelled Activities Counter")
    sh_display_all_activities_table = fields.Boolean(related='company_id.sh_display_all_activities_table',readonly=False,string="Display All Activities Table")
    sh_display_planned_activities_table = fields.Boolean(related='company_id.sh_display_planned_activities_table',readonly=False,string="Display Planned Activities Table")
    sh_display_completed_activities_table = fields.Boolean(related='company_id.sh_display_completed_activities_table',readonly=False,string="Display Completed Activities Table")
    sh_display_overdue_activities_table = fields.Boolean(related='company_id.sh_display_overdue_activities_table',readonly=False,string="Display Overdue Activities Table")
    sh_display_cancelled_activities_table = fields.Boolean(related='company_id.sh_display_cancelled_activities_table',readonly=False,string="Display Cancelled Activities Table")
    sh_display_activity_reminder = fields.Boolean(related='company_id.sh_display_activity_reminder',readonly=False,string="Activity Reminder")
    sh_document_model = fields.Boolean(related='company_id.sh_document_model',readonly=False,string="Display document model wise activity?")
    sh_document_model_ids = fields.Many2many('ir.model',related='company_id.sh_document_model_ids',readonly=False,string="Document Models")

    @api.onchange('sh_document_model')
    def onchange_sh_document_model(self):
        if self.sh_document_model:
            models = self.env['ir.model'].sudo().search([('state', '!=', 'manual')])
            document_models = []
            for model in models:
                if not model.model.startswith('ir.'):
                    document_models.append(model.id)
            return {'domain': {'sh_document_model_ids': [('id', 'in', document_models)]}}
        else:
            self.sh_document_model_ids = False

    def action_update_activity_data(self):
        activities = self.env['mail.activity'].sudo().search([('active','!=',False),('activity_cancel','=',False),('activity_done','=',False)])
        if activities:
            for activity in activities:
                activity.active = True
                activity.onchange_state()
