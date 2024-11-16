from odoo import models
from odoo.http import request

class Http(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        user = request.env.user
        result = super(Http, self).session_info()
        if self.env.user.has_group('base.group_user'):
            result['report_preview'] = user.report_preview
            result['report_automatic_printing'] = user.report_automatic_printing
        return result
