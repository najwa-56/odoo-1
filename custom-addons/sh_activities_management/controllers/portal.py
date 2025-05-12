# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from collections import OrderedDict
from dateutil.relativedelta import relativedelta
from operator import itemgetter
from odoo import fields, http, _
from odoo.http import request
from odoo.tools import date_utils, groupby as groupbyelem
from odoo.osv.expression import AND
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import json
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from odoo.addons.portal.controllers.mail import PortalChatter
import base64
from odoo import exceptions

from dateutil.parser import parse


from collections import namedtuple
import math
DummyAttendance = namedtuple(
    'DummyAttendance', 'hour_from, hour_to, dayofweek, day_period, week_type')


class ShActivityPortal(CustomerPortal):

    def _prepare_home_portal_values(self,counters):       
        values = super()._prepare_home_portal_values(counters)        
        activity_obj = request.env['mail.activity']
        activity_data = activity_obj.sudo().search(
            [('user_id', '=', request.env.user.id)])
        activity_count = activity_obj.sudo().search_count(
            [('user_id', '=', request.env.user.id)])
        values['activity_count'] = activity_count
        # values['activities'] = activity_data
        model_obj = request.env['ir.model'].sudo().search_read([], [
            'name', 'id'])
        # values['model_obj'] = model_obj
        if not activity_count:
            activity_count = '0'
            values['activity_count'] = activity_count
        else:
            values['activity_count'] = activity_count   

        return values

    @http.route(['/my/activities', '/my/activities/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_activities(self, page=1, sortby=None, filterby=None, search=None, search_in='all', groupby=None, **kw):
        Activity_sudo = request.env['mail.activity'].sudo()
        values = self._prepare_portal_layout_values()
        rec_user_id = request.env['mail.activity'].sudo().search(
            [('user_id', '=', request.env.user.id)], limit=1)        
        searchbar_sortings = {           
            'date': {'label': _('Newest'), 'order': 'date_deadline desc', 'sequence': 1},
            'name': {'label': _('Name'), 'order': 'res_name', 'sequence': 2},           
        }
     
        searchbar_inputs = {
            'all': {'input': 'all', 'label': _('Search in All')},
            'name': {'input': 'res_name', 'label': _('Search in Name')},        
        }

        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'activity_type': {'input': 'activity_type', 'label': _('Type')},
            'user': {'input': 'user', 'label': _('Assigned to')},
        }

        today = fields.Date.today()
        quarter_start, quarter_end = date_utils.get_quarter(today)
        last_week = today + relativedelta(weeks=-1)
        last_month = today + relativedelta(months=-1)
        last_year = today + relativedelta(years=-1)

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'today': {'label': _('Today'), 'domain': [("date_deadline", "=", today)]},
            'week': {'label': _('This week'), 'domain': [('date_deadline', '>=', date_utils.start_of(today, "week")), ('date_deadline', '<=', date_utils.end_of(today, 'week'))]},
            'month': {'label': _('This month'), 'domain': [('date_deadline', '>=', date_utils.start_of(today, 'month')), ('date_deadline', '<=', date_utils.end_of(today, 'month'))]},
            'year': {'label': _('This year'), 'domain': [('date_deadline', '>=', date_utils.start_of(today, 'year')), ('date_deadline', '<=', date_utils.end_of(today, 'year'))]},
            'quarter': {'label': _('This Quarter'), 'domain': [('date_deadline', '>=', quarter_start), ('date_deadline', '<=', quarter_end)]},
            'last_week': {'label': _('Last week'), 'domain': [('date_deadline', '>=', date_utils.start_of(last_week, "week")), ('date_deadline', '<=', date_utils.end_of(last_week, 'week'))]},
            'last_month': {'label': _('Last month'), 'domain': [('date_deadline', '>=', date_utils.start_of(last_month, 'month')), ('date_deadline', '<=', date_utils.end_of(last_month, 'month'))]},
            'last_year': {'label': _('Last year'), 'domain': [('date_deadline', '>=', date_utils.start_of(last_year, 'year')), ('date_deadline', '<=', date_utils.end_of(last_year, 'year'))]},
        }        
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        if not filterby:
            filterby = 'all'
        domain = AND([searchbar_filters[filterby]['domain']])
        
        if search and search_in:
            domain = AND([domain, [('res_name', 'ilike', search)]])
        domain = AND([domain, [('user_id', '=', rec_user_id.user_id.id)]])
        # domain = []

        if not groupby:
            groupby = 'none'
        
        activity_count = Activity_sudo.search_count(domain)
        
        # pager
        pager = portal_pager(
            url="/my/activities",
            url_args={'sortby': sortby, 'search_in': search_in,
                      'search': search, 'filterby': filterby, 'groupby': groupby},
            total=activity_count,
            page=page,
            step=self._items_per_page
        )
       
        activity = Activity_sudo.search(
            domain, order=order, limit=self._items_per_page, offset=pager['offset'])       
        groupby_mapping = {}
        groupby_mapping.update(
            {
                'activity_type': 'activity_type_id',
                'user': 'user_id',
                # 'country': 'country_id',
            }
        )

        group = groupby_mapping.get(groupby)
        if group:
            grouped_activity = [Activity_sudo.concat(
                *g) for k, g in groupbyelem(activity, itemgetter(group))]

        else:
            grouped_activity = [activity]
            grouped_activity[0] = grouped_activity[0].sorted(
                lambda activity: activity)
        
        values.update({
            'activities': activity,
            'grouped_activity': grouped_activity,
            'page_name': 'sh_activity',
            'default_url': '/my/activities',
            'activity_count': activity_count,
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'search_in': search_in,
            'sortby': sortby,
            'groupby': groupby,

            'searchbar_inputs': searchbar_inputs,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })      
        return request.render("sh_activities_management.portal_my_activities", values)

    @http.route('/my/activities/<int:activity_id>', type='http', auth="public", website=True)
    def portal_my_activity_form(self, activity_id, **kw):
        Activity_sudo = request.env['mail.activity'].sudo().search(
            [('user_id', '=', request.env.user.id), ('id', '=', activity_id)], limit=1)

        model_obj = request.env['ir.model'].sudo().search_read([], [
            'name', 'id'])

        values = {
            'sh_activity': Activity_sudo,
            'model_obj': model_obj,
            'current_res_id': Activity_sudo.res_id
        }

        return request.render('sh_activities_management.portal_activity_form_template', values)

    @http.route('/done-activity', type='http', auth="public", methods=["POST"], website=True, csrf=False)
    def done_activity(self, **post):        
        dic = {}
        if post.get('feedback'):
            activity_id = request.env['mail.activity'].sudo().search(
                [('id', '=', int(post.get('id')))], limit=1)
            if activity_id:
                obj = activity_id._action_done(
                    feedback=post.get('feedback'), attachment_ids=False)
                if obj:
                    dic.update({
                        'success': 'Done'
                    })
        else:
            dic.update({
                'error': 'FeedBack is required'
            })
        return json.dumps(dic)

    @http.route('/relt_document_onchange', type='json', auth="user",csrf=False)
    def relt_document_onchange(self,**kw):        
        Model = request.env['ir.model'].sudo().search(
            [('id', '=',kw['search_id'])]).exists() if kw['search_id'] else False
        all_dic = {}
        if Model:          
            record = request.env[Model.model].sudo().search([])        
            if record:
                for rec in record:                  
                    all_dic.update({str(rec.id) + 'rec_id': rec[rec._rec_name]})

        return json.dumps(all_dic)

    @http.route('/get_relateddocumentdata', type='json', auth="user",csrf=False)
    def get_relateddocumentdata(self, **kw):       
        all_dic = {}            
        models_list = []    
        models = request.env['ir.model'].sudo().search([('state', '!=', 'manual')])  
        if models:
            for model_id in models:
                if model_id.state != 'manual':
                    field_id = request.env['ir.model.fields'].sudo().search([('name','=','activity_ids'),('model_id','=',model_id.id),('store','=',True)])
                    if field_id:
                        models_list.append(model_id.id)
        record = request.env['ir.model'].sudo().search([('id', 'in',models_list)]) 
        if record:
            for rec in record:
                if not rec.model.startswith('ir.'):
                    all_dic.update({str(rec.id): rec.name})                       
        return json.dumps(all_dic)

    @http.route('/create_activity_next', type='http', auth="public", methods=["POST"], website=True, csrf=False)
    def create_next_activity(self,**kw):        
        vals={}
        dic={}
        if kw.get('due_date'):
            vals.update({
                'date_deadline':  datetime.strptime(kw.get('due_date'), DEFAULT_SERVER_DATE_FORMAT).date(),
            })
            if kw.get('duedatereminder'):
                vals.update({
                    'sh_date_deadline':  datetime.strptime(kw.get('due_date'), DEFAULT_SERVER_DATE_FORMAT),
                })
            if kw.get('link_activity_type_id'):
                vals.update({
                    'activity_type_id': int(kw.get('link_activity_type_id')),
                })
            if kw.get('assigned_to'):
                vals.update({
                    'user_id': int(kw.get('assigned_to')),
                })
            if kw.get('supervisor'):
                vals.update({
                    'supervisor_id': int(kw.get('supervisor')),
                })
            if kw.get('summary'):
                vals.update({
                    'summary': kw.get('summary'),
                })
            if kw.get('activity_tags'):
                vals.update({
                    'sh_activity_tags': kw.get('activity_tags'),
                })
            if kw.get('reminders'):
                vals.update({
                    'sh_activity_alarm_ids': kw.get('reminders'),
                })
            if kw.get('user_ids'):
                vals.update({
                    'sh_user_ids': kw.get('user_ids'),
                })                              
            if kw.get('rel_doc_name'):
                vals.update({
                    'res_model_id': int(kw.get('rel_doc_name')),
                })
            if kw.get('doc_name') and kw.get('relt_doc_data'):
                res_model = request.env['ir.model'].sudo().search([('id','=',int(kw.get('rel_doc_name')))])
                vals.update({
                    'res_name': kw.get('doc_name'),
                    'res_id': int(kw.get('relt_doc_data').replace("rec_id","")),
                    'reference':  '%s,%s' % (res_model.model, kw.get('relt_doc_data').replace("rec_id","")),                
                })           
        if vals:
            update_at = request.env['mail.activity'].sudo().create(vals)            
            if update_at:
                dic.update({
                    'success': 'success',
                })
            else:
                dic.update({
                    'error': 'error',
                })
        return json.dumps(dic)

    @http.route('/create_activity', type='json', auth="public", methods=["POST"], website=True, csrf=False)
    def create_activity(self,**kw):        
        vals={}
        dic={}
        if kw.get('due_date'):
            vals.update({
                'date_deadline':  datetime.strptime(kw.get('due_date'), DEFAULT_SERVER_DATE_FORMAT).date(),
            })
            if kw.get('duedatereminder'):
                vals.update({
                    'sh_date_deadline':  datetime.strptime(kw.get('due_date'), DEFAULT_SERVER_DATE_FORMAT),
                })
            if kw.get('link_activity_type_id'):
                vals.update({
                    'activity_type_id': int(kw.get('link_activity_type_id')),
                })
            if kw.get('assigned_to'):
                vals.update({
                    'user_id': int(kw.get('assigned_to')),
                })
            if kw.get('supervisor'):
                vals.update({
                    'supervisor_id': int(kw.get('supervisor')),
                })
            if kw.get('summary'):
                vals.update({
                    'summary': kw.get('summary'),
                })
            if kw.get('activity_tags'):
                vals.update({
                    'sh_activity_tags': kw.get('activity_tags'),
                })
            if kw.get('reminders'):
                vals.update({
                    'sh_activity_alarm_ids': kw.get('reminders'),
                })
            if kw.get('user_ids'):
                user_ids=[]
                for rec in kw.get('user_ids'):
                    user_ids.append(int(rec))
                vals.update({
                    'sh_user_ids':user_ids,
                })                              
            if kw.get('rel_doc_name'):
                vals.update({
                    'res_model_id': int(kw.get('rel_doc_name')),                   
                })
            if kw.get('doc_name') and kw.get('relt_doc_data'):
                res_model = request.env['ir.model'].sudo().search([('id','=',int(kw.get('rel_doc_name')))])
                vals.update({
                    'res_name': kw.get('doc_name'),
                    'res_id': int(kw.get('relt_doc_data').replace("rec_id","")),
                    'reference':  '%s,%s' % (res_model.model, kw.get('relt_doc_data').replace("rec_id","")),                
                })          
        if vals:
            res_model = request.env['ir.model'].sudo().search([('id','=',int(kw.get('rel_doc_name')))])                
            target_records = request.env[res_model.model].browse(vals['res_id'])
            user = request.env['res.users'].sudo().browse(int(kw.get('assigned_to')))
            if user.partner_id:
                check_follow =True
                if target_records.sudo().message_follower_ids:
                    for follower in target_records.sudo().message_follower_ids:
                        if follower.partner_id ==  user.partner_id:
                            check_follow = False
                if check_follow:                                  
                    dic.update({
                        'create_error':'Assigned user '+ user.display_name +' has no access to the document and is not able to handle this activity.'                        
                    })
                # raise exceptions.UserError(
                #     _('Assigned user %s has no access to the document and is not able to handle this activity.',
                #         request.env.user.display_name))
            if not 'create_error' in dic:
                update_at = request.env['mail.activity'].sudo().create(vals)           
                if update_at:
                    dic.update({
                        'success': "Activity is Created and Assinged to "+update_at.user_id.display_name ,
                    })
                else:
                    dic.update({
                        'error': 'error',
                    })
        else:
            dic.update({
                'error': 'error',
            })
        return json.dumps(dic)

    @http.route('/cancel-activity', type='http', auth="user", website=True, csrf=False)
    def cancel_activity(self, **kw):
        vals = {}
        dic = {}
        if kw.get('id'):
            sh_activity_obj = request.env['mail.activity']
            sh_activity_id = sh_activity_obj.sudo().browse(
                int(kw.get('id')))
            if sh_activity_id:
                sh_activity_id.action_cancel()
                dic.update({
                    'success': 'success',
                })
            else:
                dic.update({
                    'error': 'error',
                })
        return json.dumps(dic)

    @http.route('/done_schedule_next_activity', type='http', auth="user", website=True, csrf=False)
    def done_schedule_next(self, **kw):
        vals = {}
        dic = {}
        if kw.get('id'):
            sh_activity_obj = request.env['mail.activity']
            sh_activity_id = sh_activity_obj.sudo().browse(
                int(kw.get('id')))
            if sh_activity_id:
                messages, next_activities = sh_activity_id._action_done(
                    feedback=False)
                if next_activities:
                    dic.update({
                        'error': 'error',
                    })
                else:
                    dic.update({
                        'success': 'success',
                    })
            return json.dumps(dic)

    @http.route('/save_record_action', type='http', auth="user", website=True, csrf=False)
    def save_record_action(self, **kw):
        sh_activity_obj = request.env['mail.activity']
        vals = {}
        dic = {}
        if kw.get('id'):
            sh_activity_id = sh_activity_obj.sudo().browse(
                int(kw.get('id')))
            if sh_activity_id:
                if kw.get('due_date'):
                    vals.update({
                        'date_deadline':  datetime.strptime(kw.get('due_date'), DEFAULT_SERVER_DATE_FORMAT).date(),
                    })
                if kw.get('duedatereminder'):
                    vals.update({
                        'sh_date_deadline':  datetime.strptime(kw.get('due_date'), DEFAULT_SERVER_DATE_FORMAT),
                    })
                if kw.get('link_activity_type_id'):
                    vals.update({
                        'activity_type_id': int(kw.get('link_activity_type_id')),
                    })
                if kw.get('assigned_to'):
                    vals.update({
                        'user_id': int(kw.get('assigned_to')),
                    })
                if kw.get('supervisor'):
                    vals.update({
                        'supervisor_id': int(kw.get('supervisor')),
                    })
                if kw.get('summary'):
                    vals.update({
                        'summary': kw.get('summary'),
                    })
                if kw.get('activity_tags'):
                    vals.update({
                        'sh_activity_tags': kw.get('activity_tags'),
                    })
                if kw.get('reminders'):
                    vals.update({
                        'sh_activity_alarm_ids': kw.get('reminders'),
                    })
                if kw.get('user_ids'):
                    vals.update({
                        'sh_user_ids': kw.get('user_ids'),
                    })
            if vals:
                update_at = sh_activity_id.sudo().sudo().write(vals)
                if update_at:
                    dic.update({
                        'success': 'success',
                    })
                else:
                    dic.update({
                        'error': 'error',
                    })
        return json.dumps(dic)
    
   
        