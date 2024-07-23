# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies Pvt. Ltd.

from odoo import _, http
from odoo.exceptions import UserError
from odoo.http import request
from odoo.osv.expression import AND


class ShStockAdjustment(http.Controller):

    @http.route(["/sh_barcode_scanner/sh_barcode_scanner_get_widget_data"], type="json", auth="user", cors="*")
    def sh_barcode_scanner_get_widget_data(self):
        """
            Method of Softhealer Technologies Pvt. Ltd.
            The function retrieves data related to the user's stock
            management permissions and settings for a barcode scanner widget.
        :return: a dictionary named "result" which contains the following key-value pairs:
        """
        result = {}
        user_is_stock_manager = request.env.user.has_group(
            "stock.group_stock_manager")
        user_has_stock_multi_locations = request.env.user.has_group(
            "stock.group_stock_multi_locations")
        result["user_is_stock_manager"] = user_is_stock_manager
        result["user_has_stock_multi_locations"] = user_has_stock_multi_locations
        result["sh_inven_adjt_barcode_scanner_auto_close_popup"] = request.env.company.sudo().sh_inven_adjt_barcode_scanner_auto_close_popup
        result["sh_inven_adjt_barcode_scanner_warn_sound"] = request.env.company.sudo().sh_inven_adjt_barcode_scanner_warn_sound

        if user_has_stock_multi_locations:
            domain = [("usage", "in", ["internal", "transit"])]
            locations = request.env["stock.location"].search_read(domain, ["id", "display_name"])
            result["locations"] = locations
        return result

    @http.route(["/sh_barcode_scanner/sh_barcode_scanner_search_stock_quant_by_barcode"], type="json", auth="user", cors="*")
    def sh_barcode_scanner_search_stock_quant_by_barcode(self, barcode=None, domain=None, location_id=None, location_name=None, scan_negative_stock=None):
        """
            Method of Softhealer Technologies Pvt. Ltd.
        The function searches for a stock quantity
        based on a barcode and updates the quantity if found.

        :param barcode: The barcode parameter is used to specify the barcode value that you want to
        search for in the stock quant records
        :param domain: The "domain" parameter is used to filter the search for stock quantities. It is a
        list of conditions that the stock.quant records must meet in order to be included in the search
        results.
        :param location_id: The `location_id` parameter is used to specify the ID of the location where
        you want to search for the stock quantity. It is an optional parameter and if not provided, the
        function will search for stock quantities in locations with the usage of "internal" or "transit"
        :param location_name: The parameter "location_name" is used to specify the name of the location
        where the barcode is being scanned. It is an optional parameter and is used to provide more
        specific information in the error message if the barcode is not found in the specified location
        :param scan_negative_stock: The parameter "scan_negative_stock" is a boolean value that
        determines whether the inventory quantity should be decreased by 1 if the barcode is found in
        the stock. If it is set to True, the inventory quantity will be decreased by 1. If it is set to
        False or not provided, the
        :return: a dictionary with two keys: "is_qty_updated" and "message". The value of
        "is_qty_updated" indicates whether the quantity was updated or not, and the value of "message"
        provides a message explaining the result of the barcode scanning operation.
        """
        company_sudo = request.env.company.sudo()
        result = {"is_qty_updated": False, "message": _(
            "Please enter/type barcode in barcode input and try again.")}

        if barcode not in ["", False, None]:
            domain_product = []
            if company_sudo.sh_inven_adjt_barcode_scanner_type == "barcode":
                domain_product = [("product_id.barcode", "=", barcode)]

            elif company_sudo.sh_inven_adjt_barcode_scanner_type == "int_ref":
                domain_product = [("product_id.default_code", "=", barcode)]

            elif company_sudo.sh_inven_adjt_barcode_scanner_type == "sh_qr_code":
                domain_product = [("product_id.sh_qr_code", "=", barcode)]

            elif company_sudo.sh_inven_adjt_barcode_scanner_type == "all":
                domain_product = ["|", "|", ("product_id.default_code", "=", barcode), (
                    "product_id.barcode", "=", barcode), ("product_id.sh_qr_code", "=", barcode)]

            if not domain:
                domain = [("location_id.usage", "in", ["internal", "transit"])]

            if location_id:
                domain = AND([domain, [("location_id", "=", location_id)]])

            quant = request.env["stock.quant"].with_company(company_sudo.id).search(
                AND([domain, domain_product]), limit=1)
            if quant:
                if scan_negative_stock:
                    quant.inventory_quantity -= 1
                else:
                    quant.inventory_quantity += 1
                result["is_qty_updated"] = True
                result["message"] = "Product Added Successfully"
            else:
                result["is_qty_updated"] = False
                message = F"Record not found for this scanned barcode: {barcode}"
                if location_name:
                    message = F"Record not found for this scanned barcode:{barcode} and location: {location_name}"
                result["message"] = _(message)

        return result

    @http.route(["/sh_barcode_scanner/sh_barcode_scanner_stock_quant_tree_btn_apply"], type="json", auth="user", cors="*")
    def sh_barcode_scanner_stock_quant_tree_btn_apply(self, domain=None):
        """
            Method of Softhealer Technologies Pvt. Ltd.
        The function applies the counted quantity to all inventory lines that meet the specified domain criteria.

        :param domain: The domain parameter is used to filter the stock quants that will be processed.
        It is a list of conditions that the quants must meet in order to be included in the processing.
        In this case, the domain is set to [("location_id.usage", "in", ["internal", "transit"])]
        :return: a dictionary with two keys: "is_qty_applied" and "message". The value of
        "is_qty_applied" indicates whether the quantity has been applied or not, and the value of
        "message" provides a message related to the action performed.
        """
        if not request.env.user.has_group("stock.group_stock_manager"):
            raise UserError(_("Only stock manager can do this action"))

        if not domain:
            domain = [("location_id.usage", "in", ["internal", "transit"])]
        result = {"is_qty_applied": False, "message": _(
            "No any inventory line found for this action - Apply")}
        quants = request.env["stock.quant"].search(
            AND([domain, [("inventory_quantity_set", "!=", False)]]))

        if quants:
            for quant in quants:
                quant.action_apply_inventory()
            result = {"is_qty_applied": True, "message": _(
                "All Counted Quantity successfully applied")}

        return result
