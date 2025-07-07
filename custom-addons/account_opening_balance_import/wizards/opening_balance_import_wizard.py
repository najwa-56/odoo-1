import base64
import io
import pandas as pd

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class OpeningBalanceImportWizard(models.TransientModel):
    _name = "opening_balance_import_wizard"
    _description = "Import Opening Balance Journal Entry from Excel"

    file_data = fields.Binary(string="Excel file", required=True)
    file_name = fields.Char(string="Filename")

    def _read_dataframe(self):
        """Decode the uploaded file and return a pandas DataFrame (first sheet)."""
        try:
            stream = io.BytesIO(base64.b64decode(self.file_data))
            df = pd.read_excel(stream, sheet_name=0, engine="openpyxl")
            return df
        except Exception as e:
            raise UserError(_("Unable to read Excel file: %s") % e)

    def action_import(self):
        self.ensure_one()
        df = self._read_dataframe()

        if df.shape[0] < 1:
            raise UserError(_("The file seems empty."))

        # --------------------------------------------------
        # Extract move header (row 0, col 0‑3)
        # --------------------------------------------------
        date_val = pd.to_datetime(df.iloc[0, 0]).date()
        journal_name = str(df.iloc[0, 1]).strip()
        reference = str(df.iloc[0, 2]).strip() if not pd.isna(df.iloc[0, 2]) else ""

        # --------------------------------------------------
        # Resolve journal
        # --------------------------------------------------
        journal = self.env["account.journal"].search([("name", "=", 'a')], limit=1)
        if not journal:
            raise UserError(_("Journal '%s' was not found.") % journal_name)

        # --------------------------------------------------
        # Iterate rows to gather move lines.
        # The columns are assumed to be:
        #   3: Account Code
        #   4: Account Name
        #   5: Label
        #   6: Partner Name
        #   7: Credit
        #   8: Debit
        #
        # Row 0 ALSO contains a first line (opening of the balance), per user spec.
        # --------------------------------------------------
        lines = []
        total_debit = total_credit = 0.0

        for idx in range(df.shape[0]):
            row = df.iloc[idx]
            
            raw_acct_code = row.iloc[3] if len(row) > 3 else ""
            if pd.isna(raw_acct_code):
                acct_code = ""
            elif isinstance(raw_acct_code, (int, float)):
                if isinstance(raw_acct_code, float) and raw_acct_code.is_integer():
                    raw_acct_code = int(raw_acct_code)
                acct_code = str(raw_acct_code)
            else:
                acct_code = str(raw_acct_code).strip()

            if acct_code.endswith(".0"):
                acct_code = acct_code[:-2]


            partner_name = str(row.iloc[4]).strip() if len(row) > 4 and not pd.isna(row.iloc[4]) else ""
            label = str(row.iloc[5]).strip() if len(row) > 5 and not pd.isna(row.iloc[5]) else ""
            credit = float(row.iloc[6]) if len(row) > 6 and not pd.isna(row.iloc[6]) else 0.0
            debit = float(row.iloc[7]) if len(row) > 7 and not pd.isna(row.iloc[7]) else 0.0

            # skip empty lines
            if not acct_code or (debit == 0 and credit == 0):
                continue

            # Account lookup
            account = self.env["account.account"].search([("code", "=", acct_code)], limit=1)
            if not account:
                raise UserError(_("Account with code '%s' was not found (row %s).") % (acct_code, idx + 2))

            # Partner lookup / create
            partner_id = False
            if partner_name and partner_name.lower() not in ("nan", "none", ""):
                partner = self.env["res.partner"].search([("name", "=", partner_name)], limit=1)
                if not partner:
                    partner = self.env["res.partner"].create({"name": partner_name})
                partner_id = partner.id

            lines.append((0, 0, {
                "account_id": account.id,
                "name": label or account.name,
                "partner_id": partner_id,
                "credit": credit,
                "debit": debit,
            }))

            total_debit += debit
            total_credit += credit

        # --------------------------------------------------
        # Balance check
        # --------------------------------------------------
        if round(total_debit, 2) != round(total_credit, 2):
            raise UserError(
                _("The entry is not balanced.\nTotal Debit: %.2f\nTotal Credit: %.2f")
                % (total_debit, total_credit)
            )

        # --------------------------------------------------
        # Create move in draft
        # --------------------------------------------------
        move_vals = {
            "date": date_val,
            "journal_id": journal.id,
            "ref": reference,
            "move_type": "entry",
            "line_ids": lines,
        }
        move = self.env["account.move"].create(move_vals)

        return {
            "type": "ir.actions.act_window",
            "name": _("Opening Balance Journal Entry"),
            "res_model": "account.move",
            "view_mode": "form",
            "target": "current",
            "res_id": move.id,
        }
    

    