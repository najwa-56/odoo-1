from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    salesman_supervisor = fields.Many2one('res.partner', string="supervisor")

    #----------------------------------------------------------
    #Open the dashboard related to this salesman
    #----------------------------------------------------------
    def action_open_dashboard(self):

        self.ensure_one()
        # First try to find dashboard by employee's user_partner_id
        dashboard = self.env['ks_dashboard_ninja.board'].search([('salesman', '=', self.user_partner_id.id)], limit=1)

        # If not found, try to find dashboard by employee_id (direct link)
        if not dashboard:
            dashboard = self.env['ks_dashboard_ninja.board'].search([('employee_id', '=', self.id)], limit=1)

        if dashboard:
            return {
                'type': 'ir.actions.client',
                'name': dashboard.name,
                'tag': 'ks_dashboard_ninja',
                'params': {
                    'ks_dashboard_id': dashboard.id,
                },
                'target': 'current',
            }

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'لا توجد لوحة قيادة',
                'message': 'لا توجد لوحة قيادة لهذا المندوب.',
                'type': 'warning',
                'sticky': False,
            }
        }
