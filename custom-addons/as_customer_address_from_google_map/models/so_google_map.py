# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    location_name = fields.Char("Location Name")


    def write(self, vals):
        for rec in self:
            new_vals = vals.copy()

            if 'partner_latitude' in new_vals and rec.partner_latitude:
                new_vals.pop('partner_latitude')
            if 'partner_longitude' in new_vals and rec.partner_longitude:
                new_vals.pop('partner_longitude')

            super(ResPartner, rec).write(new_vals)

        return True

       

    

    def select_destination_loc(self):
        if not self.env.company.res_partner_use_gmap:
            raise ValidationError(_("Please Configure API Key"))
        return {
                    'name': 'Contacts',
                    'type': 'ir.actions.client',
                    'tag': 'partner_select_current_point',
                    'target': 'new',
                }