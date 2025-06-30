"""Employee Task Management Model
================================
This module extends Odoo to provide a *flexible task‑assignment system* that supports
recurring schedules, dependencies, fallback tasks, email notifications and activity
logging.  The comments below document each public and helper method so future
maintainers can quickly understand what it does and why it exists.
"""
from odoo import models, fields, api ,tools,exceptions
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
from datetime import datetime,date
import base64
import logging
_logger = logging.getLogger(__name__)


class EmployeeTask(models.Model):
    """Main model used to assign and track employee tasks."""
    _name = 'employee.task'
    _description = 'EmployeeTask'
    _order = 'due_date asc'
    _rec_name = 'task_code'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # -------------------------------------------------------------------------
    # Core fields
    # -------------------------------------------------------------------------
    # add id to eash asinnged task ..
    task_code = fields.Char(string="Task ID", readonly=True, copy=False, required=True, default='New')
    task_time = fields.Datetime(string="Task Time")

    # Task template – holds default rules such as delays, fallback, dependency …

    task_id = fields.Many2one(
        'task.name',
        string="Task Name",
        required=True,
        help="Choose a task from the list of predefined activities")
    employee_id = fields.Many2one('hr.employee', string="Assigned To", required=True)
    description = fields.Text(string="Description")
    image = fields.Binary(string="Task Image", attachment=True)
    active = fields.Boolean(string='Active', default=True, readonly=False)
    due_date = fields.Date(string="Due Date")
    task_type = fields.Selection([
        ('none','None'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),], string="Task Type", required=True,default='none')
    repeat_days_ids = fields.Many2many(
        'repeat.day',
        string="Repeat On Days",
        help="Choose days to repeat the task (weekly/monthly)")
    repeat_month_days = fields.Many2many(
        'repeat.month.day',
        string="Repeat On Month Days",
        help="For monthly tasks, select days like 10, 15, 20")
    status = fields.Selection([
        ('draft', 'To Assign'),
        ('assigned', 'Assigned'),
        ('done', 'Completed'),
        ('cancel', 'Cancelled'),
    ], string="Status", default='draft', tracking=True)

    status_display = fields.Selection([
        ('draft', 'To Assign'),
        ('assigned', 'Assigned'),
        ('done', 'Completed'),
        ('cancel', 'Cancelled'),
        ('overdue', 'Overdue'),
    ], string="Display Status", compute="_compute_status_display", store=False)
    repeat_until = fields.Date(string="Repeat Until")


    parent_task_id = fields.Many2one(
        'employee.task',
        string="Parent Task",
        help="The task that triggered this task, if any.",
        readonly=True
          )

    child_task_ids = fields.One2many(
        'employee.task',
        'parent_task_id',
        string="Next Tasks",
        help="Tasks that were created as a result of this task.",
        readonly=True
    )

    # Convenience – formatted email cached for debugging/logging purposes
    email_formatted = fields.Char(
        'Formatted Email',
        help='Format email address "Name <email@domain>"')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

    feedback_score = fields.Integer(
        string="Evaluation (%)",
        help="Manager rating for this task in percentage (e.g. 80%)",
        tracking=True,
        groups="task_assignment.group_task_manager"
    )
    # ---------------------------------------------------------------------
    # EMAIL HELPERS
    # ---------------------------------------------------------------------
    def compute_email_formatted(self, receiver):
        email_formatted = []
        if not receiver:
            return email_formatted

        final_reciver = receiver[0]  # Note: you are only using the first group. Consider flattening if needed.
        for partner in final_reciver:
            if partner.email:
                formatted = tools.formataddr((partner.name or "NoName", partner.email))
                email_formatted.append(formatted)
            else:
                _logger.warning("Missing email for partner: %s", partner.name)
        return email_formatted

    def notification_message(self, group):
        """
        one function one modification call any time
        :return:
        """
        receiver = []
        groups = []
        domain = None
        for ref in group:
            group_id = self.env.ref(ref).id
            groups.append(group_id)
        domain = [('id', 'in', groups)]
        group_ids = self.env['res.groups'].search(domain)
        if len(group_ids) > 1:
            for group in group_ids:
                for user in group.users:
                    if user.partner_id not in receiver:
                        receiver.append(user.partner_id)

        else:
            for user in group_ids.users:
                if user.partner_id not in receiver:
                    receiver.append(user.partner_id)
        return [receiver] if receiver else []

    def compute_user_email_formatted(self):
        """
        Return email formatted string from employee_id's user_id
        """
        if self.employee_id and self.employee_id.user_id and self.employee_id.user_id.partner_id:
            partner = self.employee_id.user_id.partner_id
            if partner.email:
                return [tools.formataddr((partner.name or u"False", partner.email or u"False"))]
        return []
    # ---------------------------------------------------------------------
    # RECURRING TASK GENERATORS
    # ---------------------------------------------------------------------
    #----------------------------------------------------
    # 1-if task daily and status done or cancel will create tomorrow task auto
    #-------------------------------------------------

    def _create_tomorrow_task(self):
        for rec in self:
            if not rec.task_time:
                raise ValidationError("Cannot create next task: task_time is missing.")

            tomorrow = rec.task_time + timedelta(days=1)

            if rec.repeat_until and tomorrow.date() > rec.repeat_until:
                continue

            #  Safe fallback value
            delay_days = 0

            if rec.task_id:
                delay_days = rec.task_id.due_date_delay if hasattr(rec.task_id,
                                                                'due_date_delay') and rec.task_id.due_date_delay else 0
            else:
                raise ValidationError("Missing task template (task.name) on current task.")

            #  Now always safe to calculate
            due_date = tomorrow.date() + timedelta(days=delay_days)

            self.env['employee.task'].create({
                'task_id': rec.task_id.id,
                'employee_id': rec.employee_id.id,
                'task_time': tomorrow,
                'due_date': due_date,
                'task_type': rec.task_type,
                'status': 'assigned',
                'description': rec.description,
                'repeat_days_ids': [(6, 0, rec.repeat_days_ids.ids)],
                'repeat_month_days': [(6, 0, rec.repeat_month_days.ids)],
                'parent_task_id': rec.id,
                'repeat_until': rec.repeat_until,
            })

    #-------------------------------
    #2-if task weekly and status done or cancel will create next task auto
    #--------------------------------
    def _create_weekly_tasks(self):
        for rec in self:
            # Mapping day name (in resource.day) to weekday index (0=Mon, 6=Sun)
            weekday_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2,
                'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
            }

            selected_weekdays = [weekday_map[d.name.lower()] for d in rec.repeat_days_ids if d.name.lower() in weekday_map]

            delay_days = rec.task_id.due_date_delay if hasattr(rec.task_id,
                                                            'due_date_delay') and rec.task_id.due_date_delay else 0

            start_date = rec.task_time.date() + timedelta(days=1)
            end_date = rec.repeat_until

            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() in selected_weekdays:
                    task_time = datetime.combine(current_date, rec.task_time.time())
                    due_date = current_date + timedelta(days=delay_days)

                    self.env['employee.task'].create({
                        'task_id': rec.task_id.id,
                        'employee_id': rec.employee_id.id,
                        'task_time': task_time,
                        'due_date': due_date,
                        'task_type': rec.task_type,
                        'status': 'assigned',
                        'description': rec.description,
                        'repeat_days_ids': [(6, 0, rec.repeat_days_ids.ids)],
                        'repeat_month_days': [(6, 0, rec.repeat_month_days.ids)],
                        'parent_task_id': rec.id,
                        'repeat_until': rec.repeat_until,
                    })

                current_date += timedelta(days=1)

    #--------------------------
    #3 create_monthly_tasks
    #--------------------------
    def _create_monthly_tasks(self):
        for rec in self:

            # Extract sorted list of valid day numbers (1 to 31) from the related model
            month_days = sorted([
                day.day_number for day in rec.repeat_month_days if 1 <= day.day_number <= 31
            ])

            delay_days = rec.task_id.due_date_delay if hasattr(rec.task_id,
                                                            'due_date_delay') and rec.task_id.due_date_delay else 0

            # Start from the first day of the task's current month
            current = rec.task_time.date().replace(day=1)
            current_month = current.month
            current_year = current.year

            while date(current_year, current_month, 1) <= rec.repeat_until:
                for day in month_days:
                    try:
                        task_date = date(current_year, current_month, day)
                    except ValueError:
                        # Skip invalid dates like Feb 30, April 31
                        continue

                    # Skip past or same-day tasks
                    if task_date < rec.task_time.date() + timedelta(days=1):
                        continue

                    # Stop if we exceed repeat_until
                    if task_date > rec.repeat_until:
                        continue

                    # Construct datetime with same time as original task
                    task_datetime = datetime.combine(task_date, rec.task_time.time())
                    due_date = task_date + timedelta(days=delay_days)

                    self.env['employee.task'].create({
                        'task_id': rec.task_id.id,
                        'employee_id': rec.employee_id.id,
                        'task_time': task_datetime,
                        'due_date': due_date,
                        'task_type': rec.task_type,
                        'status': 'assigned',
                        'description': rec.description,
                        'repeat_days_ids': [(6, 0, rec.repeat_days_ids.ids)],
                        'repeat_month_days': [(6, 0, rec.repeat_month_days.ids)],
                        'parent_task_id': rec.id,
                        'repeat_until': rec.repeat_until,
                    })

                # Move to the first of the next month
                if current_month == 12:
                    current_month = 1
                    current_year += 1
                else:
                    current_month += 1

    # ---------------------------------------------------------------------
    # ORM overrides
    # ---------------------------------------------------------------------
    #-------------------------
    # creat id for task
    #--------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('task_code', 'New') == 'New':
                today_str = datetime.today().strftime('%Y%m%d')  # e.g. 20250519
                seq_number = self.env['ir.sequence'].next_by_code('employee.task.code') or '0000'
                vals['task_code'] = f"TASK-{today_str}-{seq_number}"
        return super().create(vals_list)


    # ---------------------------------------------------------------------
    # Onchange / Constraints
    # ---------------------------------------------------------------------
    #----------------------------------------
    # if task type daily make repeat day auto
    #------------------------------------------
    @api.onchange('task_type')
    def _onchange_task_type(self):
        if self.task_type == 'daily':
            self.repeat_days_ids = [(5, 0, 0)]  # Clear selected repeat_days_ids

    #-----------------------------------------------------------------
    # this function make field repeat days requair to weekly and monthly task type
    #-----------------------------------------------------------------

    @api.constrains('task_type', 'repeat_days_ids', 'repeat_month_days')
    def _check_repeat_days_required(self):
        for rec in self:
            if rec.task_type == 'weekly' and not rec.repeat_days_ids:
                raise ValidationError("Weekly tasks must have at least one weekday selected.")
            if rec.task_type == 'monthly' and not rec.repeat_month_days:
                raise ValidationError("Monthly tasks must have at least one month day selected.")
    # ---------------------------------------------------------------------
    # Computed fields
    # ---------------------------------------------------------------------
    #---------------------------------
    # to now if task is overdue
    #--------------------------------
    @api.depends('status', 'due_date')
    def _compute_status_display(self):
        today = fields.Date.today()
        for task in self:
            if task.due_date and task.due_date < today and task.status in ['draft', 'assigned']:
                task.status_display = 'overdue'
            else:
                task.status_display = task.status

    # ---------------------------------------------------------------------
    # BUTTON ACTIONS
    # ---------------------------------------------------------------------
    #-------------------------------------------
    # press button assign
    def action_assign(self):
        for rec in self:
            rec.status = 'assigned'

            # Schedule an activity to remind the employee
            if rec.employee_id.user_id:
                rec.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=rec.employee_id.user_id.id,
                    summary="Complete Task: %s" % rec.task_id.name,
                    note=rec.description or '',
                    date_deadline=rec.due_date or fields.Date.today()
                )

            # Compute recipient email
            email_formatted = rec.compute_user_email_formatted()
            rec.email_formatted = email_formatted[0] if email_formatted else False

            if not email_formatted:
                continue  # Or optionally log and skip

            # Get mail template
            template = rec.env.ref('task_assignment.mail_template_task_status_notification_users',
                                   raise_if_not_found=False)
            if not template:
                raise UserError("Mail template not found.")

            base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
            action_id = rec.env.ref('task_assignment.action_employee_task').id

            ctx = dict(self.env.context)
            ctx.update({
                'base_url': base_url,
                'model': rec._name,
                'action_id': action_id,
            })

            email_values = {
                'email_to': ','.join(email_formatted),
                'email_from': rec.company_id.email or self.env.user.email,
                'subject': f"Task {rec.task_code or rec.task_id.name} Assigned",
            }

            template.sudo().with_context(ctx).send_mail(
                rec.id, force_send=True, email_values=email_values
            )

    # -------------------------------------------
    # press button  complete
    def action_done(self):
        for rec in self:
            rec.status = 'done'

            # 1. Handle recurring tasks
            if rec.task_type == 'daily':
                rec._create_tomorrow_task()
            elif rec.task_type == 'weekly':
                rec._create_weekly_tasks()
            elif rec.task_type == 'monthly':
                rec._create_monthly_tasks()

            # 2. Handle dependent task
            dep_template = rec.task_id.dependent_task_id
            if dep_template:
                delay = timedelta(
                    days=dep_template.delay_days or 0,
                    hours=dep_template.delay_hours or 0,
                    minutes=dep_template.delay_minutes or 0,
                )
                task_time = rec.task_time + delay
                due_date = task_time.date() + timedelta(days=dep_template.due_date_delay or 0)

                next_employee = dep_template.default_employee_id
                if not next_employee:
                    raise ValidationError(
                        f"No default next employee set on dependent task '{dep_template.task_id}'."
                    )

                new_task =self.env['employee.task'].create({
                    'task_id': dep_template.id,
                    'employee_id': next_employee.id,
                    'task_time': task_time,
                    'due_date': due_date,
                    'task_type': 'none',
                    'status': 'assigned',
                    'description': f"Auto-created after completing '{rec.task_id.id}'",
                    'parent_task_id': rec.id,
                })
                # ✅ Send email notification to assigned employee
                try:
                    email_formatted = new_task.compute_user_email_formatted()
                    new_task.email_formatted = email_formatted[0] if email_formatted else False

                    if email_formatted:
                        template = new_task.env.ref('task_assignment.mail_template_task_status_notification_users',
                                                    raise_if_not_found=False)
                        if not template:
                            raise UserError("Mail template not found.")

                        base_url = new_task.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        action_id = new_task.env.ref('task_assignment.action_employee_task').id

                        ctx = dict(self.env.context)
                        ctx.update({
                            'base_url': base_url,
                            'model': new_task._name,
                            'action_id': action_id,
                        })

                        email_values = {
                            'email_to': ','.join(email_formatted),
                            'email_from': new_task.company_id.email or self.env.user.email,
                            'subject': f"New Dependent Task Assigned: {new_task.task_code or new_task.task_id.name}",
                        }

                        template.sudo().with_context(ctx).send_mail(new_task.id, force_send=True,
                                                                    email_values=email_values)

                except Exception as e:
                    _logger.exception(f"Failed to send email for dependent task {new_task.id}: {e}")

            # 3. Email Notification
            reciver = rec.notification_message(['task_assignment.group_task_manager'])
            email_formatted = rec.compute_email_formatted(reciver)
            if not email_formatted:
                raise UserError("No recipient email found.")

            rec.email_formatted = email_formatted[0]  # Optional for display/debug

            template = rec.env.ref('task_assignment.mail_template_task_status_notification', raise_if_not_found=False)
            if not template:
                raise UserError("Mail template not found.")

            base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
            action_id = rec.env.ref('task_assignment.action_employee_task').id

            ctx = dict(self.env.context)
            ctx.update({
                'base_url': base_url,
                'model': rec._name,
                'action_id': action_id,
            })

            email_values = {
                'email_to': ','.join(email_formatted),
                'email_from': rec.company_id.email or self.env.user.email,
                'subject': f"Task {rec.task_code} Completed",
            }

            template.sudo().with_context(ctx).send_mail(rec.id, force_send=True, email_values=email_values)

    #-------------------------------------------
    # press button  cancel
    def action_cancel(self):
        for rec in self:
            rec.status = 'cancel'

            # Handle recurring tasks as usual
            if rec.task_type == 'daily':
                rec._create_tomorrow_task()

            # Handle fallback task logic
            fallback_template = rec.task_id.fallback_task_id
            if fallback_template:
                delay = timedelta(
                    days=fallback_template.delay_days or 0,
                    hours=fallback_template.delay_hours or 0,
                    minutes=fallback_template.delay_minutes or 0,
                )
                task_time = rec.task_time + delay
                due_date = task_time.date() + timedelta(days=fallback_template.due_date_delay or 0)

                next_employee = fallback_template.default_employee_id
                if not next_employee:
                    raise ValidationError(
                        f"No default employee set for fallback task '{fallback_template.name}'.")

                self.env['employee.task'].create({
                    'task_id': fallback_template.id,
                    'employee_id': next_employee.id,
                    'task_time': task_time,
                    'due_date': due_date,
                    'task_type': 'none',
                    'status': 'assigned',
                    'description': f"Auto-created after cancellation of '{rec.task_id.name}'",
                    'parent_task_id': rec.id,
                })
            # 3. Email Notification
            reciver = rec.notification_message(['task_assignment.group_task_manager'])
            email_formatted = rec.compute_email_formatted(reciver)
            if not email_formatted:
                raise UserError("No recipient email found.")

            rec.email_formatted = email_formatted[0]  # Optional for display/debug

            template = rec.env.ref('task_assignment.mail_template_task_status_notification_cancel', raise_if_not_found=False)
            if not template:
                raise UserError("Mail template not found.")

            base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
            action_id = rec.env.ref('task_assignment.action_employee_task').id

            ctx = dict(self.env.context)
            ctx.update({
                'base_url': base_url,
                'model': rec._name,
                'action_id': action_id,
            })

            email_values = {
                'email_to': ','.join(email_formatted),
                'email_from': rec.company_id.email or self.env.user.email,
                'subject': f"Task {rec.task_code} Canceled",
            }

            template.sudo().with_context(ctx).send_mail(rec.id, force_send=True, email_values=email_values)


    #---------------------------------
    #if overdue will creat task to other user
    #---------------------------------
    @api.model
    def create_fallback_for_overdue_tasks(self):
        overdue_tasks = self.search([
            ('status', 'in', ['draft', 'assigned']),
            ('due_date', '<', fields.Date.today()),
        ])
        for rec in overdue_tasks:
            fallback_template = rec.task_id.fallback_task_id
            if not fallback_template:
                continue

            # Skip if fallback already exists
            if rec.child_task_ids.filtered(lambda t: t.task_id == fallback_template):
                continue

            delay = timedelta(
                days=fallback_template.delay_days or 0,
                hours=fallback_template.delay_hours or 0,
                minutes=fallback_template.delay_minutes or 0,
            )
            task_time = fields.Datetime.now() + delay
            due_date = task_time.date() + timedelta(days=fallback_template.due_date_delay or 0)

            next_employee = fallback_template.default_employee_id
            if not next_employee:
                raise ValidationError(f"No default employee set for fallback task '{fallback_template.name}'.")

            # ✅ Create fallback task
            fallback_task = self.env['employee.task'].create({
                'task_id': fallback_template.id,
                'employee_id': next_employee.id,
                'task_time': task_time,
                'due_date': due_date,
                'task_type': 'none',
                'status': 'assigned',
                'description': f"Auto-created after cancellation of '{rec.task_id.name}'",
                'parent_task_id': rec.id,
            })

            # ✅ Send Email Notification
            try:
                reciver = rec.notification_message(['task_assignment.group_task_manager'])
                email_formatted = rec.compute_email_formatted(reciver)
                if not email_formatted:
                    continue  # Or log an error

                template = rec.env.ref(
                    'task_assignment.mail_template_task_status_notification_ovedue', raise_if_not_found=False
                )
                if not template:
                    continue  # Or log an error

                base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
                action_id = rec.env.ref('task_assignment.action_employee_task').id

                ctx = dict(self.env.context)
                ctx.update({
                    'base_url': base_url,
                    'model': rec._name,
                    'action_id': action_id,
                })
                email_values = {
                    'email_to': ','.join(email_formatted),
                    'email_from': rec.company_id.email or self.env.user.email,
                    'subject': f"Fallback Task Created due to Overdue Task: {rec.task_code or rec.task_id.name}",
                }

                template.sudo().with_context(ctx).send_mail(rec.id, force_send=True,
                                                            email_values=email_values)

            except Exception as e:
                _logger = self.env['ir.logging']
                _logger.sudo().create({
                    'name': 'Fallback Task Email Error',
                    'type': 'server',
                    'level': 'error',
                    'message': f"Failed to send fallback task email for task {fallback_task.id}: {str(e)}",
                    'path': 'employee.task',
                    'func': 'create_fallback_for_overdue_tasks',
                    'line': '0',
                })






