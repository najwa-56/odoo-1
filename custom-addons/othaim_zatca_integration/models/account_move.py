from odoo import api, fields, models, exceptions, _

import logging

from datetime import date
from datetime import datetime
from datetime import  timedelta



_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"


    
    pos_reference = fields.Char(string='Receipt Number')

    tax_line_missing = fields.Boolean('Missing Tax Line')

    def amount_word(self, amount , lang="ar_001"):
        return self.currency_id.with_context(lang=lang).amount_to_text(amount)
    

    

    def send_invoice_batch(self):
        today = date.today()
        two_days_ago = today - timedelta(days=2)
        recipients = ['abeersalh166@gmail.com','n4ajwa4@gmail.com']
        invoices = self.sudo().search([
            ('invoice_date', '>=', two_days_ago),
            ('invoice_date', '<=', today),
            ('move_type', '=', 'out_invoice'),            
            ('state', '=', 'posted'),
            ('l10n_sa_zatca_status', 'ilike', 'not'),
            ('partner_id.is_dolfin', '!=', True)])

        _logger.info(f"first invoices lenght (Invoices length: {len(invoices)}) *****************************")
        if not invoices:
            _logger.info(f"no left invoices lenght (Invoices length: {len(invoices)}) *****************************")
            return

        invoices = invoices.filtered(lambda inv: all(line.tax_ids for line in inv.invoice_line_ids))
        _logger.info(f"fitlered invoice Send To Zatca Errors (Invoice ID: {len(invoices)}) *****************************")
        
        
        for record in invoices:
            if not record.zatca_invoice_name or not record.zatca_compliance_invoices_api or \
                            record.zatca_status_code == '400':
                if not (record.partner_id.vat.startswith('3') and record.partner_id.vat.endswith('3')):
                    record.partner_id.vat = '300000000000003'
           
                if record.partner_id.is_company and len(record.partner_id.vat) != 15:
                    record.partner_id.vat = '300000000000003'
                
                if not record.partner_id.is_company and  record.partner_id.vat :
                    if len(record.partner_id.vat) != 15:
                        record.partner_id.vat = '300000000000003'
                        record.is_company = True

                if record.partner_id.is_company and  not record.partner_id.vat :
                    record.partner_id.vat = '300000000000003'

                if not record.partner_id.street:
                    record.partner_id.street = '/'
                
                if not record.partner_id.street2:
                    record.partner_id.street2 = '/'
                
                if not record.partner_id.city:
                    record.partner_id.city = '/'
                
                if not record.partner_id.district:
                    record.partner_id.district = '/'
                
                if not record.partner_id.country_id:
                    record.partner_id.country_id = 192
                
                if not record.partner_id.building_no:
                    record.partner_id.building_no = '1234'

                if not record.partner_id.zip:
                    record.partner_id.zip = '12345'

            

                if not record.partner_id.state_id:
                    state_id = self.env['res.country.state'].search([('code','=','BRU')],limit=1)
                    record.partner_id.state_id = state_id.id

                

                try:
                
                    for line in record.invoice_line_ids:
                        if '&' in line.name:
                            line.name = line.name.replace('&', 'و')
                    
                    if record.l10n_sa_invoice_type == 'Standard':
                        _logger.info(f"l10n_sa_invoice_type standard Send To Zatca (Invoice ID: {record.id})===================")
                        record.send_for_clearance()
                        self.env.cr.commit() 
                        record.message_post(body="invoice send to zatca from cron job")
                        
                    elif record.l10n_sa_invoice_type == 'Simplified':
                        _logger.info(f"l10n_sa_invoice_type standard Send To Zatca (Invoice ID: {record.id}) =============")
                        record.send_for_reporting()
                        self.env.cr.commit() 
                        record.message_post(body="invoice send to zatca from cron job")
                    
                    
                    
                            
                except Exception as e:
                    # Bypass errors.
                    _logger.info(f"Multi Send To Zatca Errors (Invoice ID: {record.id}) ***************************** :: {str(e)}")

                    mail_values = {
                        'subject': f"Sent Invoice To Zatca Processing Failed for {record.name}",
                        'body_html': f"<p><strong>Error:</strong> {str(e)}</p>",
                        'email_to': ','.join(recipients),
                        }
                    self.env['mail.mail'].create(mail_values).send()


        
      

        



    def resend_invoice(self):
        today = date.today()
        two_days_ago = today - timedelta(days=2)      
        invoices = self.sudo().search([
            ('invoice_date', '>=', two_days_ago),
            ('invoice_date', '<=', today),
            ('move_type', '=', 'out_invoice'),            
            ('state', '=', 'posted'),
            ('partner_id.is_dolfin', '!=', True),
            ('l10n_sa_zatca_status', 'ilike', 'error')
             
             
            
        ])

        if not invoices:
            return

        invoices = invoices.filtered(lambda inv: all(line.tax_ids for line in inv.invoice_line_ids))        
        
        for record in invoices:

            try:
            
                for line in record.invoice_line_ids:
                    if '&' in line.name:
                        line.name = line.name.replace('&', 'و')
                
                if record.l10n_sa_invoice_type == 'Standard':
                    record.create_xml_file()
                    record.invoices_clearance_single_api()
                    self.env.cr.commit() 
                    
                elif record.l10n_sa_invoice_type == 'Simplified':
                    record.create_xml_file()
                    record.invoices_reporting_single_api(no_xml_generate=0)
                    self.env.cr.commit() 
                
                
                
                        
            except Exception as e:
                # Bypass errors.
                _logger.info(f"Multi Send To Zatca Errors (Invoice ID: {record.id}) ***************************** :: {str(e)}")




    




 