# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    #_order = 'sequence'

    #adding map from google_maps_partner to rout line
    #def open_map(self):
    #    super(ResPartner, self).open_map()

    visit = fields.Many2many(comodel_name='daily.visit', string="الزيارات", ondelete='cascade', index=True, copy=False)
    weekly_route_ids = fields.Many2many( 'weekly.routs.line', string="Weekly Routes" )

    #This code is used to set the status of a partner to either "visit" or "sale"
    # based on whether a related daily.visit record has the is_it_sold field set to True or False

    status = fields.Selection( [
        ('not_yet', 'لاشيء'),
        ('visit', 'تمت الزيارة'),
        ('sale', 'تم البيع'),
    ], string="Status", default='not_yet' )

    def _update_status_from_visit (self, is_it_sold):
        for partner in self:
            if is_it_sold is True:
                partner.status = 'sale'
            elif is_it_sold is False:
                partner.status = 'visit'
            else:
                partner.status = 'not_yet'

    # Reference to the most recent daily.visit
    last_daily_visit_id = fields.Many2one('daily.visit', string='Last Visit')

    # Make sure the status is updated based on the latest visit
    @api.model
    def create(self, vals):
        partner = super(ResPartner, self).create(vals)
        if partner.last_daily_visit_id:
            partner._update_status_from_visit(partner.last_daily_visit_id.is_it_sold)
        return partner
    def action_open_daily_visit (self):
        self.ensure_one()

        # Just open the visit form without creating it or assigning status directly
        return {
            'type': 'ir.actions.act_window',
            'name': 'Daily Visit',
            'res_model': 'daily.visit',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.id,
            },
        }


    #we inhirit action_view_partner_invoices function and we add a new domain which is 'payment_state', '!=', 'paid'
    def action_view_partner_invoices_custom(self):
        self.ensure_one()
        action = super(ResPartner, self).action_view_partner_invoices()

        # Add your custom domain here
        custom_domain = [('payment_state', '!=', 'paid')]

        # Check if 'domain' key exists in action and add the custom domain
        if action.get('context'):
            action['context'] = dict(action['context'])
            if 'search_default_partner_id' in action['context']:
                action['context'].pop('search_default_partner_id')
        else:
            action['context'] = {}

        if 'domain' in action['context']:
            action['context']['domain'].extend(custom_domain)
        else:
            action['context']['domain'] = custom_domain

        return action








