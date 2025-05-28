from collections import defaultdict
from odoo import api, fields, models

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    complete_contact_address = fields.Char(compute='_compute_complete_address', store=True)

    @api.model
    def write_latitude_longitude(self, partner_id):
        return True
        lat = self.env.context.get('partner_latitude')
        lng = self.env.context.get('partner_longitude')
        if partner_id and lat and lng:
            partner = self.env['res.partner'].sudo().search([('id', '=', int(partner_id))])
            partner.sudo().write({
                'partner_latitude': lat,
                'partner_longitude': lng,
            })
        return True

    @api.depends('street', 'zip', 'city', 'country_id')
    def _compute_complete_address(self):
        for record in self:
            record.complete_contact_address = ''
            if record.street:
                record.complete_contact_address += record.street + ', '
            if record.zip:
                record.complete_contact_address += record.zip + ' '
            if record.city:
                record.complete_contact_address += record.city + ', '
            if record.state_id:
                record.complete_contact_address += record.state_id.name + ', '
            if record.country_id:
                record.complete_contact_address += record.country_id.name
            record.complete_contact_address = record.complete_contact_address.strip().strip(',')
