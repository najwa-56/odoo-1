from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PartnerUpdateWizard(models.TransientModel):
    _name = 'partner.update.wizard'
    _description = 'Partner Update Wizard'

    partner_id = fields.Many2one('res.partner', string="Partner", readonly=True)
    name = fields.Char("Name", required=True)
    vat = fields.Char("VAT", required=True)
    buyer_identification_no = fields.Char(string="CRN")

    @api.constrains('vat')
    def _check_vat_format(self):
        for rec in self:
            vat = rec.vat or ''
            if not (len(vat) == 15 and vat.startswith('3') and vat.endswith('3') and vat.isdigit()):
                raise ValidationError("VAT must be 15 digits, start with 3, end with 3.")

    def action_update_partner(self):
        self.ensure_one()
        if self.partner_id:
            data = {
                'name': self.name,
                'vat': self.vat,
            }
            if self.buyer_identification_no:
                data.update({
                    'buyer_identification': 'CRN',
                    'buyer_identification_no': self.buyer_identification_no,
                })
            self.partner_id.write(data)
