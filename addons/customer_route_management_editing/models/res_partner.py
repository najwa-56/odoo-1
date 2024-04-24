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

    #we inhirit action_view_partner_invoices function and we add a new domain which is 'payment_state', '!=', 'paid'
    """ 
    #version 16
    def action_view_partner_invoices_custom(self):
        self.ensure_one()
        action = super(ResPartner, self).action_view_partner_invoices()

        # Add your custom domain here
        custom_domain = [('payment_state', '!=', 'paid')]

        # Check if 'domain' key exists in action and add the custom domain
        if 'domain' in action:
            action['domain'].extend(custom_domain)
        else:
            action['domain'] = custom_domain

        return action
     """

    # version 17
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








