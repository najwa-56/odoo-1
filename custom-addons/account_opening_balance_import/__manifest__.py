{
    "name": "Opening Balance Import (Excel)",
    "version": "17.0.1.0.0",
    "category": "Accounting/Configuration",
    "summary": "Upload an Excel file and create one balanced opening-balance journal entry",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "views/opening_balance_import_wizard.xml"
    ],
    "external_dependencies": {"python": ["pandas", "openpyxl"]},
    "license": "OPL-1",
}