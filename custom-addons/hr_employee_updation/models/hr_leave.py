

from odoo import models, fields, api

class HrLeave(models.Model):
   
    _inherit = 'hr.leave'

    @api.model
    def default_get(self, fields_list):
        defaults = super(HrLeave, self).default_get(fields_list)
        defaults = self._default_get_request_dates(defaults)
        defaults['holiday_status_id'] = False
        return defaults