from odoo import models, fields, api
from odoo.exceptions import UserError

class PerformanceReview(models.Model):
    _name = 'performance.review'
    _inherit = ['mail.thread']
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
    accepted = fields.Boolean(string="Accepted", tracking=True)
    refused = fields.Boolean(string="Refused", tracking=True)
    status_message = fields.Char(string="Status Message", compute="_compute_status_message")

    @api.depends('average_score')
    def _compute_status(self):
        for rec in self:
            if rec.average_score >= 90:
                rec.status = 'excellent'
            elif rec.average_score >= 70:
                rec.status = 'good'
            else:
                rec.status = 'needs_improvement'

    @api.depends('status')
    def _compute_status_message(self):
        for rec in self:
            if rec.status == 'excellent':
                rec.status_message = "Excellent performance. The employee deserves a bonus."
            elif rec.status == 'good':
                rec.status_message = "Good performance. Keep motivating the employee."
            elif rec.status == 'needs_improvement':
                rec.status_message = "Needs improvement. Consider coaching or training."
            else:
                rec.status_message = ""

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

    def action_accept_review(self):
        for rec in self:
            if rec.refused or rec.accepted:
                raise UserError("This review has already been accepted or refused.")
            rec.accepted = True  # ✅ mark it as accepted
            if rec.average_score >= 90:
                # Suggest creating a bonus
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Create Bonus',
                    'res_model': 'hr.bonus',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'default_date' : rec.review_date,
                        'default_employee_ids': [
                        (0, 0, {
                            'employee_id': rec.employee_id.id,
                            'email': rec.employee_id.work_email or rec.employee_id.user_id.email or ''
                        })
                    ],
                        'default_review_id': rec.id,
                        'default_reason': ('Excellent performance review'),
                    }
                }
            else:
                if rec.average_score < 70:
                    # Suggest creating a sanction
                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'Create Sanction',
                        'res_model': 'sanctions.procedures',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_date': rec.review_date,
                            'default_employee': rec.employee_id.id,
                            'default_review_id': rec.id,
                            'default_reason': ('Low performance review score'),
                        }
                    }
                    # No bonus/sanction if score is between 70-89
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': "Review Accepted",
                            'message': "Review accepted successfully. No bonus or sanction needed.",
                            'type': 'success',
                        }
                    }

    def action_refuse_review(self):
        for rec in self:
            if rec.refused or rec.accepted:
                raise UserError("This review has already been accepted or refused.")
            if 70 <= rec.average_score < 100:
                rec.refused = True  # Optional tracking field
                rec.message_post(body="❌ This review has been marked as refused .")
                raise UserError("❌ Marked as Refused. No further action required.")
