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
charge_reson_list = [
    ('AA', 'Advertising'), ('AAA', 'Telecommunication'), ('AAC', 'Technical modification'),
    ('AAD', 'Job-order production'), ('AAE', 'Outlays'), ('AAF', 'Off-premises'),
    ('AAH', 'Additional processing'), ('AAI', 'Attesting'), ('AAS', 'Acceptance'),
    ('AAT', 'Rush delivery'), ('AAV', 'Special construction'), ('AAY', 'Airport facilities'),
    ('AAZ', 'Concession'), ('ABA', 'Compulsory storage'), ('ABB', 'Fuel removal'),
    ('ABC', 'Into plane'), ('ABD', 'Overtime'), ('ABF', 'Tooling'), ('ABK', 'Miscellaneous'),
    ('ABL', 'Additional packaging'), ('ABN', 'Dunnage'), ('ABR', 'Containerisation'),
    ('ABS', 'Carton packing'), ('ABT', 'Hessian wrapped'), ('ABU', 'Polyethylene wrap packing'),
    ('ACF', 'Miscellaneous treatment'), ('ACG', 'Enamelling treatment'), ('ACH', 'Heat treatment'),
    ('ACI', 'Plating treatment'), ('ACJ', 'Painting'), ('ACK', 'Polishing'), ('ACL', 'Priming'),
    ('ACM', 'Preservation treatment'), ('ACS', 'Fitting'), ('ADC', 'Consolidation'),
    ('ADE', 'Bill of lading'), ('ADJ', 'Airbag'), ('ADK', 'Transfer'), ('ADL', 'Slipsheet'),
    ('ADM', 'Binding'), ('ADN', 'Repair or replacement of broken returnable package'),
    ('ADO', 'Efficient logistics'), ('ADP', 'Merchandising'), ('ADQ', 'Product mix'),
    ('ADR', 'Other services'), ('ADT', 'Pick-up'), ('ADW', 'Chronic illness'),
    ('ADY', 'New product introduction'), ('ADZ', 'Direct delivery'), ('AEA', 'Diversion'),
    ('AEB', 'Disconnect'), ('AEC', 'Distribution'), ('AED', 'Handling of hazardous cargo'),
    ('AEF', 'Rents and leases'), ('AEH', 'Location differential'), ('AEI', 'Aircraft refueling'),
    ('AEJ', 'Fuel shipped into storage'), ('AEK', 'Cash on delivery'),
    ('AEL', 'Small order processing service'), ('AEM', 'Clerical or administrative services'),
    ('AEN', 'Guarantee'), ('AEO', 'Collection and recycling'), ('AEP', 'Copyright fee collection'),
    ('AES', 'Veterinary inspection service'), ('AET', 'Pensioner service'),
    ('AEU', 'Medicine free pass holder'), ('AEV', 'Environmental protection service'),
    ('AEW', 'Environmental clean-up service'),
    ('AEX', 'National cheque processing service outside account area'),
    ('AEY', 'National payment service outside account area'),
    ('AEZ', 'National payment service within account area'), ('AJ', 'Adjustments'),
    ('AU', 'Authentication'), ('CA', 'Cataloguing'), ('CAB', 'Cartage'), ('CAD', 'Certification'),
    ('CAE', 'Certificate of conformance'), ('CAF', 'Certificate of origin'), ('CAI', 'Cutting'),
    ('CAJ', 'Consular service'), ('CAK', 'Customer collection'), ('CAL', 'Payroll payment service'),
    ('CAM', 'Cash transportation'), ('CAN', 'Home banking service'),
    ('CAO', 'Bilateral agreement service'), ('CAP', 'Insurance brokerage service'),
    ('CAQ', 'Cheque generation'), ('CAR', 'Preferential merchandising location'), ('CAS', 'Crane'),
    ('CAT', 'Special colour service'), ('CAU', 'Sorting'),
    ('CAV', 'Battery collection and recycling'), ('CAW', 'Product take back fee'),
    ('CD', 'Car loading'), ('CG', 'Cleaning'), ('CS', 'Cigarette stamping'),
    ('CT', 'Count and recount'), ('DAB', 'Layout/design'), ('DAD', 'Driver assigned unloading'),
    ('DL', 'Delivery'), ('EG', 'Engraving'), ('EP', 'Expediting'),
    ('ER', 'Exchange rate guarantee'), ('FAA', 'Fabrication'), ('FAB', 'Freight equalization'),
    ('FAC', 'Freight extraordinary handling'), ('FC', 'Freight service'),
    ('FH', 'Filling/handling'), ('FI', 'Financing'), ('GAA', 'Grinding'), ('HAA', 'Hose'),
    ('HD', 'Handling'), ('HH', 'Hoisting and hauling'), ('IAA', 'Installation'),
    ('IAB', 'Installation and warranty'), ('ID', 'Inside delivery'), ('IF', 'Inspection'),
    ('IR', 'Installation and training'), ('IS', 'Invoicing'), ('KO', 'Koshering'),
    ('L1', 'Carrier count'), ('LA', 'Labelling'), ('LAA', 'Labour'), ('LAB', 'Repair and return'),
    ('LF', 'Legalisation'), ('MAE', 'Mounting'), ('MI', 'Mail invoice'),
    ('ML', 'Mail invoice to each location'), ('NAA', 'Non-returnable containers'),
    ('OA', 'Outside cable connectors'), ('PA', 'Invoice with shipment'),
    ('PAA', 'Phosphatizing (steel treatment)'), ('PC', 'Packing'), ('PL', 'Palletizing'),
    ('RAB', 'Repacking'), ('RAC', 'Repair'), ('RAD', 'Returnable container'), ('RAF', 'Restocking'),
    ('RE', 'Re-delivery'), ('RF', 'Refurbishing'), ('RH', 'Rail wagon hire'), ('RV', 'Loading'),
    ('SA', 'Salvaging'), ('SAA', 'Shipping and handling'), ('SAD', 'Special packaging'),
    ('SAE', 'Stamping'), ('SAI', 'Consignee unload'), ('SG', 'Shrink-wrap'),
    ('SH', 'Special handling'), ('SM', 'Special finish'), ('SU', 'Set-up'), ('TAB', 'Tank renting'),
    ('TAC', 'Testing'), ('TT', 'Transportation - third party billing'),
    ('TV', 'Transportation by vendor'), ('V1', 'Drop yard'), ('V2', 'Drop dock'),
    ('WH', 'Warehousing'), ('XAA', 'Combine all same day shipment'), ('YY', 'Split pick-up'),
    ('ZZZ', 'Mutually defined'),
]


class AccountTax(models.Model):
    _inherit = 'account.tax'

    is_zatca = fields.Boolean(related="company_id.parent_is_zatca")
    classified_tax_category = fields.Selection([("E", "E"), ("S", "S"), ("Z", "Z"),
                                                ("O", "O")], 'Tax Category', default="S", required=True)
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
    tax_exemption_code = fields.Char("Tax exemption Reason Code", readonly=True)
    tax_exemption_text = fields.Char("Tax exemption Reason Text ", readonly=False)
    l10n_charge_reason = fields.Selection(charge_reson_list, string="Charge Reason Code")

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
                self.tax_exemption_text = arabic_tax[self.env['ir.model.fields.selection'].sudo()
                .search([('value', '=', self.tax_exemption_selection)]).name]
            else:
                self.tax_exemption_text = None

    # classified_tax_category','not in', ['E', 'Z', 'O']
    def write(self, vals):
        res = super(AccountTax, self).write(vals)
        for record in self:
            if record.classified_tax_category in ['E', 'Z', 'O'] and record.amount != 0:
                raise exceptions.ValidationError(_('Tax Amount must be 0 in case of category') + ' ' + str(record.classified_tax_category) + ' .')
        return res
