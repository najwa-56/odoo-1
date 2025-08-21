from datetime import timedelta
from odoo import models, fields,api
from odoo.exceptions import ValidationError

class TaskName(models.Model):
    _name = 'task.name'
    _description = 'task Name'
    # to create task
    name = fields.Char(string='task Name', required=True)
    is_linked = fields.Selection([
        ('linked', 'Linked'),
        ('not_linked', 'Not Linked')
    ], string="Linked or Not", default='not_linked')
    tag_ids = fields.Many2many('task.tag', string='Tags')
    description = fields.Html("Description")
    task_image = fields.Binary("Task Image")
    #sequence = fields.Integer(string="Sequence", default=10)
    dependent_task_id = fields.Many2one(
        'task.name',
        string="Next Task Template",
        help="Task that should follow this one"
    )
    fallback_task_id = fields.Many2one(
        'task.name',
        string="Fallback Task",
        help="Used if the main task is cancelled or overdue"
    )
    delay_days = fields.Integer(string="Delay (Days)", default=0)
    delay_hours = fields.Integer(string="Delay (Hours)", default=0)
    delay_minutes = fields.Integer(string="Delay (Minutes)", default=0)
    default_employee_id = fields.Many2one(
        'hr.employee',
        string=" Task Assigned To",
        help="If set, the next task will be assigned to this employee"
    )
    due_date_delay = fields.Integer(
        string="Due Date Delay (Days)",
        help="Number of days after task_time to set the due date for generated tasks"
    )
    priority_task = fields.Selection([
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], string="priority")

  