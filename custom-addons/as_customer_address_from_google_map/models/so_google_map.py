# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    location_name = fields.Char("Location Name")

    def select_destination_loc(self):
        if not self.env.company.res_partner_use_gmap:
            raise ValidationError(_("Please Configure API Key"))
        return {
                    'name': 'Contacts',
                    'type': 'ir.actions.client',
                    'tag': 'partner_select_current_point',
                    'target': 'new',
                }