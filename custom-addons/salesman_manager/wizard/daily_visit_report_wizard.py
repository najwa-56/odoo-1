from odoo import models, fields, api
from odoo.exceptions import UserError
import io
import base64
import xlsxwriter



class DailyVisitReportWizard( models.TransientModel ):
    _name = 'daily.visit.report.wizard'
    _description = 'Daily Visit Report Wizard'

    created_by = fields.Many2one( 'res.users', string='salesman' )
    date_from = fields.Datetime( string='From' )
    date_to = fields.Datetime( string='To' )

    def _search_visits (self):
        """Return daily.visit.report records filtered by the wizard."""
        domain = []
        if self.created_by:
            domain.append( ('created_by', '=', self.created_by.id) )
        if self.date_from:
            domain.append( ('creation_date', '>=', self.date_from) )
        if self.date_to:
            domain.append( ('creation_date', '<=', self.date_to) )

        visits = self.env['daily.visit.report'].search( domain, order='creation_date asc' )
        if not visits:
            raise UserError( "No records found for the selected filters." )
        return visits

    @staticmethod
    def _fmt_display_datetime (self_rec, dt):
        """Return a display string in the user's timezone (no seconds)."""
        if not dt:
            return False
        local_dt = fields.Datetime.context_timestamp( self_rec, dt )  # to user tz
        return local_dt.strftime( '%Y-%m-%d %H:%M' )

    # ---------- PDF ----------
    def action_print_pdf (self):
        visits = self._search_visits()

        data = {
            'salesman_name': self.created_by.name if self.created_by else False,
            'date_from_display': self._fmt_display_datetime( self, self.date_from ),
            'date_to_display': self._fmt_display_datetime( self, self.date_to ),
            'docids': visits.ids,
        }
        return self.env.ref( 'salesman_manager.action_daily_visit_pdf_report' ) \
            .report_action( visits, data=data )

    # ---------- Excel ----------
    def action_export_xlsx (self):
        visits = self._search_visits()

        # Build workbook in memory (remove_timezone makes aware datetimes acceptable)
        output = io.BytesIO()
        wb = xlsxwriter.Workbook( output, {
            'in_memory': True,
            'remove_timezone': True,  # <- key to avoid timezone error
        } )
        ws = wb.add_worksheet( 'Daily Visits' )

        # Formats
        base_border = {'border': 1, 'align': 'center', 'valign': 'vcenter'}
        title_fmt = wb.add_format( {'bold': True, 'align': 'center', 'font_size': 14} )
        header_fmt = wb.add_format( {**base_border, 'bold': True} )
        text_fmt = wb.add_format( base_border )
        date_fmt = wb.add_format( {**base_border, 'num_format': 'yyyy-mm-dd hh:mm'} )
        num_fmt = wb.add_format( {**base_border, 'num_format': '0.00'} )
        num_red_bold = wb.add_format( {**base_border, 'num_format': '0.00', 'font_color': 'red', 'bold': True} )

        row = 0
        # Title
        ws.merge_range( row, 0, row, 6, 'Daily Visit Report', title_fmt )
        row += 1

        # Filters line
        salesman = self.created_by.name if self.created_by else 'All'
        df = self._fmt_display_datetime( self, self.date_from ) or 'All'
        dt = self._fmt_display_datetime( self, self.date_to ) or 'All'
        ws.write( row, 0, 'Salesman', header_fmt );
        ws.write( row, 1, salesman, text_fmt )
        ws.write( row, 3, 'Date From', header_fmt );
        ws.write( row, 4, df, text_fmt )
        ws.write( row, 5, 'Date To', header_fmt );
        ws.write( row, 6, dt, text_fmt )
        row += 2

        # Table header
        headers = ['Reference', 'Customer', 'Is Sold?', 'Check In', 'Check Out', 'Time Spent in customer', 'Time Between customers']
        for col, h in enumerate( headers ):
            ws.write( row, col, h, header_fmt )
        row += 1

        # Column widths (nice to read)
        widths = [18, 22, 10, 20, 20, 12, 14]
        for i, w in enumerate( widths ):
            ws.set_column( i, i, w )

        # Rows
        for rec in visits:
            # Localized datetimes (xlsxwriter with remove_timezone=True accepts aware, but we'll also .replace(tzinfo=None) to be explicit)
            ci = fields.Datetime.context_timestamp( self, rec.creation_date ) if rec.creation_date else None
            co = fields.Datetime.context_timestamp( self, rec.check_out_time ) if rec.check_out_time else None

            ws.write( row, 0, rec.reference or '', text_fmt )
            ws.write( row, 1, rec.partner_id.name or '', text_fmt )
            ws.write( row, 2, 'Yes' if rec.is_it_sold else 'No', text_fmt )

            if ci:
                ws.write_datetime( row, 3, ci.replace( tzinfo=None ), date_fmt )
            else:
                ws.write( row, 3, '', text_fmt )

            if co:
                ws.write_datetime( row, 4, co.replace( tzinfo=None ), date_fmt )
            else:
                ws.write( row, 4, '', text_fmt )

            # Numbers with red/bold if above averages
            ts = rec.time_spending_in_customer or 0.0
            tb = rec.time_between_customers or 0.0

            ts_fmt = num_red_bold if (
                        rec.avg_time_spent_per_customer and ts > rec.avg_time_spent_per_customer) else num_fmt
            tb_fmt = num_red_bold if (rec.avg_time_between_customer and tb > rec.avg_time_between_customer) else num_fmt

            ws.write_number( row, 5, ts, ts_fmt )
            ws.write_number( row, 6, tb, tb_fmt )

            row += 1

        wb.close()
        output.seek( 0 )

        # Make an attachment and return a download action
        filename = 'Daily_Visit_Report.xlsx'
        attachment = self.env['ir.attachment'].create( {
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode( output.read() ),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        } )
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }