import logging
import re

from odoo import http
from odoo.http import request
from odoo import http, SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo import fields


class Google_Map(http.Controller):

    @http.route(['/google_cred_customer'], type='json', auth="public")
    def google_cred(self, **kwargs):
        #TODO find a way to current company not request.env.company becasue it gets the company from user not the active one
        company_id = request.env['res.company'].browse(2)
        return {
            'res_partner_use_gmap': company_id.res_partner_use_gmap,
        }

    @http.route(['/set_current_location_name_contact/'], type='json', auth="public")
    def set_current_location_name_contact(self, **post):
        active_id = post.get('active_id')
        location_name = post.get('location_name')
        addres_component_length = post.get('addres_component_length')
        address = post.get('address')
        latitude = post.get('latitude')
        longitude = post.get('longitude')
        get_partner_rec = request.env['res.partner'].sudo().browse(int(active_id))
        get_partner_rec.write({
            'location_name': location_name,
            'partner_latitude': latitude, 
            'partner_longitude': longitude,
             'date_localization': fields.Datetime.now()
        })
        if addres_component_length and address:
            addres_component_length = len(address)
            partner_address = {
                'street': False,
                'street2': False,
                'city': False,
                'state_id': False,
                'country_id': False,
                'zip': False,
                'location_name': location_name,
                'partner_latitude': latitude,
                'partner_longitude': longitude,
                'date_localization': fields.Datetime.now()
            }
            state_id = False
            country_id = False

            for i in range(addres_component_length):
                types = address[i].get('types', [])
                long_name = address[i].get('long_name', False)
                
                if 'street_number' in types:
                    partner_address['street'] = (partner_address['street'] or '') + ' ' + long_name
                elif 'route' in types:
                    partner_address['street'] = long_name
                elif 'premise' in types:
                    partner_address['street2'] = long_name
                elif 'locality' in types and not partner_address['city']:
                    partner_address['city'] = long_name
                elif 'administrative_area_level_1' in types:
                    state_id = request.env['res.country.state'].with_context(lang='ar_001').search([
                        ('name', '=ilike', long_name)
                    ], limit=1)
                    
                    if not state_id:
                        state_id = request.env['res.country.state'].with_context(lang='en_US').search([
                            ('name', '=ilike', long_name)
                        ], limit=1)
                        
                    partner_address['state_id'] = state_id.id or False
                elif 'country' in types:
                    country_id = request.env['res.country'].search([('id', '=', 192)])
                    partner_address['country_id'] = country_id.id or False
                elif 'postal_code' in types:
                    partner_address['zip'] = long_name

            # Parse `location_name` for missing street or street2
            location_list = location_name.split(', ')
            if not partner_address['street'] and location_list:
                partner_address['street'] = location_list[0]
            if not partner_address['street2'] and len(location_list) > 1:
                partner_address['street2'] = location_list[1]
            
            if partner_address and get_partner_rec:
                get_partner_rec.update(partner_address)


        # if addres_component_length and address:
        #     addres_component_length = len(address)
        #     partner_address = {
        #         'street': False,
        #         'street2': False,
        #         'city': False,
        #         'state_id': False,
        #         'country_id': False,
        #         'zip': False,
        #         'location_name': location_name,
        #         'partner_latitude': latitude,
        #         'partner_longitude': longitude,
        #         'date_localization': fields.Datetime.now()
        #     }
        #     state_id = False
        #     country_id = False

        #     for i in range(addres_component_length):
        #         types = address[i].get('types', [])
        #         long_name = address[i].get('long_name', False)
        #         if 'administrative_area_level_3' in types:
        #             partner_address.update({'city': long_name})
        #         elif 'locality' in types:
        #             if 'administrative_area_level_3' not in types:
        #                 partner_address.update({'city': long_name})
        #         elif 'administrative_area_level_1' in types:
        #             state_id = request.env['res.country.state'].search([('name', '=ilike', long_name)])
        #             partner_address.update({'state_id': state_id.id or False})
        #         elif 'locality' in types:
        #             if 'administrative_area_level_1' not in types:
        #                 state_id = request.env['res.country.state'].search([('name', '=ilike', long_name)])
        #                 partner_address.update({'state_id': state_id.id or False})
        #         elif 'country' in types:
        #             country_id = request.env['res.country'].search([('name', '=ilike',long_name)])
        #             partner_address.update({'country_id': country_id.id or False})
        #         elif 'locality' in types:
        #             if 'country' not in types:
        #                 country_id = request.env['res.country'].search([('name', '=ilike', long_name)])
        #                 partner_address.update({'country_id': country_id.id or False})
        #         elif 'postal_code' in types:
        #             partner_address.update({'zip': long_name})
        #         elif 'plus_code' in types:
        #             partner_address.update({'street': long_name})

        #     location_list = location_name.split(', ')
        #     if partner_address['city'] and partner_address['city'] in location_list:
        #         index = location_list.index(partner_address['city'])
        #         if index:
        #             location_list.pop(index)
        #     if partner_address['country_id']:
        #         country = request.env['res.country'].browse(partner_address['country_id']).name
        #         if country and country in location_list:
        #             index1 = location_list.index(country)
        #             if index1:
        #                 location_list.pop(index1)
        #     if location_list:
        #         remove_state = location_list.pop(-1)
        #     if location_list[:2]:
        #         partner_address.update({'street': ', '.join(location_list[:2])})
        #     if location_list[2:]:
        #         partner_address.update({'street2': ', '.join(location_list[2:])})

        #     if partner_address and get_partner_rec:
        #         get_partner_rec.update(partner_address)
                # get_partner_rec.write({
                #                             'street': partner_address.get('street'),
                #                             'street2': partner_address.get('street2'),
                #                             'city': partner_address.get('city'),
                #                             'state_id': partner_address.get('state_id'),
                #                             'zip': partner_address.get('zip'),
                #                             'country_id': partner_address.get('country_id'),
                #                             'location_name': location_name,
                #                             'partner_latitude': latitude,
                #                             'partner_longitude': longitude,
                #                             'date_localization': fields.Datetime.now()
                #                          })

        return True