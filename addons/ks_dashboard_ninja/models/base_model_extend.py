# -*- coding: utf-8 -*-

from odoo import models, api


class BaseExtend(models.AbstractModel):
    _inherit = 'base'

    @api.model_create_multi
    def create(self, vals):
        recs = super(BaseExtend, self).create(vals)
        if 'ir.' not in self._name and 'bus.' not in self._name and self.env.user.has_group('base.group_user'):
            # items = self.env['ks_dashboard_ninja.item'].search(
            #     [['ks_model_id.model', '=', self._name]])
            # if items:
            # online_partners = self.env["bus.presence"].sudo().search([('status', '=', 'online')]).mapped('user_id.partner_id').ids
            # updates = [ for partner_id in online_partners]
            self.env['bus.bus']._sendone('ks_notification', 'Update: Dashboard Items', {'model': self._name})
        return recs

    def write(self, vals):
        recs = super(BaseExtend, self).write(vals)
        if 'ir.' not in self._name and 'bus.' not in self._name and self.env.user.has_group('base.group_user') and 'res.partner' not in self._name:
            # items = self.env['ks_dashboard_ninja.item'].search(
            #     [['ks_model_id.model', '=', self._name]])
            # if items:
            # online_partner = self.env["bus.presence"].search([('status', '=', 'online')]).mapped('user_id.partner_id').ids
            # updates = [[
            #     (self._cr.dbname, 'res.partner', partner_id),
            #     {'type': 'ks_notification', 'model': self._name},
            #     {'id': self.id}
            # ] for partner_id in online_partner]
            self.env['bus.bus']._sendone('ks_notification', 'Update: Dashboard Items', {'model': self._name})
        return recs