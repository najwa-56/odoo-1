# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import api, models

class SearchDocument(models.Model):
    _name = "sh_barcode_scanner.search.document"
    _description = "Search Document By Barcode"

    @api.model
    def has_global_search_enabled(self):
        return self.env.company.sh_global_document_search_is_enable

    @api.model
    def _search_document_all(self, barcode):
        result = {}
        if self.env.company.sh_global_document_search_is_sale:
            result = self._search_document_sale(barcode)
        if not result and self.env.company.sh_global_document_search_is_purchase:
            result = self._search_document_purchase(barcode)
        if not result and self.env.company.sh_global_document_search_is_picking:
            result = self._search_document_picking(barcode)
        if not result and self.env.company.sh_global_document_search_is_invoice:
            result = self._search_document_invoice(barcode)
        if not result and self.env.company.sh_global_document_search_is_product:
            result = self._search_document_product(barcode)
        if not result and self.env.company.sh_global_document_search_is_lot:
            result = self._search_document_lot(barcode)
        if not result and self.env.company.sh_global_document_search_is_location:
            result = self._search_document_location(barcode)

        return result

    @api.model
    def _search_document_sale(self, barcode):
        result = {}
        order = self.env["sale.order"].search([("name","=",barcode)],limit=1)
        if order:
            action = self.env.ref("sale.action_orders").read()[0]
            action["context"] = {}
            action["domain"] = []
            action["views"] = [
                (self.env.ref("sale.view_order_form").id, "form")]
            action["res_id"] = order.id
            action["target"] = "new"

            result["action"] = action
        return result

    @api.model
    def _search_document_purchase(self, barcode):
        result = {}
        order = self.env["purchase.order"].search([("name","=",barcode)],limit=1)
        if order:
            action = self.env.ref("purchase.purchase_form_action").read()[0]
            action["context"] = {}
            action["domain"] = []
            action["views"] = [
                (self.env.ref("purchase.purchase_order_form").id, "form")]
            action["res_id"] = order.id
            action["target"] = "new"
            result["action"] = action
        return result

    @api.model
    def _search_document_picking(self, barcode):
        result = {}
        picking = self.env["stock.picking"].search([("name","=",barcode)],limit=1)
        if picking:
            action = self.env.ref("stock.action_picking_tree_all").read()[0]
            action["context"] = {}
            action["domain"] = []
            action["views"] = [
                (self.env.ref("stock.view_picking_form").id, "form")]
            action["res_id"] = picking.id
            action["target"] = "new"
            result["action"] = action
        return result

    @api.model
    def _search_document_invoice(self, barcode):
        result = {}
        move = self.env["account.move"].search([("name","=",barcode)],limit=1)
        if move:
            action = self.env.ref(
                "account.action_move_out_invoice_type").read()[0]
            action["domain"] = []
            action["views"] = [
                (self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = move.id
            action["target"] = "new"
            result["action"] = action
        return result

    @api.model
    def _search_document_product(self, barcode):
        result = {}
        product = self.env["product.product"].search([("barcode","=",barcode)],limit=1)
        if product:
            if product.product_tmpl_id and product.product_tmpl_id.product_variant_ids and len(product.product_tmpl_id.product_variant_ids) == 1:
                action = self.env.ref("product.product_template_action").read()[0]
                action["domain"] = []
                action["views"] = [
                    (self.env.ref("product.product_template_only_form_view").id, "form")]
                action["res_id"] = product.product_tmpl_id.id
                action["target"] = "new"
                result["action"] = action

            elif product.product_tmpl_id and product.product_tmpl_id.product_variant_ids and len(product.product_tmpl_id.product_variant_ids) != 1:
                action = self.env.ref("product.product_normal_action_sell").read()[0]
                action["domain"] = []
                action["views"] = [
                    (self.env.ref("product.product_normal_form_view").id, "form")]
                action["res_id"] = product.id
                action["target"] = "new"
                result["action"] = action
        return result

    @api.model
    def _search_document_lot(self, barcode):
        result = {}
        lot = self.env["stock.lot"].search([("name","=",barcode)],limit=1)
        if lot:
            action = self.env.ref("stock.action_production_lot_form").read()[0]
            action["context"] = {}
            action["domain"] = []
            action["views"] = [(self.env.ref("stock.view_production_lot_form").id, "form")]
            action["res_id"] = lot.id
            action["target"] = "new"
            result["action"] = action

        return result

    @api.model
    def _search_document_location(self, barcode):
        result = {}
        location = self.env["stock.location"].search([("barcode","=",barcode)],limit=1)
        if location:
            action = self.env.ref("stock.action_location_form").read()[0]
            action["domain"] = []
            action["views"] = [(self.env.ref("stock.view_location_form").id, "form")]
            action["res_id"] = location.id
            action["target"] = "new"
            result["action"] = action
        return result

    @api.model
    def search_document(self, barcode, doc_type):
        search_doc_method = getattr(self, "_search_document_" + doc_type) if hasattr(self, "_search_document_" + doc_type) else False
        result = search_doc_method(barcode) if search_doc_method else {}
        if result and result.get("action"):
            action = result.get("action", {})
            action.update({
                "target": self.env.company.sh_global_document_search_action_target_type
            })
            result["action"] = action
        return result
