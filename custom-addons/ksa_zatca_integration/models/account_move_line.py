from odoo import api, fields, models, exceptions, _
from decimal import Decimal
import uuid


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_zatca = fields.Boolean(related="move_id.is_zatca")
    zatca_id = fields.Char(string='Zatca Id', copy=False)

    # BR-KSA-DEC-01 for BT-138 only
    @api.onchange('discount')
    def zatca_onchange_discount(self):
        for res in self:
            if res.is_zatca:
                res.discount = 100 if res.discount > 100 else (0 if res.discount < 0 else res.discount)

    #BR-KSA-F-04
    @api.onchange('quantity')
    def zatca_BR_KSA_F_04(self):
        self.quantity = 0 if self.quantity < 0 else self.quantity
        self.price_unit = abs(self.price_unit)

    @api.onchange('tax_ids')
    def onchange_tax_ids(self):
        for record in self:
            if record.is_zatca:
                if len(record.tax_ids.ids) > 1:
                    raise exceptions.ValidationError(_("Only 1 tax can be applied per line."))
                if len(list(set(record.move_id.invoice_line_ids.tax_ids.filtered(lambda x: x.classified_tax_category == 'E').mapped('tax_exemption_selection')))) > 1 \
                        or \
                        len(list(set(record.move_id.invoice_line_ids.tax_ids.filtered(lambda x: x.classified_tax_category == 'Z').mapped('tax_exemption_selection')))) > 1 \
                        or \
                        len(list(set(record.move_id.invoice_line_ids.tax_ids.filtered(lambda x: x.classified_tax_category == 'O').mapped('tax_exemption_text')))) > 1:
                    raise exceptions.ValidationError(_("Multiple tax reasons for same tax group can't be applied in one invoice."))
                # if self.tax_ids.filtered(lambda x: x.invoice_line_id.tax_ids.tax_exemption_code)
                #     tax_exemption_text
