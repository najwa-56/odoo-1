before installing/updating this module

1)

to be done in future

1) enterprise  report preview testing.

changelog

1) 17.12.x
   1) AV update completed.
   2) send to zatca via cron added as config.
   3) 
2) 17.11.x
    1) code modified for compatibility with tax inclusive prices
    2) ~~invoice level (document level) discount added~~
    3) invoice line level allowance added.
    4) ~~gift cards & promotions.~~ 
    5) invoice level (document level) discount added as -ve lines
    6) In simplified invoice, if partner.company_type == company, then 1000 SAR limit will be checked.
    7) new report template added.
    8) new configurations added in company
    9) invoice preview after "Send & Print" make same as zatca report.
   10) barcode added.
   11) skip customer address validations added as config
   12) header/footer remove from invoices, via config
   13) branch address, other seller & logo can be used, via config
   14) current datetime added for compliance invoices.
   15) simplified as A4 report
   16) invoice line level allowance added.
   17) disable odoo invoice reports from print menu in tree & form
   18) PDF-A3 outlines, warning/error solved,
   19) Report invoice type modified for both
   20) tax exception reason (*), added in report lines.
3) 17.10.x
    1) code modified for compatibility with pre-payment module extension
    2) bt25 function separated. 
    3) pos payment info added in simplified report
    4) invoice line & document level discount separated.
    5) remaining time added. 
    6) invoice line made unique to each invoice.
4) 17.9.x
    1) multi branches support added
    2) zatca solution is made under the assumption that (if zatca ever asked, then this scenario has to be answered),
       there is 1 centralized system, (also called company headquarters in terms of database)
       we send all the invoices from there, therefore all the sequences are used from parent company,
       Only other seller id will be used from child company, as according to zatca technical documentation,
       it has to be mentioned from the branch info
5) 17.8.x
    1) auto compliance added.
6) 17.7.x
    1) translations, dashboard, self billed, arabic fields, reports
    2) (updated with arabic & self billed).
