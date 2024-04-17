# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, modules, exceptions, _,Command
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import clean_context
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import html2plaintext
import math
from odoo.osv import expression
from collections import defaultdict
from odoo.http import request
import json
import logging
import uuid
from odoo.tools import SQL
import pytz

from odoo.exceptions import ValidationError, UserError
_logger = logging.getLogger('odoo.addons.base.partner.merge')


class MailActivityMixin(models.AbstractModel):
    _inherit = 'mail.activity.mixin'

    def _read_group_groupby(self, groupby_spec, query):
        if groupby_spec != 'activity_state':
            return super()._read_group_groupby(groupby_spec, query)

        self.env['mail.activity'].flush_model(['res_model', 'res_id', 'user_id', 'date_deadline'])        

        tz = 'UTC'
        if self.env.context.get('tz') in pytz.all_timezones_set:
            tz = self.env.context['tz']

        sql_join = SQL(
            """
            (SELECT res_id,
                CASE
                    WHEN min(date_deadline - (now() AT TIME ZONE COALESCE(res_partner.tz, %(tz)s))::date) > 0 THEN 'planned'
                    WHEN min(date_deadline - (now() AT TIME ZONE COALESCE(res_partner.tz, %(tz)s))::date) < 0 THEN 'overdue'
                    WHEN min(date_deadline - (now() AT TIME ZONE COALESCE(res_partner.tz, %(tz)s))::date) = 0 THEN 'today'
                    ELSE null
                END AS activity_state
            FROM mail_activity
            JOIN res_users ON (res_users.id = mail_activity.user_id)
            JOIN res_partner ON (res_partner.id = res_users.partner_id)
            WHERE res_model = %(res_model)s and mail_activity.active = True
            GROUP BY res_id)
            """,
            res_model=self._name,
            tz=tz,
        )
        alias = query.join(self._table, "id", sql_join, "res_id", "last_activity_state")

        return SQL.identifier(alias, 'activity_state'), ['activity_state']



class MailActivity(models.Model):
    """ Inherited Mail Acitvity to add custom field"""   
    _name = 'mail.activity'
    _inherit = ['portal.mixin','mail.activity']


    # portal.mixin override
    def _compute_access_url(self):
        super()._compute_access_url()
        for order in self:
            order.access_url = f'/my/activities/{order.id}'

    def _default_access_token(self):
        return uuid.uuid4().hex

    @api.model
    def default_company_id(self):
        return self.env.company

    active = fields.Boolean(default=True)
    supervisor_id = fields.Many2one('res.users', string="Supervisor",domain=[('share','=',False)])
    sh_activity_tags = fields.Many2many(
        "sh.activity.tags", string='Activity Tags')
    state = fields.Selection(
        selection_add=[("done", "Done"),("cancel","Cancelled")],
        search = '_search_state'
    )
    sh_state = fields.Selection([('overdue','Overdue'),('today','Today'),('planned','Planned'),('done','Done'),('cancel','Cancelled')])
    date_done = fields.Date("Completed Date", index=True, readonly=True)
    feedback = fields.Text("Feedback")

    text_note = fields.Char("Notes In Char format ",
                            compute='_compute_html_to_char_note')
    sh_user_ids = fields.Many2many('res.users', string="Assign Multi Users",domain=[('share','=',False)])
    sh_display_multi_user = fields.Boolean(
        compute='_compute_sh_display_multi_user')
    company_id = fields.Many2one(
        'res.company', string='Company', default=default_company_id)
    color = fields.Integer('Color Index', default=0)
    sh_create_individual_activity = fields.Boolean(
        'Individual activities for multi users ?')
    sh_activity_alarm_ids = fields.Many2many('sh.activity.alarm',string = 'Reminders')
    sh_date_deadline = fields.Datetime('Reminder Due Date', default=lambda self: fields.Datetime.now())
    activity_cancel = fields.Boolean()
    activity_done = fields.Boolean()
    sh_activity_id = fields.Many2one("sh.recurring.activities", ondelete="cascade")
    reference = fields.Reference(string='Related Document',
        selection='_reference_models')

    @api.model
    def _reference_models(self):
        all_dic = {}            
        models_list = []    
        models = request.env['ir.model'].sudo().search([('state', '!=', 'manual')])  
        if models:
            for model_id in models:
                if model_id.state != 'manual':
                    field_id = request.env['ir.model.fields'].sudo().search([('name','=','activity_ids'),('model_id','=',model_id.id),('store','=',True)])
                    if field_id:
                        models_list.append(model_id.id)
        models = request.env['ir.model'].sudo().search([('id', 'in',models_list)])         
        return [(model.model, model.name)
                for model in models
                if not model.model.startswith('ir.')]

    @api.onchange('reference')
    def onchange_reference(self):
        if self.reference:
            if self.reference._name:
                model_id = self.env['ir.model'].sudo().search([('model','=',self.reference._name)],limit=1)
                if model_id:
                    self.res_model_id = model_id.id
                    self.res_id = self.reference.id
                    self.res_model = self.reference._name

    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for activity in self:
            activity.res_name = ''
            if activity.res_model and activity.res_id:
                activity.res_name = self.env[activity.res_model].browse(activity.res_id).name_get()[0][1]

    @api.onchange('state')
    def onchange_state(self):
        self.ensure_one()
        self.activity_done = False
        self.activity_cancel = False
        self._compute_state()

    @api.depends('date_deadline')
    def _compute_state(self):
        super(MailActivity, self)._compute_state()
        for record in self.filtered(lambda activity: not activity.active):
            if record.activity_cancel:
                record.state = 'cancel'
            if record.activity_done:
                record.state = 'done'
        for activity_record in self.filtered(lambda activity: activity.active):
            activity_record.sh_state = activity_record.state

    def write(self, vals):
        if self:
            for rec in self:
                if vals.get('state'):
                    vals.update({
                        'sh_state':vals.get('state')
                        })
                if vals.get('active') and vals.get('active') == True:
                    rec.onchange_state()
        return super(MailActivity, self).write(vals)


    def _search_state(self,operator,value):
        not_done_ids = []
        done_ids = []
        if value == 'done':
            for record in self.search([('active','=',False),('date_done','!=',False)]):
                done_ids.append(record.id)
        elif value == 'cancel':
            for record in self.search([('active','=',False),('date_done','=',False)]):
                done_ids.append(record.id)
        elif value == 'today':
            for record in self.search([('date_deadline','=',fields.Date.today())]):
                done_ids.append(record.id)
        elif value == 'planned':
            for record in self.search([('date_deadline','>',fields.Date.today())]):
                done_ids.append(record.id)
        elif value == 'overdue':
            for record in self.search([('date_deadline','<',fields.Date.today())]):
                done_ids.append(record.id)
        if operator == '=':
            return [('id', 'in', done_ids)]
        elif operator == 'in':
            return [('id', 'in', done_ids)]
        elif operator == '!=':
            return [('id', 'in', not_done_ids)]
        elif operator == 'not in':
            return [('id', 'in', not_done_ids)]
        else:
            return []

    @api.onchange('date_deadline')
    def _onchange_sh_date_deadline(self):
        if self:
            for rec in self:
                if rec.date_deadline:
                    rec.sh_date_deadline = rec.date_deadline + timedelta(hours=0, minutes=0, seconds=0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('res_model_id'):
                model_id = self.env['ir.model'].sudo().search([('id','=',vals.get('res_model_id'))],limit=1)
                if model_id:
                    if 'activity_ids' not in self.env[model_id.model]._fields:
                        raise UserError('You can not create activity for this model due to this model does not have activity field.')
        res_values = super(MailActivity, self).create(vals_list) 
        for res in res_values:         
            if res.sh_user_ids and res.sh_create_individual_activity:
                for user in res.sh_user_ids:
                    if res.user_id.id != user.id:
                        self.env['mail.activity'].sudo().create({
                            'user_id':user.id,
                            'res_model_id': res.res_model_id.id,
                            'res_id': res.res_id,
                            'date_deadline': res.date_deadline,
                            'sh_user_ids': [(6, 0, user.ids)],
                            'supervisor_id': res.supervisor_id.id,
                            'activity_type_id': res.activity_type_id.id,
                            'summary': res.summary,
                            'sh_activity_tags': [(6, 0, res.sh_activity_tags.ids)],
                            'note': res.note,
                        })
            if res.state:
                res.sh_state = res.state
        return res_values
    
    @api.model
    def action_cancel_dashboard(self,activity_id):
        mail_activity_id = self.env['mail.activity'].sudo().browse(int(activity_id))
        if mail_activity_id:
            mail_activity_id.action_cancel()
            if mail_activity_id.state == 'cancel':
                return {'cancelled':True}
        
    def action_cancel(self):
        if self:
            for rec in self:
                rec.state = 'cancel'
                rec.active = False
                rec.date_done = False
                rec.activity_cancel = True
                rec._compute_state()

    @api.model
    def unarchive_dashboard(self,activity_id):
        mail_activity_id = self.env['mail.activity'].sudo().browse(int(activity_id))
        if mail_activity_id:
            mail_activity_id.unarchive()
            return {'unarchive':True}
    
    @api.model
    def action_done_dashboard(self,activity_id,activity_feedback):
        mail_activity_id = self.env['mail.activity'].sudo().browse(int(activity_id))
        if mail_activity_id:
            mail_activity_id.action_feedback(feedback = activity_feedback,attachment_ids=None)
            if mail_activity_id.state == 'done':
                return {'completed':True}

    def unarchive(self,active=True):
        self.ensure_one()
        self.activity_cancel = False
        self.active = True
        self._compute_state()

    @api.depends('company_id')
    def _compute_sh_display_multi_user(self):
        if self:
            for rec in self:
                rec.sh_display_multi_user = False
                if rec.company_id and rec.company_id.sh_display_multi_user:
                    rec.sh_display_multi_user = True

    def _compute_html_to_char_note(self):
        if self:
            for rec in self:
                if rec.note:
                    rec.text_note = html2plaintext(rec.note)
                else:
                    rec.text_note = ''

    @api.model
    def notify_mail_activity_fun(self):

        template = self.env.ref(
            'sh_activities_management.template_mail_activity_due_notify_email')
        notify_create_user_template = self.env.ref(
            'sh_activities_management.template_mail_activity_due_notify_email_create_user')
        company_object = self.env['res.company'].search(
            [('activity_due_notification', '=', True)], limit=1)

        if template and company_object and company_object.activity_due_notification:

            activity_obj = self.env['mail.activity'].search([])

            if activity_obj:
                for record in activity_obj:
                    if record.date_deadline and record.user_id and record.user_id.id != self.env.ref('base.user_root').id and record.user_id.partner_id and record.user_id.partner_id.email:

                        # On Due Date
                        if company_object.ondue_date_notify:

                            if datetime.strptime(str(record.date_deadline), DEFAULT_SERVER_DATE_FORMAT).date() == datetime.now().date():
                                template.send_mail(record.id, force_send=True)
                                if notify_create_user_template and company_object.notify_create_user_due:
                                    if record.user_id.id != record.create_uid.id and record.create_uid.id != self.env.ref('base.user_root').id:
                                        notify_create_user_template.send_mail(
                                            record.id, force_send=True)
                        # On After First Notify
                        if company_object.after_first_notify and company_object.enter_after_first_notify:
                            after_date = datetime.strptime(str(record.date_deadline), DEFAULT_SERVER_DATE_FORMAT).date(
                            ) + timedelta(days=company_object.enter_after_first_notify)

                            if after_date == datetime.now().date():
                                template.send_mail(record.id, force_send=True)
                                if notify_create_user_template and company_object.notify_create_user_after_first:
                                    if record.user_id.id != record.create_uid.id and record.create_uid.id != self.env.ref('base.user_root').id:
                                        notify_create_user_template.send_mail(
                                            record.id, force_send=True)
                        # On After Second Notify
                        if company_object.after_second_notify and company_object.enter_after_second_notify:
                            after_date = datetime.strptime(str(record.date_deadline), DEFAULT_SERVER_DATE_FORMAT).date(
                            ) + timedelta(days=company_object.enter_after_second_notify)

                            if after_date == datetime.now().date():
                                template.send_mail(record.id, force_send=True)
                                if notify_create_user_template and company_object.notify_create_user_after_second:
                                    if record.user_id.id != record.create_uid.id and record.create_uid.id != self.env.ref('base.user_root').id:
                                        notify_create_user_template.send_mail(
                                            record.id, force_send=True)
                        # On Before First Notify
                        if company_object.before_first_notify and company_object.enter_before_first_notify:
                            before_date = datetime.strptime(str(record.date_deadline), DEFAULT_SERVER_DATE_FORMAT).date(
                            ) - timedelta(days=company_object.enter_before_first_notify)

                            if before_date == datetime.now().date():
                                template.send_mail(record.id, force_send=True)
                                if notify_create_user_template and company_object.notify_create_user_before_first:
                                    if record.user_id.id != record.create_uid.id and record.create_uid.id != self.env.ref('base.user_root').id:
                                        notify_create_user_template.send_mail(
                                            record.id, force_send=True)
                        # On Before Second Notify
                        if company_object.before_second_notify and company_object.enter_before_second_notify:
                            before_date = datetime.strptime(str(record.date_deadline), DEFAULT_SERVER_DATE_FORMAT).date(
                            ) - timedelta(days=company_object.enter_before_second_notify)

                            if before_date == datetime.now().date():
                                template.send_mail(record.id, force_send=True)
                                if notify_create_user_template and company_object.notify_create_user_before_second:
                                    if record.user_id.id != record.create_uid.id and record.create_uid.id != self.env.ref('base.user_root').id:
                                        notify_create_user_template.send_mail(
                                            record.id, force_send=True)

    def action_view_activity(self):
        self.ensure_one()
        try:
            self.env[self.res_model].browse(
                self.res_id).check_access_rule('read')
            return{
                'name': 'Origin Activity',
                'res_model': self.res_model,
                'res_id': self.res_id,
                'view_mode': 'form',
                'type': 'ir.actions.act_window',
                'target': 'current',
            }
        except exceptions.AccessError:
            raise exceptions.UserError(
                _('Assigned user %s has no access to the document and is not able to handle this activity.') %
                self.env.user.display_name)

    def action_edit_activity(self):
        self.ensure_one()
        view_id = self.env.ref(
            'sh_activities_management.sh_mail_activity_type_view_form_inherit').id
        return {
            'name': _('Schedule an Activity'),
            'view_mode': 'form',
            'res_model': 'mail.activity',
            'views': [(view_id, 'form')],
            'res_id':self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_done(self):
        """ Wrapper without feedback because web button add context as
        parameter, therefore setting context to feedback """
        return{
            'name': 'Activity Feedback',
            'res_model': 'activity.feedback',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'context': {'default_done_button_pressed': True},
            'target': 'new',
        }

    def action_feedback(self, feedback=False, attachment_ids=None):
        messages, _next_activities = self.with_context(
            clean_context(self.env.context)
        )._action_done(feedback=feedback, attachment_ids=attachment_ids)
        self.state = 'done'
        self.active = False
        self.activity_done = True
        self._compute_state()
        if self.state == 'done':
            self.date_done = fields.Date.today()
        self.feedback = feedback
        # return messages[0].id if messages else False

    def action_done_from_popup(self, feedback=False):
        self.ensure_one()
        self = self.with_context(clean_context(self.env.context))
        messages, next_activities = self._action_done(
            feedback=feedback, attachment_ids=False)
        self.state = 'done'
        self.active = False
        self.activity_done = True
        self._compute_state()
        if self.state == 'done':
            self.date_done = fields.Date.today()
        self.feedback = feedback
#         return messages.ids and messages.ids[0] or False

    def _action_done(self, feedback=False, attachment_ids=None):
        self.ensure_one()
        """ Private implementation of marking activity as done: posting a message, deleting activity
            (since done), and eventually create the automatical next activity (depending on config).
            :param feedback: optional feedback from user when marking activity as done
            :param attachment_ids: list of ir.attachment ids to attach to the posted mail.message
            :returns (messages, activities) where
                - messages is a recordset of posted mail.message
                - activities is a recordset of mail.activity of forced automically created activities
        """
        # marking as 'done'
        messages = self.env['mail.message']
        next_activities_values = []
        next_activities =None
        # Search for all attachments linked to the activities we are about to unlink. This way, we
        # can link them to the message posted and prevent their deletion.
        attachments = self.env['ir.attachment'].search_read([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
        ], ['id', 'res_id'])

        activity_attachments = defaultdict(list)
        for attachment in attachments:
            activity_id = attachment['res_id']
            activity_attachments[activity_id].append(attachment['id'])

        for activity in self:
            # extract value to generate next activities
            if activity.chaining_type == 'trigger':
                Activity = self.env['mail.activity'].with_context(activity_previous_deadline=activity.date_deadline)  # context key is required in the onchange to set deadline
                vals = Activity.default_get(Activity.fields_get())

                vals.update({
                    'previous_activity_type_id': activity.activity_type_id.id,
                    'res_id': activity.res_id,
                    'res_model': activity.res_model,
                    'res_model_id': self.env['ir.model']._get(activity.res_model).id,
                })
                virtual_activity = Activity.new(vals)
                virtual_activity._onchange_previous_activity_type_id()
                virtual_activity._onchange_activity_type_id()
                next_activities_values.append(virtual_activity._convert_to_write(virtual_activity._cache))

            # post message on activity, before deleting it
            record = self.env[activity.res_model].browse(activity.res_id)            
            record.sudo().message_post_with_source(
               'mail.message_activity_done',
                attachment_ids=[],
                render_values={
                    'activity': activity,
                    'feedback': self.feedback,
                    'display_assignee': activity.user_id != self.env.user
                },
                mail_activity_type_id=activity.activity_type_id.id,
                subtype_xmlid='mail.mt_activities',
            )
            # Moving the attachments in the message
            # TODO: Fix void res_id on attachment when you create an activity with an image
            # directly, see route /web_editor/attachment/add
            activity_message = record.message_ids[0]
            message_attachments = self.env['ir.attachment'].browse(activity_attachments[activity.id])
            if message_attachments:
                message_attachments.write({
                    'res_id': activity_message.id,
                    'res_model': activity_message._name,
                })
                activity_message.attachment_ids = message_attachments
            messages |= activity_message
        if next_activities_values:
            next_activities = self.env['mail.activity'].create(next_activities_values)
        self.active = False
        self.date_done = fields.Date.today()
        self.feedback = feedback
        self.state = "done"
        self.activity_done = True
        self._compute_state()
        return messages, next_activities

    def activity_format(self):
        self = self.filtered(lambda r: r.active == True)
        activities = self.read()
        mail_template_ids = set([template_id for activity in activities for template_id in activity["mail_template_ids"]])
        mail_template_info = self.env["mail.template"].browse(mail_template_ids).read(['id', 'name'])
        mail_template_dict = dict([(mail_template['id'], mail_template) for mail_template in mail_template_info])
        for activity in activities:
            activity['mail_template_ids'] = [mail_template_dict[mail_template_id] for mail_template_id in activity['mail_template_ids']]
        return activities



class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def systray_get_activities(self):        
        activities = super(ResUsers, self).systray_get_activities()        
        # query = """SELECT m.id, count(*), act.res_model as model,
        #                 CASE
        #                     WHEN %(today)s::date - act.date_deadline::date = 0 Then 'today'
        #                     WHEN %(today)s::date - act.date_deadline::date > 0 Then 'overdue'
        #                     WHEN %(today)s::date - act.date_deadline::date < 0 Then 'planned'
        #                 END AS states
        #             FROM mail_activity AS act
        #             JOIN ir_model AS m ON act.res_model_id = m.id
        #             WHERE user_id = %(user_id)s  and active=True
        #             GROUP BY m.id, states, act.res_model;
        #             """
        # self.env.cr.execute(query, {
        #     'today': fields.Date.context_today(self),
        #     'user_id': self.env.user.id,
        # })
        # print("\n\\n\n...self.env.uid...",self.env.cr.dictfetchall())    
        # activity_data = self.env.cr.dictfetchall()            
        # model_ids = [a['id'] for a in activity_data]
        # print("\n\\n\n...self.env.uid...",model_ids)
        # model_names = {n[0]: n[1] for n in self.env['ir.model'].sudo().browse(model_ids).name_get()}
        # print("\n\\n\n...self.env.uid...",model_names)
        # user_activities = {}
        # for activity in activity_data:
        #     if not user_activities.get(activity['model']):
        #         module = self.env[activity['model']]._original_module
        #         icon = module and modules.module.get_module_icon(module)
        #         user_activities[activity['model']] = {
        #             'id': activity['id'],
        #             'name': model_names[activity['id']],
        #             'model': activity['model'],
        #             'type': 'activity',
        #             'icon': icon,
        #             'total_count': 0, 'today_count': 0, 'overdue_count': 0, 'planned_count': 0,
        #         }
        #     user_activities[activity['model']]['%s_count' % activity['states']] += activity['count']
        #     if activity['states'] in ('today', 'overdue'):
        #         user_activities[activity['model']]['total_count'] += activity['count']

        #     user_activities[activity['model']]['actions'] = [{
        #         'icon': 'fa-clock-o',
        #         'name': 'Summary',
        #     }]
        # activities = list(user_activities.values())
        # if self.env['ir.module.module'].sudo().search([('name','=','note'),('state','=','installed')]):
        #     notes_count = self.env['note.note'].search_count([('user_id', '=', self.env.uid)])
        #     if notes_count:
        #         note_index = next((index for (index, a) in enumerate(activities) if a["model"] == "note.note"), None)
        #         note_label = _('Notes')
        #         if note_index is not None:
        #             activities[note_index]['name'] = note_label
        #         else:
        #             activities.append({
        #                 'type': 'activity',
        #                 'name': note_label,
        #                 'model': 'note.note',
        #                 'icon': modules.module.get_module_icon(self.env['note.note']._original_module),
        #                 'total_count': 0,
        #                 'today_count': 0,
        #                 'overdue_count': 0,
        #                 'planned_count': 0
        #             })
        # for activity in activities:
        #     if self.env['ir.module.module'].sudo().search([('name','=','contacts'),('state','=','installed')]):
        #         if activity['model'] == 'res.partner':
        #             activity['icon'] = '/sh_activities_management/static/description/contacts_icon.png'
        #     if self.env['ir.module.module'].sudo().search([('name','=','mass_mailing'),('state','=','installed')]):
        #         if activity.get('model') == 'mailing.mailing':
        #             activity['name'] = _('Email Marketing')
        #             break
        #     if self.env['ir.module.module'].sudo().search([('name','=','mass_mailing_sms'),('state','=','installed')]):
        #         if activity.get('model') == 'mailing.mailing':
        #             activities.remove(activity)
        #             query = """SELECT m.mailing_type, count(*), act.res_model as model, act.res_id,
        #                         CASE
        #                             WHEN %(today)s::date - act.date_deadline::date = 0 Then 'today'
        #                             WHEN %(today)s::date - act.date_deadline::date > 0 Then 'overdue'
        #                             WHEN %(today)s::date - act.date_deadline::date < 0 Then 'planned'
        #                         END AS states
        #                     FROM mail_activity AS act
        #                     JOIN mailing_mailing AS m ON act.res_id = m.id
        #                     WHERE act.res_model = 'mailing.mailing' AND act.user_id = %(user_id)s  
        #                     GROUP BY m.mailing_type, states, act.res_model, act.res_id;
        #                     """
        #             self.env.cr.execute(query, {
        #                 'today': fields.Date.context_today(self),
        #                 'user_id': self.env.uid,
        #             })
        #             activity_data = self.env.cr.dictfetchall()
            
        #             user_activities = {}
        #             for act in activity_data:
        #                 if not user_activities.get(act['mailing_type']):
        #                     if act['mailing_type'] == 'sms':
        #                         module = 'mass_mailing_sms'
        #                         name = _('SMS Marketing')
        #                     else:
        #                         module = 'mass_mailing'
        #                         name = _('Email Marketing')
        #                     icon = module and modules.module.get_module_icon(module)
        #                     res_ids = set()
        #                     user_activities[act['mailing_type']] = {
        #                         'name': name,
        #                         'model': 'mailing.mailing',
        #                         'type': 'activity',
        #                         'icon': icon,
        #                         'total_count': 0, 'today_count': 0, 'overdue_count': 0, 'planned_count': 0,
        #                         'res_ids': res_ids,
        #                     }
        #                 user_activities[act['mailing_type']]['res_ids'].add(act['res_id'])
        #                 user_activities[act['mailing_type']]['%s_count' % act['states']] += act['count']
        #                 if act['states'] in ('today', 'overdue'):
        #                     user_activities[act['mailing_type']]['total_count'] += act['count']
            
        #             for mailing_type in user_activities.keys():
        #                 user_activities[mailing_type].update({
        #                     'actions': [{'icon': 'fa-clock-o', 'name': 'Summary',}],
        #                     'domain': json.dumps([['activity_ids.res_id', 'in', list(user_activities[mailing_type]['res_ids'])]])
        #                 })
        #             activities.extend(list(user_activities.values()))
        #             break
        # if self.env['ir.module.module'].sudo().search([('name','=','calendar'),('state','=','installed')]):
        #     meetings_lines = self.env['calendar.event'].search_read(
        #     self._systray_get_calendar_event_domain(),
        #     ['id', 'start', 'name', 'allday', 'attendee_status'],
        #     order='start')
        #     meetings_lines = [line for line in meetings_lines if line['attendee_status'] != 'declined']
        #     if meetings_lines:
        #         meeting_label = _("Today's Meetings")
        #         meetings_systray = {
        #             'type': 'meeting',
        #             'name': meeting_label,
        #             'model': 'calendar.event',
        #             'icon': modules.module.get_module_icon(self.env['calendar.event']._original_module),
        #             'meetings': meetings_lines,
        #         }
                
        #         activities.insert(0, meetings_systray)
        return activities

class MergePartnerAutomaticCustom(models.TransientModel):
    _inherit='base.partner.merge.automatic.wizard'


    def _merge(self, partner_ids, dst_partner=None, extra_checks=True):
            """ private implementation of merge partner
                :param partner_ids : ids of partner to merge
                :param dst_partner : record of destination res.partner
                :param extra_checks: pass False to bypass extra sanity check (e.g. email address)
            """
            # super-admin can be used to bypass extra checks
            if self.env.is_admin():
                extra_checks = False

            Partner = self.env['res.partner']
            partner_ids = Partner.browse(partner_ids).exists()
            if len(partner_ids) < 2:
                return

            if len(partner_ids) > 3:
                raise UserError(_("For safety reasons, you cannot merge more than 3 contacts together. You can re-open the wizard several times if needed."))

            # check if the list of partners to merge contains child/parent relation
            child_ids = self.env['res.partner']
            for partner_id in partner_ids:
                child_ids |= Partner.search([('id', 'child_of', [partner_id.id])]) - partner_id
            if partner_ids & child_ids:
                raise UserError(_("You cannot merge a contact with one of his parent."))

            if extra_checks and len(set(partner.email for partner in partner_ids)) > 1:
                raise UserError(_("All contacts must have the same email. Only the Administrator can merge contacts with different emails."))

            # remove dst_partner from partners to merge
            if dst_partner and dst_partner in partner_ids:
                src_partners = partner_ids - dst_partner
            else:
                ordered_partners = self._get_ordered_partner(partner_ids.ids)
                dst_partner = ordered_partners[-1]
                src_partners = ordered_partners[:-1]
            _logger.info("dst_partner: %s", dst_partner.id)

            # FIXME: is it still required to make and exception for account.move.line since accounting v9.0 ?
            if extra_checks and 'account.move.line' in self.env and self.env['account.move.line'].sudo().search([('partner_id', 'in', [partner.id for partner in src_partners])]):
                raise UserError(_("Only the destination contact may be linked to existing Journal Items. Please ask the Administrator if you need to merge several contacts linked to existing Journal Items."))

            # Make the company of all related users consistent with destination partner company
            if dst_partner.company_id:
                partner_ids.mapped('user_ids').sudo().write({
                    'company_ids': [Command.link(dst_partner.company_id.id)],
                    'company_id': dst_partner.company_id.id
                })

            #--------------------------------
            #CUSTOM CHANGES 
            #--------------------------------
           
            if dst_partner.activity_ids:
                for activity in dst_partner.activity_ids:
                    activity.res_id = dst_partner.id
            if src_partners.activity_ids:
                for activity in src_partners.activity_ids:
                    activity.res_id = dst_partner.id


            # call sub methods to do the merge
            self._update_foreign_keys(src_partners, dst_partner)
            # self._update_reference_fields(src_partners, dst_partner)
            self._update_values(src_partners, dst_partner)

            self._log_merge_operation(src_partners, dst_partner)

            # delete source partner, since they are merged
            src_partners.unlink()