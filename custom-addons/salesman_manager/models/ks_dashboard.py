from odoo import models, fields, api


class KsDashboardNinja(models.Model):
    _inherit = 'ks_dashboard_ninja.board'

    salesman = fields.Many2one('res.partner', string="المندوب",
                               help="The partner associated with the salesperson")
    employee_id = fields.Many2one('hr.employee', string="الموظف المندوب",
                                  help="Direct reference to the employee record")

    @api.model
    def create(self, vals):
        """Override create to link dashboard to employee if salesman is provided"""
        res = super(KsDashboardNinja, self).create(vals)
        if res.salesman and not res.employee_id:
            employee = self.env['hr.employee'].search([('user_partner_id', '=', res.salesman.id)], limit=1)
            if employee:
                res.employee_id = employee.id
        return res

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """When employee is set, automatically set the salesman"""
        for record in self:
            if record.employee_id and record.employee_id.user_partner_id and not record.salesman:
                record.salesman = record.employee_id.user_partner_id.id
