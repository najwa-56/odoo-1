from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TaskNameMassReassignWizard(models.TransientModel):
    _name = 'task.name.reassign.wizard'
    _description = 'Mass Update Next Assigned Employee'

    employee_id = fields.Many2one('hr.employee', string="New Default Next Employee", required=True)

    def action_mass_update_next_employee(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            raise ValidationError("No task templates selected.")
        task_names = self.env['task.name'].browse(active_ids)
        for rec in task_names:
            rec.default_employee_id = self.employee_id.id
        return {'type': 'ir.actions.act_window_close'}
