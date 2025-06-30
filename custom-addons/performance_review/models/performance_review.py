from odoo import models, fields, api
from datetime import date

class PerformanceReview(models.Model):
    _name = 'performance.review'
    _description = 'Employee Performance Review'
    _order = 'review_date desc'

    name = fields.Char(string="Review Name", required=True, default="New")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    review_date = fields.Date(string="Review Date", default=fields.Date.today)
    period_start = fields.Date(string="Period Start", required=True)
    period_end = fields.Date(string="Period End", required=True)

    task_ids = fields.One2many('employee.task', compute='_compute_tasks', string="Tasks")
    number_of_tasks = fields.Integer(compute='_compute_tasks', string="Number of Tasks")
    completed_tasks = fields.Integer(compute='_compute_tasks', string="Completed Tasks")
    completion_rate = fields.Float(compute='_compute_tasks', string="Completion Rate (%)")
    average_score = fields.Float(compute='_compute_tasks', string="Final Evaluation (%)")
    status = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('needs_improvement', 'Needs Improvement')
    ], compute='_compute_tasks', string="Status", store=True)

    @api.depends('employee_id', 'period_start', 'period_end')
    def _compute_tasks(self):
        for rec in self:
            domain = [
                ('employee_id', '=', rec.employee_id.id),
                ('task_time', '>=', rec.period_start),
                ('due_date', '<=', rec.period_end),
            ]
            tasks = self.env['employee.task'].search(domain)
            rec.task_ids = tasks
            rec.number_of_tasks = len(tasks)
            rec.completed_tasks = len(tasks.filtered(lambda t: t.status == 'done'))
            rec.completion_rate = (rec.completed_tasks / rec.number_of_tasks * 100) if rec.number_of_tasks else 0.0
            scored_tasks = tasks.filtered(lambda t: t.status == 'done')  # Include score = 0
            rec.average_score = sum(scored_tasks.mapped('feedback_score')) / len(scored_tasks) if scored_tasks else 0.0

            # Evaluate status based on score
            if rec.average_score >= 90:
                rec.status = 'excellent'
            elif rec.average_score >= 70:
                rec.status = 'good'
            else:
                rec.status = 'needs_improvement'
