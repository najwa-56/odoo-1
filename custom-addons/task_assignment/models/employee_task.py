from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta
from datetime import datetime,date
import base64

class EmployeeTask(models.Model):
    _name = 'employee.task'
    _description = 'EmployeeTask'
    _order = 'due_date asc'
    _rec_name = 'task_code'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # this model to assign task to employee ...

    # add id to eash asinnged task ..
    task_code = fields.Char(string="Task ID", readonly=True, copy=False, required=True, default='New')
    task_time = fields.Datetime(string="Task Time")

    #####################
    task_id = fields.Many2one( #task_id
        'task.name',
        string="Task Name",
        required=True,
        help="Choose a task from the list of predefined activities")
    employee_id = fields.Many2one('hr.employee', string="Assigned To", required=True)
    description = fields.Text(string="Description")
    image = fields.Binary(string="Task Image", attachment=True)
    active = fields.Boolean(string='Active', default=True, readonly=False)
    due_date = fields.Date(string="Due Date")
    task_type = fields.Selection([ # add None type
        ('none','None'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),], string="Task Type", required=True,default='none')
    repeat_days_ids = fields.Many2many( #repeat_days_ids
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
    repeat_until = fields.Date(string="Repeat Until")  # <-- Add this line


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



    #----------------------------------------------------
    # if task daily and status done or cancel will create tomorrow task auto
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
    #if task weekly and status done or cancel will create next task auto
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



    # -------------------------------------------
    # press button  complete
    def action_done(self):
        for rec in self:
            rec.status = 'done'

            #  First: Handle daily recurring task for the same employee
            if rec.task_type == 'daily':
                rec._create_tomorrow_task()

            elif rec.task_type == 'weekly':
                rec._create_weekly_tasks()

            elif rec.task_type == 'monthly':
                rec._create_monthly_tasks()

            #  Second: Handle dependent task for another employee
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
                        f"No default next employee set on dependent task '{dep_template.task_id}'.")

                self.env['employee.task'].create({
                    'task_id': dep_template.id,
                    'employee_id': next_employee.id,
                    'task_time': task_time,
                    'due_date': due_date,
                    'task_type': 'none',  # Or use dep_template.task_type if you want it dynamic
                    'status': 'assigned',
                    'description': f"Auto-created after completing '{rec.task_id.id}'",
                    'parent_task_id': rec.id,

                })


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
            # check if fallback task already exists
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


