# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions, _

arabic_tax = {
    "Financial services mentioned in Article 29 of the VAT Regulations": "الخدمات المالية",
    "Life insurance services mentioned in Article 29 of the VAT Regulations": "عقد تأمين على الحياة",
    "Real estate transactions mentioned in Article 30 of the VAT Regulations": "التوريدات العقارية المعفاة من الضريبة",
    "Export of goods": "صادرات السلع من المملكة",
    "Export of services": "صادرات الخدمات من المملكة",
    "The international transport of Goods": "النقل الدولي للسلع",
    "international transport of passengers": "النقل الدولي للركاب",
    "services directly connected and incidental to a Supply of international passenger transport": "الخدمات المرتبطة مباشرة أو عرضيًا بتوريد النقل الدولي للركاب",
    "Supply of a qualifying means of transport": "توريد وسائل النقل المؤهلة",
    "Any services relating to Goods or passenger transportation, as defined in article twenty five of these Regulations":
        "الخدمات ذات الصلة بنقل السلع أو الركاب، وفقًا للتعريف الوارد بالمادة الخامسة والعشرين من الالئحة التنفيذية لنظام ضريبة القيامة المضافة",
    "Medicines and medical equipment": "األدوية والمعدات الطبية",
    "Qualifying metals": "المعادن المؤهلة",
    "Private education to citizen": "الخدمات التعليمية الخاصة للمواطنين",
    "Private healthcare to citizen": "الخدمات الصحية الخاصة للمواطنين",
    "supply of qualified military goods": "توريد السلع العسكرية المؤهلة",
}


class AccountTax(models.Model):
    _inherit = 'account.tax'

    is_zatca = fields.Boolean(related="company_id.parent_is_zatca")
    classified_tax_category = fields.Selection([("E", "E"), ("S", "S"), ("Z", "Z"),
                                                ("O", "O")], 'Tax Category', default="S", required=1)
    tax_exemption_selection = fields.Selection([
        # Tax Category E
        ("VATEX-SA-29", "Financial services mentioned in Article 29 of the VAT Regulations"),
        ("VATEX-SA-29-7", "Life insurance services mentioned in Article 29 of the VAT Regulations"),
        ("VATEX-SA-30", "Real estate transactions mentioned in Article 30 of the VAT Regulations"),
        # Tax Category Z
        ("VATEX-SA-32", "Export of goods"),
        ("VATEX-SA-33", "Export of services"),
        ("VATEX-SA-34-1", "The international transport of Goods"),
        ("VATEX-SA-34-2", "international transport of passengers"),
        ("VATEX-SA-34-3", "services directly connected and incidental to a Supply of international passenger transport"),
        ("VATEX-SA-34-4", "Supply of a qualifying means of transport"),
        ("VATEX-SA-34-5", "Any services relating to Goods or passenger transportation, as defined in article twenty five of these Regulations"),
        ("VATEX-SA-35", "Medicines and medical equipment"),
        ("VATEX-SA-36", "Qualifying metals"),
        ("VATEX-SA-EDU", "Private education to citizen"),
        ("VATEX-SA-HEA", "Private healthcare to citizen"),
        ("VATEX-SA-MLTRY", "supply of qualified military goods"),
        # Tax Category O
        ("VATEX-SA-OOS", "Reason is free text, to be provided by the taxpayer on case to case basis. "
                         "(Tax Category O)"),
    ],
        string="Tax exemption Reason Text")
    tax_exemption_code = fields.Char("Tax exemption Reason Code", readonly=1)
    tax_exemption_text = fields.Char("Tax exemption Reason Text ", readonly=0)

    @api.onchange('classified_tax_category')
    def _onchange_classified_tax_category(self):
        if self.classified_tax_category == 'O':
            self.tax_exemption_selection = 'VATEX-SA-OOS'
            self.tax_exemption_text = None
        else:
            self.tax_exemption_text = None
            self.tax_exemption_code = None
            self.tax_exemption_selection = None

    @api.onchange('tax_exemption_selection')
    def _onchange_tax_exemption_text(self):
        if self.tax_exemption_selection:
            if self.classified_tax_category == 'O':
                if self.tax_exemption_selection not in ['VATEX-SA-OOS']:
                    self.classified_tax_category = None
            elif self.classified_tax_category == 'E':
                if self.tax_exemption_selection not in ['VATEX-SA-29', 'VATEX-SA-29-7', 'VATEX-SA-30']:
                    raise exceptions.ValidationError(_("For Category E, reason code should be in") + " ["
                                                                                                     "'Financial services mentioned in Article 29 of the VAT Regulations',"
                                                                                                     "'Life insurance services mentioned in Article 29 of the VATRegulations',"
                                                                                                     "'Real estate transactions mentioned in Article 30 of the VAT Regulations']")
            elif self.classified_tax_category == 'Z':
                if self.tax_exemption_selection in ['VATEX-SA-29', 'VATEX-SA-29-7', 'VATEX-SA-30', 'VATEX-SA-OOS']:
                    raise exceptions.ValidationError(_("For Category E, reason code should not be in") + " ["
                                                                                                         "'Financial services mentioned in Article 29 of the VAT Regulations',"
                                                                                                         "'Life insurance services mentioned in Article 29 of the VATRegulations',"
                                                                                                         "'Real estate transactions mentioned in Article 30 of the VAT Regulations',"
                                                                                                         "'Reason is free text, to be provided by the taxpayer on case to case basis.']")
            self.tax_exemption_code = self.tax_exemption_selection
            if self.classified_tax_category != 'O':
                self.tax_exemption_text = arabic_tax[self.env['ir.model.fields.selection'].search([('value', '=', self.tax_exemption_selection)]).name]
            else:
                self.tax_exemption_text = None

    # classified_tax_category','not in', ['E', 'Z', 'O']
    def write(self, vals):
        res = super(AccountTax, self).write(vals)
        for record in self:
            if record.classified_tax_category in ['E', 'Z', 'O'] and record.amount != 0:
                raise exceptions.ValidationError(_('Tax Amount must be 0 in case of category') + ' ' + str(record.classified_tax_category) + ' .')
        return res
