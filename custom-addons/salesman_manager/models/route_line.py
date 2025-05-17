from odoo import models, fields, api


class RouteLine(models.Model):
    _name = 'route.line'
    _inherit = ['route.line', 'mail.thread', 'mail.activity.mixin']

    #for changing the string name
    active_weekly_ref = fields.Char(string="Weekly Reference", compute='_compute_weekly_ref', store=False)


    @api.model
    def default_get(self, fields):
        rec = super(RouteLine, self).default_get(fields)
        print("self.env.context.==================",self.env.context)
        active_model = self.env.context.get('active_model')
        
        return rec

    def _compute_weekly_ref(self):
        for rec in self:
            print("weekly context=====================",self.env.context)
            rec.active_weekly_ref = self.env.context.get('active_weekly_ref')


    
