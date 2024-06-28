before installing/updating this module

1)

changelog

1) 17.10.x
    1) code modified for compatibility with pre-payment module extension
    2) bt25 function separated. 
    3) pos payment info added in simplified report
    4) invoice line & document level discount separated.
    5) remaining time added 
2) 17.9.x
    1) multi branches support added
    2) zatca solution is made under the assumption that (if zatca ever asked, then this scenario has to be answered),
       there is 1 centralized system, (also called company headquarters in terms of database)
       we send all the invoices from there, therefore all the sequences are used from parent company,
       Only other seller id will be used from child company, as according to zatca technical documentation,
       it has to be mentioned from the branch info
3) 17.8.x
    1) auto compliance added.
4) 17.7.x
    1) translations, dashboard, self billed, arabic fields, reports
    2) (updated with arabic & self billed).
