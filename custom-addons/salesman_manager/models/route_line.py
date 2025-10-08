from odoo import models, fields, api


class RouteLine(models.Model):
    _inherit = 'route.line'

    #This domain shows all customers whose record was created before (the date of lunching the deferred sales))OR whose status_contact is either “accepted” or “rejected.”
    #    cust_tree_ids = fields.One2many(domain=['|', ('create_date', '<', '2025-08-08 00:00:00'), ('status_contact', 'in', ['accepted', 'rejected'])], string='العملاء')
    cust_tree_ids = fields.One2many( string='العملاء')
    is_later = fields.Boolean(
        related='cust_tree_ids.is_later',
        store=True,
        readonly=False,
        string='Is Later',
        index=True,
    )




class Chatterr(models.Model):
    _name = 'route.line'
    _inherit = ['route.line', 'mail.thread', 'mail.activity.mixin']
