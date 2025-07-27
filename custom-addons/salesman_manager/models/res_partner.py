# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    #_order = 'sequence'



    visit = fields.Many2many(comodel_name='daily.visit', string="Visits", index=True, copy=False)
    daily_visit_ids = fields.One2many('daily.visit','partner_id',string='Daily Visits')
    specific_visit_id = fields.Many2one('daily.visit',string='Specific Visit',compute='_compute_specific_visit',)
    
    status = fields.Selection([
        ('not_yet', 'Not Yet'),
        ('visit', 'Visit'),
        ('sale', 'Sale'),
    ], string="Status", default='not_yet', compute='_compute_specific_visit', store=False)


    #--------- adjustment --------------------------------------
    status_contact = fields.Selection( [
        ('waiting', 'قيد الانتظار'),
        ('accepted', 'مصدق'),
        ('rejected', 'مرفوض'),
    ], string='الحالة', default='waiting' )

    is_later = fields.Boolean( 'is_later' )

    def action_accept_partner (self):
        for rec in self:
            rec.status_contact = 'accepted'
            rec.is_later = True

    def action_reject_partner (self):
        for rec in self:
            rec.status_contact = 'rejected'
            rec.is_later = False

    #---------------------------------------------------------------------------------------------------------
    #once you created a new visit it is should be saved in field specific_visit_id for a spicific weekly route
    #---------------------------------------------------------------------------------------------------------
    @api.depends('daily_visit_ids')
    def _compute_specific_visit(self):
        for rec in self:
            ref = None
            active_weekly_ref = self.env.context.get('active_weekly_ref') 
            if active_weekly_ref:
                weekly_route = self.env['weekly.routs'].browse(active_weekly_ref)
                ref = weekly_route.reference

            if ref:
                visit = rec.daily_visit_ids.filtered(lambda v: v.ref == ref)
                rec.specific_visit_id = visit[:1] if visit else False
                if visit:
                    if  visit[0].is_it_sold:
                        rec.status = 'sale'
                    else:
                        rec.status = 'visit' 
                else:
                    rec.status = 'not_yet'
            else:
                rec.specific_visit_id = False
                rec.status = 'not_yet'


    def action_open_specific_visit (self):
        self.ensure_one()
        if not self.specific_visit_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': 'Daily Visit',
            'res_model': 'daily.visit',
            'view_mode': 'form',
            'res_id': self.specific_visit_id.id,
            'target': 'current',
        }

    #---------------------------------------------------------------------------------------------
    #This code is used to set the status of a partner to either "visit" or "sale"
    # based on whether a related daily.visit record has the is_it_sold field set to True or False
    #---------------------------------------------------------------------------------------------
    def _update_status_from_visit (self, is_it_sold):
        for partner in self:
            if is_it_sold is True:
                partner.status = 'sale'
            elif is_it_sold is False:
                partner.status = 'visit'
            else:
                partner.status = 'not_yet'


    #---------------------------------------------------------------------------------------------
    # once you click on button action_open_daily_visit it should be open Daily Visit form and linke
    #it with the last weekly rout
    #---------------------------------------------------------------------------------------------
    def action_open_daily_visit (self):
        self.ensure_one()

        # Find the first weekly route record for the current user (example ordering by creation_date desc)
        first_route = self.env['weekly.routs'].search(
            [('user_id', '=', self.env.uid)], order='creation_date desc, id desc', limit=1
        )
        print("------------------------------",first_route.reference)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Daily Visit',
            'res_model': 'daily.visit',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.id,
                'default_weekly_route_id': first_route.id if first_route else False,
                'default_ref': first_route.reference,
            },
        }


    #--------------------------------------------
    #to Update Partner Info
    #--------------------------------------------
    def open_update_partner_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Update Partner Info',
            'res_model': 'partner.update.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_name': self.name,
                'default_vat': self.vat,
            },
        }

