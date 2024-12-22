# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


class DropboxAuthorizationCodeWizard(models.TransientModel):
    _name = 'dropbox.auth.refresh.token.wiz'
    _description = "Dropbox Authorization Code Wizard"

    dropbox_uri = fields.Text()
    dropbox_authorization_code = fields.Char(string='Authorization Code')

    def action_confirm(self):
        if not self.dropbox_authorization_code:
            raise UserError(_("Authorization Code is required"))
        try:
            bckup = self.env['database.backup'].sudo().search([('id', '=', self.env.context.get('backup_id'))])
            bckup.write({'dropbox_authorization_code': self.dropbox_authorization_code, })
        except Exception as e:
            raise UserError(str(e))
            exit(1)
