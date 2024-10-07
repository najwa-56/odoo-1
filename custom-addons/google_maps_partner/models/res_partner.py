# -*- coding: utf-8 -*-
######################################################################################################
#
# Copyright (C) B.H.C. sprl - All Rights Reserved, http://www.bhc.be
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied,
# including but not limited to the implied warranties
# of merchantability and/or fitness for a particular purpose
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
######################################################################################################
from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def open_map(self):
        for partner in self:
            url = "http://maps.google.com/maps?oi=map&q="
            if partner.street:
                url += partner.street.replace(' ', '+')
            if partner.city:
                url += '+'+partner.city.replace(' ', '+')
            if partner.state_id:
                url += '+'+partner.state_id.name.replace(' ', '+')
            if partner.country_id:
                url += '+'+partner.country_id.name.replace(' ', '+')
            if partner.zip:
                url += '+'+partner.zip.replace(' ', '+')
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': url
        }
