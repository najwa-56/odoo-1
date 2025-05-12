# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
from datetime import datetime, timedelta ,date
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.osv import expression
from odoo.http import request
from odoo.exceptions import UserError

class ActivityDashboard(models.Model):
    _name = 'activity.dashboard'
    _description = 'Activity Dashboard'


    @api.model
    def get_model(self):
        return [{'id': model.id, 'name': model.name} for model in self.env['ir.model'].sudo().search([])]
    
    # Get Current company activate document model and its models
    @api.model
    def get_model_activate(self,current_company_id):
        company=self.env["res.company"].sudo().browse(current_company_id)
        document_models=[]
        if company.sh_document_model:
            if company.sh_document_model_ids:
                domain = [('id','in',company.sh_document_model_ids.ids)]
                document_models = self.env["ir.model"].sudo().search(domain).ids
        is_document_model=company.sh_document_model
        return is_document_model,document_models

    @api.model
    def get_user(self):
        return [{'id': user.id, 'name': user.name} for user in self.env['res.users'].sudo().search([])]

    @api.model
    def get_type(self):
        return [{'id': type.id, 'name': type.name} for type in self.env['mail.activity.type'].sudo().search([])]
    
    @api.model
    def get_activity_count_tbl(self, filter_date, filter_user, start_date, end_date, filter_supervisor,filter_model,filter_record,filter_type):
        uid = request.session.uid
        user = request.env['res.users'].sudo().browse(uid)
        cids = request.httprequest.cookies.get('cids', str(user.company_id.id))
        cids = [int(cid) for cid in cids.split(',')]
        # domain = []
        domain = [
            ('company_id','in',cids)
        ]
        if filter_type and filter_type != None:
            domain.append(('activity_type_id','=',int(filter_type)))


        if filter_date == 'custom' and not (start_date and end_date):
            start_date = end_date = False
        elif filter_date and filter_date != 'custom':
            start_date, end_date = self.generate_start_end_date(option=filter_date)

        if isinstance(start_date, str) and isinstance(end_date, str):
            start_date_time = datetime.strptime(start_date, "%m/%d/%Y").replace(hour=0, minute=0, second=0) #update name purpose with using only date field
            end_date_time = datetime.strptime(end_date, "%m/%d/%Y").replace(hour=23, minute=59, second=59)
            domain.append(('create_date', '>=', start_date_time))
            domain.append(('create_date', '<=', end_date_time))
            
            sh_start_date = datetime.strptime(start_date, "%m/%d/%Y") #only date field
            sh_end_date = datetime.strptime(end_date, "%m/%d/%Y")
            
            domain=expression.OR([domain, [('date_done', '>=', sh_start_date),('date_done', '<=', sh_end_date)]])
            domain=expression.OR([domain, [('date_deadline', '>=', sh_start_date),('date_deadline', '<=', sh_end_date)]])


        # FILTER USER
        if filter_user not in ['', "", None, False]:
            domain.append(('|'))
            domain.append(('sh_user_ids', 'in', [int(filter_user)]))
            domain.append(('user_id', '=', int(filter_user)))
        else:
            if self.env.user.has_group('sh_activities_management.group_activity_supervisor') and self.env.user.has_group('sh_activities_management.group_activity_user') and not self.env.user.has_group('sh_activities_management.group_activity_manager'):
                domain.append(('|'))
                domain.append(('|'))
                domain.append(('user_id', '!=', self.env.user.id))
                domain.append(('user_id', '=', self.env.user.id))
                domain.append(('sh_user_ids', 'in', [self.env.user.id]))

            elif not self.env.user.has_group('sh_activities_management.group_activity_supervisor') and self.env.user.has_group('sh_activities_management.group_activity_user') and not self.env.user.has_group('sh_activities_management.group_activity_manager'):
                domain.append(('|'))
                domain.append(('sh_user_ids', 'in', [self.env.user.id]))
                domain.append(('user_id', '=', self.env.user.id))
        if filter_supervisor not in ['', "", None, False]:
            domain.append(('supervisor_id', '=', int(filter_supervisor)))
        else:
            if self.env.user.has_group('sh_activities_management.group_activity_supervisor') and self.env.user.has_group('sh_activities_management.group_activity_user') and not self.env.user.has_group('sh_activities_management.group_activity_manager'):
                domain.append(('|'))
                domain.append(('|'))
                domain.append(('supervisor_id', '=', self.env.user.id))
                domain.append(('user_id', '=', self.env.user.id))
                domain.append(('sh_user_ids', 'in', [self.env.user.id]))
            elif not self.env.user.has_group('sh_activities_management.group_activity_supervisor') and self.env.user.has_group('sh_activities_management.group_activity_user') and not self.env.user.has_group('sh_activities_management.group_activity_manager'):
                domain.append(('|'))
                domain.append(('|'))
                domain.append(('supervisor_id', '=', self.env.user.id))
                domain.append(('supervisor_id', '!=', self.env.user.id))
                domain.append(('supervisor_id', '=', False))
        domain.append(('|'))
        domain.append(('active', '=', True))
        domain.append(('active', '=', False))
        if filter_model and filter_model  not in ['',"",None,False]:
            res_model_id = self.env['ir.model'].sudo().browse(int(filter_model))
            if res_model_id and 'activity_ids' not in self.env[res_model_id.model]._fields:
                raise UserError("You can't found activities for this document model.")
            if filter_record not in ['',"",None,False]:
                domain.append(('res_id','=',filter_record))
                domain.append(('res_model_id','=',int(filter_model)))
            else:
                domain.append(('res_model_id','=',int(filter_model)))
        # -------------------------------------
        # ALL ACTIVITES
        # -------------------------------------

        from_clause, where_clause_all_activities, where_params_all_activities = self.env['mail.activity']._where_calc(domain).get_sql()

        query = f'''
            SELECT "mail_activity".id FROM "mail_activity" WHERE {where_clause_all_activities}
        '''

        self.env.cr.execute(query, where_params_all_activities)    
        result_all = self._cr.fetchall()

        all_activities_ids = [r[0] for r in result_all]
        activities = self.env['mail.activity'].search([('id','in',all_activities_ids),'|',('active','=',True),('active','=',False)])
        # activities = self.env['mail.activity'].browse(all_activities_ids)

        # return {}

        # -------------------------------------
        # ALL ACTIVITES
        # -------------------------------------


        # -------------------------------------
        # PLANNED ACTIVITES
        # -------------------------------------

        # planned_domain = domain.copy()
        planned_domain = expression.AND([domain.copy(), [('active','=',True)]])
        planned_domain = expression.AND([planned_domain.copy(), [('date_deadline','!=',False)]])
        planned_domain = expression.AND([planned_domain.copy(), [('date_deadline','>=',fields.Date.today())]])
        from_clause, where_clause_planned_activities, where_params_planned_activities = self.env['mail.activity']._where_calc(planned_domain).get_sql()

        query = f'''
            SELECT "mail_activity".id FROM "mail_activity" WHERE {where_clause_planned_activities}
        '''

        self.env.cr.execute(query, where_params_planned_activities)    
        result_planned_activities = self._cr.fetchall()

        planned_activities_list = [r[0] for r in result_planned_activities]
        planned_activities = self.env['mail.activity'].search([('id','in',planned_activities_list)])
        # planned_activities = self.env['mail.activity'].browse(planned_activities_list)
        
        # -------------------------------------
        # PLANNED ACTIVITES
        # -------------------------------------


        # -------------------------------------
        # OVERDUE ACTIVITES
        # -------------------------------------
          
        # overdue_domain = domain.copy()
        overdue_domain = expression.AND([domain.copy(), [('active','=',True)]])
        overdue_domain = expression.AND([overdue_domain.copy(), [('date_deadline','!=',False)]])
        overdue_domain = expression.AND([overdue_domain.copy(), [('date_deadline','<',fields.Date.today())]])

        from_clause, where_clause_overdue_activities, where_params_overdue_activities = self.env['mail.activity']._where_calc(overdue_domain).get_sql()

        query = f'''
            SELECT "mail_activity".id FROM "mail_activity" WHERE {where_clause_overdue_activities}
        '''

        self.env.cr.execute(query, where_params_overdue_activities)    
        result_overdue_activities = self._cr.fetchall()

        
        overdue_activities_list = [r[0] for r in result_overdue_activities]
        overdue_activities = self.env['mail.activity'].search([('id','in',overdue_activities_list)])
        # overdue_activities = self.env['mail.activity'].browse(overdue_activities_list)

        # -------------------------------------
        # OVERDUE ACTIVITES
        # -------------------------------------

        # -------------------------------------
        # COMPLETED ACTIVITES
        # ------------------------------------- 
        
        # completed_domain = domain.copy()
        completed_domain = expression.AND([domain.copy(), [('active','=',False)]])
        completed_domain = expression.AND([completed_domain.copy(), [('state','=','done')]])

        from_clause, where_clause_completed_activities, where_params_completed_activities = self.env['mail.activity']._where_calc(completed_domain).get_sql()

        query = f'''
            SELECT "mail_activity".id FROM "mail_activity" WHERE {where_clause_completed_activities}
        '''

        self.env.cr.execute(query, where_params_completed_activities)    
        result_completed_activities = self._cr.fetchall()
        completed_activities_list = [r[0] for r in result_completed_activities]
        completed_activities = self.env['mail.activity'].search([('id','in',completed_activities_list),'|',('active','=',True),('active','=',False)])
        # completed_activities = self.env['mail.activity'].browse(completed_activities_list)
        # -------------------------------------
        # COMPLETED ACTIVITES
        # ------------------------------------- 


        # -------------------------------------
        # CANCELLED ACTIVITES
        # -------------------------------------


        # cancelled_domain = domain.copy()
        cancelled_domain = expression.AND([domain.copy(), [('active','=',False)]])
        cancelled_domain = expression.AND([cancelled_domain.copy(), [('state','=','cancel')]])

        from_clause, where_clause_cancelled_activities, where_params_cancelled_activities = self.env['mail.activity']._where_calc(cancelled_domain).get_sql()

        query = f'''
            SELECT "mail_activity".id FROM "mail_activity" WHERE {where_clause_cancelled_activities}
        '''

        self.env.cr.execute(query, where_params_cancelled_activities)    
        result_cancelled_activities = self._cr.fetchall()
        
        cancelled_activities_list = [r[0] for r in result_cancelled_activities]
        cancelled_activities = self.env['mail.activity'].search([('id','in',cancelled_activities_list),'|',('active','=',True),('active','=',False)])
        # cancelled_activities = self.env['mail.activity'].browse(cancelled_activities_list)
        

        # -------------------------------------
        # CANCELLED ACTIVITES
        # -------------------------------------
        planned_activities_table=[]    
        if planned_activities_list:
            for planned in planned_activities_table:
                planned_activities_table.append({
                    'name':planned.name,
                    'activity_type':planned.activity_type_id.name,
                    'user_name':planned.user_id.name,
                    'supervisor_name':planned.supervisor_id.name,
                })  

        master_dictionary = {}
        stage_model = []
        if self.env.user.company_id.sh_display_all_activities_counter:
            stage_model.append('All Activities')
        if self.env.user.company_id.sh_display_planned_activities_counter:
            stage_model.append('Planned Activities')
        if self.env.user.company_id.sh_display_completed_activities_counter:
            stage_model.append('Completed Activities')
        if self.env.user.company_id.sh_display_overdue_activities_counter:
            stage_model.append('Overdue Activities')
        if self.env.user.company_id.sh_display_cancelled_activities_counter:
            stage_model.append('Cancelled Activities')
        for each in stage_model:
            act_count =[]          
            if each == 'All Activities':
                act_count = activities.ids
            if each == 'Planned Activities':
                act_count = planned_activities.ids                                 
            if each == 'Completed Activities':
                act_count = completed_activities.ids
            if each == 'Overdue Activities':
                act_count = overdue_activities.ids
            if each == 'Cancelled Activities':
                act_count = cancelled_activities.ids
            master_dictionary.update({
                    each:act_count
                })                 
        return master_dictionary

    def generate_start_end_date(self,option):
        today = datetime.now()  # replace with the actual current date

        if option == "today":
            start_date = end_date = today
        elif option == "yesterday":
            start_date = end_date = today - timedelta(days=1)
        elif option == "weekly":
            start_date = today - timedelta(days=today.weekday())
            end_date = today
        elif option == "prev_week":
            start_date = (today - timedelta(days=today.weekday())) - timedelta(days=7)
            end_date = today - timedelta(days=today.weekday() + 1)
        elif option == "monthly":
            start_date = date(today.year, today.month, 1)
            end_date = today
        elif option == "prev_month":
            first_day_prev_month = date(today.year, today.month, 1) - timedelta(days=1)
            start_date = date(first_day_prev_month.year, first_day_prev_month.month, 1)
            end_date = first_day_prev_month
        elif option == "cur_year":
            start_date = date(today.year, 1, 1)
            end_date = today
        elif option == "prev_year":
            start_date = date(today.year - 1, 1, 1)
            end_date = date(today.year - 1, 12, 31)
        else:
            start_date = end_date = today  # Default to today if no valid option is provided
            
        return start_date.strftime("%m/%d/%Y"), end_date.strftime("%m/%d/%Y")

    @api.model    
    def get_activity_tbl(self, filter_date, filter_user, start_date, end_date, filter_supervisor,filter_model,filter_record,filter_type):#,limit,offset):
        uid = request.session.uid
        user = request.env['res.users'].sudo().browse(uid)
        cids = request.httprequest.cookies.get('cids', str(user.company_id.id))
        cids = [int(cid) for cid in cids.split(',')]
        # domain = []
        domain = [
            ('company_id','in',cids)
        ]
        if filter_type and filter_type != None:
            domain.append(('activity_type_id','=',int(filter_type)))


        if filter_date == 'custom' and not (start_date and end_date):
            start_date = end_date = False
        elif filter_date and filter_date != 'custom':
            start_date, end_date = self.generate_start_end_date(option=filter_date)

        if isinstance(start_date, str) and isinstance(end_date, str):
            start_date_time = datetime.strptime(start_date, "%m/%d/%Y").replace(hour=0, minute=0, second=0)
            end_date_time = datetime.strptime(end_date, "%m/%d/%Y").replace(hour=23, minute=59, second=59)
            domain.append(('create_date', '>=', start_date_time)) #update name purpose with using only date field
            domain.append(('create_date', '<=', end_date_time))
            
            sh_start_date = datetime.strptime(start_date, "%m/%d/%Y") #only date field
            sh_end_date = datetime.strptime(end_date, "%m/%d/%Y")
            
            domain=expression.OR([domain, [('date_done', '>=', sh_start_date),('date_done', '<=', sh_end_date)]])
            domain=expression.OR([domain, [('date_deadline', '>=', sh_start_date),('date_deadline', '<=', sh_end_date)]])


        # FILTER USER
        if filter_user not in ['', "", None, False]:
            domain.append(('|'))
            domain.append(('sh_user_ids', 'in', [int(filter_user)]))
            domain.append(('user_id', '=', int(filter_user)))
        else:
            if self.env.user.has_group('sh_activities_management.group_activity_supervisor') and self.env.user.has_group('sh_activities_management.group_activity_user') and not self.env.user.has_group('sh_activities_management.group_activity_manager'):
                domain.append(('|'))
                domain.append(('|'))
                domain.append(('user_id', '!=', self.env.user.id))
                domain.append(('user_id', '=', self.env.user.id))
                domain.append(('sh_user_ids', 'in', [self.env.user.id]))

            elif not self.env.user.has_group('sh_activities_management.group_activity_supervisor') and self.env.user.has_group('sh_activities_management.group_activity_user') and not self.env.user.has_group('sh_activities_management.group_activity_manager'):
                domain.append(('|'))
                domain.append(('sh_user_ids', 'in', [self.env.user.id]))
                domain.append(('user_id', '=', self.env.user.id))
        if filter_supervisor not in ['', "", None, False]:
            domain.append(('supervisor_id', '=', int(filter_supervisor)))
        else:
            if self.env.user.has_group('sh_activities_management.group_activity_supervisor') and self.env.user.has_group('sh_activities_management.group_activity_user') and not self.env.user.has_group('sh_activities_management.group_activity_manager'):
                domain.append(('|'))
                domain.append(('|'))
                domain.append(('supervisor_id', '=', self.env.user.id))
                domain.append(('user_id', '=', self.env.user.id))
                domain.append(('sh_user_ids', 'in', [self.env.user.id]))
            elif not self.env.user.has_group('sh_activities_management.group_activity_supervisor') and self.env.user.has_group('sh_activities_management.group_activity_user') and not self.env.user.has_group('sh_activities_management.group_activity_manager'):
                domain.append(('|'))
                domain.append(('|'))
                domain.append(('supervisor_id', '=', self.env.user.id))
                domain.append(('supervisor_id', '!=', self.env.user.id))
                domain.append(('supervisor_id', '=', False))
        domain.append(('|'))
        domain.append(('active', '=', True))
        domain.append(('active', '=', False))
        if filter_model and filter_model  not in ['',"",None,False]:
            res_model_id = self.env['ir.model'].sudo().browse(int(filter_model))
            if res_model_id and 'activity_ids' not in self.env[res_model_id.model]._fields:
                raise UserError("You can't found activities for this document model.")
            if filter_record not in ['',"",None,False]:
                domain.append(('res_id','=',filter_record))
                domain.append(('res_model_id','=',int(filter_model)))
            else:
                domain.append(('res_model_id','=',int(filter_model)))
        # -------------------------------------
        # ALL ACTIVITES
        # -------------------------------------
        from_clause, where_clause_all_activities, where_params_all_activities = self.env['mail.activity']._where_calc(domain).get_sql()

        query = f'''
            SELECT "mail_activity".id FROM "mail_activity" WHERE {where_clause_all_activities}
        '''

        self.env.cr.execute(query, where_params_all_activities)    
        result_all = self._cr.fetchall()

        all_activities_ids = [int(r[0]) for r in result_all]
        activities = self.env['mail.activity'].search([('id','in',all_activities_ids),'|',('active','=',True),('active','=',False)])#,limit=limit, offset=offset)
        all_activities = self.env['mail.activity'].browse(activities.ids[:self.env.user.company_id.sh_all_table])

        # return {}

        # -------------------------------------
        # ALL ACTIVITES
        # -------------------------------------


        # -------------------------------------
        # PLANNED ACTIVITES
        # -------------------------------------

        # planned_domain = domain.copy()
        planned_domain = expression.AND([domain.copy(), [('active','=',True)]])
        planned_domain = expression.AND([planned_domain.copy(), [('date_deadline','!=',False)]])
        planned_domain = expression.AND([planned_domain.copy(), [('date_deadline','>=',fields.Date.today())]])
        from_clause, where_clause_planned_activities, where_params_planned_activities = self.env['mail.activity']._where_calc(planned_domain).get_sql()

        query = f'''
            SELECT "mail_activity".id FROM "mail_activity" WHERE {where_clause_planned_activities}
        '''

        self.env.cr.execute(query, where_params_planned_activities)    
        result_planned_activities = self._cr.fetchall()

        planned_activities_list = [int(r[0]) for r in result_planned_activities]
        planned_activities_search = self.env['mail.activity'].search([('id','in',planned_activities_list)])#,limit=limit,offset=offset)
        
        planned_activities_search_sudo_browse = self.env['mail.activity'].sudo().browse(planned_activities_list) #Use this for display only accessible record. Ex :- private project record is only display created user
        planned_activities = self.env['mail.activity'].browse(planned_activities_search.ids[:self.env.user.company_id.sh_planned_table])
        need_to_remove_planned_activities = planned_activities_search_sudo_browse - planned_activities_search
        if need_to_remove_planned_activities:
            for planned_remove in need_to_remove_planned_activities:
                planned_activities_list.remove(planned_remove.id)
        
        
        # -------------------------------------
        # PLANNED ACTIVITES
        # -------------------------------------


        # -------------------------------------
        # OVERDUE ACTIVITES
        # -------------------------------------
          
        # overdue_domain = domain.copy()
        overdue_domain = expression.AND([domain.copy(), [('active','=',True)]])
        overdue_domain = expression.AND([overdue_domain.copy(), [('date_deadline','!=',False)]])
        overdue_domain = expression.AND([overdue_domain.copy(), [('date_deadline','<',fields.Date.today())]])

        from_clause, where_clause_overdue_activities, where_params_overdue_activities = self.env['mail.activity']._where_calc(overdue_domain).get_sql()

        query = f'''
            SELECT "mail_activity".id FROM "mail_activity" WHERE {where_clause_overdue_activities}
        '''

        self.env.cr.execute(query, where_params_overdue_activities)    
        result_overdue_activities = self._cr.fetchall()

        
        overdue_activities_list = [int(r[0]) for r in result_overdue_activities]
        overdue_activities_search = self.env['mail.activity'].search([('id','in',overdue_activities_list)])#,limit=limit,offset=offset)
        overdue_activities = self.env['mail.activity'].browse(overdue_activities_search.ids[:self.env.user.company_id.sh_due_table])

        # -------------------------------------
        # OVERDUE ACTIVITES
        # -------------------------------------

        # -------------------------------------
        # COMPLETED ACTIVITES
        # ------------------------------------- 
        
        # completed_domain = domain.copy()
        completed_domain = expression.AND([domain.copy(), [('active','=',False)]])
        completed_domain = expression.AND([completed_domain.copy(), [('state','=','done')]])

        from_clause, where_clause_completed_activities, where_params_completed_activities = self.env['mail.activity']._where_calc(completed_domain).get_sql()

        query = f'''
            SELECT "mail_activity".id FROM "mail_activity" WHERE {where_clause_completed_activities}
        '''

        self.env.cr.execute(query, where_params_completed_activities)    
        result_completed_activities = self._cr.fetchall()
        completed_activities_list = [int(r[0]) for r in result_completed_activities]
        completed_activities_search = self.env['mail.activity'].search([('id','in',completed_activities_list),'|',('active','=',True),('active','=',False)])#,limit=limit,offset=offset)
        completed_activities = self.env['mail.activity'].browse(completed_activities_search.ids[:self.env.user.company_id.sh_completed_table])
        # -------------------------------------
        # COMPLETED ACTIVITES
        # ------------------------------------- 


        # -------------------------------------
        # CANCELLED ACTIVITES
        # -------------------------------------


        # cancelled_domain = domain.copy()
        cancelled_domain = expression.AND([domain.copy(), [('active','=',False)]])
        cancelled_domain = expression.AND([cancelled_domain.copy(), [('state','=','cancel')]])

        from_clause, where_clause_cancelled_activities, where_params_cancelled_activities = self.env['mail.activity']._where_calc(cancelled_domain).get_sql()

        query = f'''
            SELECT "mail_activity".id FROM "mail_activity" WHERE {where_clause_cancelled_activities}
        '''

        self.env.cr.execute(query, where_params_cancelled_activities)    
        result_cancelled_activities = self._cr.fetchall()
        
        cancelled_activities_list = [int(r[0]) for r in result_cancelled_activities]
        cancelled_activities_search = self.env['mail.activity'].search([('id','in',cancelled_activities_list),'|',('active','=',False),('active','=',True)])
        cancelled_activities = self.env['mail.activity'].browse(cancelled_activities_search.ids[:self.env.user.company_id.sh_cancel_table])
        

        # -------------------------------------
        # CANCELLED ACTIVITES
        # -------------------------------------
        planned_activities_table=[]    
        if planned_activities_list:
            for planned in planned_activities_table:
                planned_activities_table.append({
                    'name':planned.name,
                    'activity_type':planned.activity_type_id.name,
                    'user_name':planned.user_id.name,
                    'supervisor_name':planned.supervisor_id.name,
                })  

        master_list = []
        stage_model = []
        if self.env.user.company_id.sh_display_all_activities_table:
            stage_model.append('All Activities')
        if self.env.user.company_id.sh_display_planned_activities_table:
            stage_model.append('Planned Activities')
        if self.env.user.company_id.sh_display_completed_activities_table:
            stage_model.append('Completed Activities')
        if self.env.user.company_id.sh_display_overdue_activities_table:
            stage_model.append('Overdue Activities')
        if self.env.user.company_id.sh_display_cancelled_activities_table:
            stage_model.append('Cancelled Activities')
        # max_records_per_stage = 8
        # if limit:
        #     max_records_per_stage = limit
        for each in stage_model:
            act_count =0
            tem_act =[]
            if each == 'All Activities':
                act_count = len(all_activities)
                if act_count > 0:
                                      
                    for t in all_activities:
                        activity_data_list = [
                                t.res_name, t.activity_type_id.name, t.user_id.name,
                                t.user_id.name, t.date_deadline,t.id,t.state,t.res_model,str(t.res_id)
                            ]
                        tem_act.append(activity_data_list)
            if each == 'Planned Activities':
                act_count = len(planned_activities)
                planned_activities = self.env['mail.activity'].browse(planned_activities_list)              
                if act_count > 0:
                    for t in planned_activities:
                        activity_data_list = [
                                t.res_name, t.activity_type_id.name, t.user_id.name,
                                t.user_id.name, t.date_deadline,t.id,t.state,t.res_model,str(t.res_id)
                            ]
                        tem_act.append(activity_data_list)
            if each == 'Completed Activities':
                act_count = len(completed_activities)               
                if act_count > 0:
                    for t in completed_activities:
                        activity_data_list = [
                                t.res_name, t.activity_type_id.name, t.user_id.name,
                                t.supervisor_id.name, t.date_deadline,t.id,t.state,t.res_model,str(t.res_id)
                            ]
                        tem_act.append(activity_data_list)
            if each == 'Overdue Activities':
                act_count = len(overdue_activities)
                if act_count > 0:
                    for t in overdue_activities:
                        activity_data_list = [
                                t.res_name, t.activity_type_id.name, t.user_id.name,
                                t.user_id.name, t.date_deadline,t.id,t.state,t.res_model,str(t.res_id)
                            ]
                        tem_act.append(activity_data_list)
            if each == 'Cancelled Activities':
                act_count = len(cancelled_activities)               
                if act_count > 0:
                    for t in cancelled_activities:
                        activity_data_list = [
                                t.res_name, t.activity_type_id.name, t.user_id.name,
                                t.supervisor_id.name, t.date_deadline,t.id,t.state,t.res_model,str(t.res_id)
                            ]
                        tem_act.append(activity_data_list)
            each_table_data = {               
                'status_name': each,
                'count_acts':act_count,
                'activitiy_data': tem_act
            }
            if each == 'All Activities':
                # for ticket in tem_act:
                #     if len(each_table_data['activitiy_data']) < max_records_per_stage:
                #         each_table_data['activitiy_data'].append(ticket)
                each_table_data.update({
                    'stage_id':'all'
                })
            if each == 'Planned Activities':
                # for ticket in tem_act:
                #     if len(each_table_data['activitiy_data']) < max_records_per_stage:
                #         each_table_data['activitiy_data'].append(ticket)
                each_table_data.update({
                    'stage_id':'planned'
                })
            if each == 'Completed Activities':
                # for ticket in tem_act:
                #     if len(each_table_data['activitiy_data']) < max_records_per_stage:
                #         each_table_data['activitiy_data'].append(ticket)
                each_table_data.update({
                    'stage_id':'completed'
                })
            if each == 'Overdue Activities':
                # for ticket in tem_act:
                #     if len(each_table_data['activitiy_data']) < max_records_per_stage:
                #         each_table_data['activitiy_data'].append(ticket)
                each_table_data.update({
                    'stage_id':'overdue'
                })
            if each == 'Cancelled Activities':
                # for ticket in tem_act:
                #     if len(each_table_data['activitiy_data']) < max_records_per_stage:
                #         each_table_data['activitiy_data'].append(ticket)
                each_table_data.update({
                    'stage_id':'cancel'
                })
            master_list.append(each_table_data)
        return master_list


    @api.model
    def get_user_list(self):
        uid = request.session.uid
        user = request.env['res.users'].sudo().browse(uid)
        cids = request.httprequest.cookies.get('cids', str(user.company_id.id))
        cids = [int(cid) for cid in cids.split(',')]
        domain = [
            ('company_ids', 'in', cids),
            ('share','=',False)
        ]
        users = self.env["res.users"].sudo().search_read(domain,['id','name'])
        return users

    # Comment this code because of no use  and use this some code in get_model_activate method
    # @api.model
    # def get_document_models(self):
    #     document_models = False
    #     uid = request.session.uid
    #     user = request.env['res.users'].sudo().browse(uid)
    #     cids = request.httprequest.cookies.get('cids', str(user.company_id.id))
    #     cids = [int(cid) for cid in cids.split(',')]
    #     company_id = self.env['res.company'].sudo().browse(cids)[0]
    #     if company_id.sh_document_model:
    #         if company_id.sh_document_model_ids:
    #             domain = [('id','in',company_id.sh_document_model_ids.ids)]
    #             document_models = self.env["ir.model"].sudo().search_read(domain,['id','name'])
    #     return document_models

    @api.model
    def get_document_model_records(self,filter_model):
        document_model_records = False
        if filter_model not in ["",None,False]:
            model_id = self.env['ir.model'].sudo().browse(int(filter_model))
            if model_id:
                if 'activity_ids' not in self.env[model_id.model]._fields:
                    raise UserError("You can't found activities for this document model.")
                model_records = self.env[model_id.model].sudo().search([('activity_ids','!=',False)])
                domain = [('id','in',model_records.ids)]
                document_model_records = self.env[model_id.model].sudo().search_read(domain,['id','name'])
        return document_model_records

    @api.model
    def sh_get_activity_types(self):
        domain=[('active','=',True)]
        return self.env['mail.activity.type'].sudo().search_read(domain,['id','name'])
    
    @api.model
    def get_default_config(self):
        dic={
            'sh_display_cancelled_activities_counter':False,
            'sh_display_overdue_activities_counter':False,
            'sh_display_completed_activities_counter':False,
            'sh_display_planned_activities_counter':False,
            'sh_display_all_activities_counter':False,
        }
        if request.env.company.sh_display_cancelled_activities_counter:
            dic['sh_display_cancelled_activities_counter']=True
        if request.env.company.sh_display_overdue_activities_counter:
            dic['sh_display_overdue_activities_counter']=True
        if request.env.company.sh_display_completed_activities_counter:
            dic['sh_display_completed_activities_counter']=True
        if request.env.company.sh_display_planned_activities_counter:
            dic['sh_display_planned_activities_counter']=True
        if request.env.company.sh_display_all_activities_counter:
            dic['sh_display_all_activities_counter']=True      
        return dic