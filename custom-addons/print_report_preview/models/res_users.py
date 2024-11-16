from odoo import api, fields, models, tools, _

class ResUsers(models.Model):
    _inherit = "res.users"

    report_preview = fields.Boolean(string="Report Preview", default=True)
    report_automatic_printing = fields.Boolean(srting="Report Automatic printing")   

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['report_preview', 'report_automatic_printing']

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['report_preview', 'report_automatic_printing']


    def report_preview_reload(self):
        return {
            "type": "ir.actions.client",
            "tag": "reload_context"
        }
    
    @api.model
    def action_get_print_report_preview(self):
        if self.env.user:
            return self.env['ir.actions.act_window']._for_xml_id('print_report_preview.action_simple_print_report_preview')