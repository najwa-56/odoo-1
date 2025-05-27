# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or
#    sell copies of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
#    OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import models, fields,api


class RouteLines(models.Model):
    """This class creates a model 'route.line' and adds fields"""
    _name = 'route.line'
    _description = 'Route Line'
    _rec_name = 'route'
    _order = 'sequence'

    sequence = fields.Integer(string='User Sequence',default=10)
    route = fields.Char(string='Routes', help="Route of corresponding"
                                              " route line.")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', default=lambda self: self.env.company)

    delivery_route_link_id = fields.Many2one('delivery.route',
                                             help="Delivery route of "
                                                  "corresponding delivery.")
    cust_tree_ids = fields.One2many('res.partner', 'location_id',
                                    string='Customers', help="Customer who has "
                                                             "selected "
                                                             "corresponding "
                                                             "route line seen "
                                                             "under route"
                                                             " line.")


    available_partner_ids = fields.Many2many(
        'res.partner',
        string='Add Existing Customers',
        domain="[('location_id', '=', False)]",
        help='Select existing customers to assign to this route'
    )

    @api.onchange('available_partner_ids')
    def _onchange_available_partner_ids(self):
        for partner in self.available_partner_ids:
            partner.location_id = self.id
        self.available_partner_ids = [(5, 0, 0)]  # clear the selection after assigning


    
    def action_add_customers(self):
        return {
            'name': 'Select Customers',
            'type': 'ir.actions.act_window',
            'res_model': 'select.customer.route.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_route_line_id': self.id,
            }
        }
    


    def action_create_customer(self):
        return {
            'name': 'Create Customer',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_location_id': self.id,
                'form_view_ref': 'base.view_partner_form',  # or your custom form
            }
        }