# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_zatca = fields.Boolean(related="company_id.parent_is_zatca")
    building_no = fields.Char('Building Number', help="https://splonline.com.sa/en/national-address-1/")
    additional_no = fields.Char('Additional Number', help="https://splonline.com.sa/en/national-address-1/")
    district = fields.Char('District')
    country_id_name = fields.Char(related="country_id.name")
    # vat = fields.Char(help="|) VAT registration number (if applicable) for the buyer and in case the buyer "
    #                        "is part of a VAT group then the VAT group Registration number should be entered."
    #                        "||) In case of tax invoice, "
    #                        "1) Not mandatory for export invoices. "
    #                        "2) Not Mandatory for internal supplies")
    # bt_46-1 (BR-KSA-14)
    buyer_identification = fields.Selection([('TIN', 'Tax Identification Number'),
                                             ('CRN', 'Commercial Registration number'),
                                             ('MOM', 'Momrah license'), ('MLS', 'MHRSD license'), ('700', '700 Number'),
                                             ('SAG', 'MISA license'), ('NAT', 'National ID'), ('GCC', 'GCC ID'),
                                             ('IQA', 'Iqama Number'), ('PAS', 'Passport ID'), ('OTH', 'Other OD')],
                                            string="Buyer Identification",
                                            help="|) required only if buyer is not VAT registered."
                                                 "||) In case of multiple commercial registrations, the seller should "
                                                 "fill the commercial registration of the branch in respect of which "
                                                 "the Tax Invoice is being issued.")
    # bt_46 (BR-KSA-14)
    buyer_identification_no = fields.Char(string="Buyer Identification Number (Other buyer ID)",
                                          help="|) required only if buyer is not VAT registered."
                                               "||) In case of multiple commercial registrations, the seller should "
                                               "fill the commercial registration of the branch in respect of which "
                                               "the Tax Invoice is being issued.")
# reports invoice fields
    building_no = fields.Char('Building No')
    additional_no = fields.Char('Additional No')
    other_seller_id = fields.Char('Other Seller Id')
    
   
   
    @api.constrains('zip')
    def constrains_brksa64(self):
        for record in self:
            # BR-KSA-67
            if record.company_id and record.is_zatca:
                zip = record.company_id.sanitize_int(record.zip)
                if (record.country_id.id and record.country_id.code == 'SA' and
                        (not zip or len(str(zip)) != 5 or not zip.isdigit())):
                    raise exceptions.ValidationError(_("zip must be exactly 5 digits in case of SA"))

    def write(self, vals):
        vals_dict = [vals] if type(vals) == dict else vals
        sanitize = self[0].company_id.sanitize_int if self else self.company_id.sanitize_int
        for val_dict in vals_dict:
            if 'vat' in val_dict:
                val_dict['vat'] = sanitize(val_dict['vat'])
            if 'building_no' in val_dict:
                val_dict['building_no'] = sanitize(val_dict['building_no'])
            if 'additional_no' in val_dict:
                val_dict['additional_no'] = sanitize(val_dict['additional_no'])
            if 'zip' in val_dict:
                val_dict['zip'] = sanitize(val_dict['zip'])
        res = super(ResPartner, self).write(vals)
        # BR-KSA-40
        for record in self:
            if record.company_id and record.is_zatca:
                if record.vat and record.country_id.id and record.country_id.code == 'SA':
                    if len(str(record.vat)) != 15:
                        raise exceptions.ValidationError(_("Vat must be exactly 15 digits."))
                    if str(record.vat)[0] != '3' or str(record.vat)[-1] != '3':
                        raise exceptions.ValidationError(_("Vat must start/end with 3."))
        return res
