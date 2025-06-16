from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PartnerUpdateWizard(models.TransientModel):
    _name = 'partner.update.wizard'
    _description = 'Partner Update Wizard'

    partner_id = fields.Many2one('res.partner', string="Partner", readonly=True)
    name = fields.Char("Name", required=True)
    vat = fields.Char("VAT", required=True)

    @api.constrains('vat')
    def _check_vat_format(self):
        for rec in self:
            vat = rec.vat or ''
            if not (len(vat) == 15 and vat.startswith('3') and vat.endswith('3') and vat.isdigit()):
                raise ValidationError("VAT must be 15 digits, start with 3, end with 3.")

    def action_update_partner(self):
        self.ensure_one()
        if self.partner_id:
            self.partner_id.write({
                'name': self.name,
                'vat': self.vat,
            })
