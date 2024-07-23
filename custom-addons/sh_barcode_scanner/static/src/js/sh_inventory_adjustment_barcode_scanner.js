/** @odoo-module **/

import { InventoryReportListView } from "@stock/views/list/inventory_report_list_view"
import { InventoryReportListController } from "@stock/views/list/inventory_report_list_controller";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { onWillStart, useRef, markup } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { debounce } from "@web/core/utils/timing";
import { AutoCloseDialog } from "./sh_dialog_auto_close";
import { escape } from "@web/core/utils/strings";

class InventoryAdjustmentBarcodeScannerListController extends InventoryReportListController {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.dialogService = useService("dialog");
        this.shScannerContainer = useRef("shInventoryAdjustmentBarcodeScannerContainer");
        onWillStart(this.willStart);
        this.debouncedChangeStockBarcodeScannerInput = debounce(this._onChangeStockBarcodeScannerInput.bind(this), 500);
    }
    /** Lifecycle
     * Get Inventory Barcode Scanner configuration settings.
     */
    async willStart() {
        const result = await this.rpc('/sh_barcode_scanner/sh_barcode_scanner_get_widget_data');
        this.sh_barcode_scanner_user_is_stock_manager = result.user_is_stock_manager;
        this.sh_barcode_scanner_user_has_stock_multi_locations = result.user_has_stock_multi_locations;
        this.sh_barcode_scanner_stock_locations = result.locations;
        this.sh_inven_adjt_barcode_scanner_auto_close_popup = result.sh_inven_adjt_barcode_scanner_auto_close_popup;
        this.sh_inven_adjt_barcode_scanner_warn_sound = result.sh_inven_adjt_barcode_scanner_warn_sound;
        this.selectedStockLocationId = browser.localStorage.getItem('sh_barcode_scanner_location_selected') !== undefined && !isNaN(browser.localStorage.getItem('sh_barcode_scanner_location_selected')) ? parseInt(browser.localStorage.getItem("sh_barcode_scanner_location_selected")) : 0;
        this.sh_scan_negative_stock = browser.localStorage.getItem('sh_barcode_scanner_is_scan_negative_stock') === "true" ? true : false;
    }

    /**
     * This method is called when barcode is changed above tree view
     * list view.
     * @private
     * @param {MouseEvent} ev
     */
    async _onChangeStockBarcodeScannerInput(ev) {
        let $el = $(ev.currentTarget);
        if (!this.$scannerAlertMessage) { this.$scannerAlertMessage = $(this.shScannerContainer.el).find(".js_cls_alert_msg"); }

        if (!this.$scannerErrorAudio) { this.$scannerErrorAudio = $(this.shScannerContainer.el).find("#sh_barcode_scanner_error_sound"); }

        let location = (this.sh_barcode_scanner_stock_locations || []).filter(location => location.id === this.selectedStockLocationId)
        if (this.sh_barcode_scanner_stock_locations?.length && !location.length) {
            location = this.sh_barcode_scanner_stock_locations[0];
            this.selectedStockLocationId = location[0].id !== undefined && !isNaN(location[0].id) ? parseInt(location[0].id) : 0;
            browser.localStorage.setItem('sh_barcode_scanner_location_selected', this.selectedStockLocationId);
        }
        if (location && location.length) { this.location_name = location[0].display_name }
        const barcode = $el.val();
        if (barcode) {
            const result = await this.rpc('/sh_barcode_scanner/sh_barcode_scanner_search_stock_quant_by_barcode', {
                barcode: barcode,
                domain: this.props.domain,
                location_id:this.sh_barcode_scanner_user_has_stock_multi_locations ? this.selectedStockLocationId: false,
                location_name:this.sh_barcode_scanner_user_has_stock_multi_locations && this.location_name !== undefined ? this.location_name : "",
                scan_negative_stock: this.sh_scan_negative_stock,
            });
            if (result && result.is_qty_updated) {
                await this.model.root.load();
                this.render(true);
                if (this.$scannerAlertMessage) { this.$scannerAlertMessage.html($('<div class="alert alert-info mt-3" role="alert">' + result.message + ' </div>')); }

            } else {
                if (this.$scannerAlertMessage) { this.$scannerAlertMessage.html($('<div class="alert alert-danger mt-3" role="alert">' + result.message + ' </div>')); }
                // Play Warning Sound
                if (this.sh_inven_adjt_barcode_scanner_warn_sound && this.$scannerErrorAudio) { this.$scannerErrorAudio[0].play(); }
            }
            $el.val('');
        }
        // ---------------------------------------
        // auto focus barcode input            
        $el.focus();
        $el.keydown();
        $el.trigger({ type: 'keydown', which: 13 });
    }

    /**
     * This method is called when barcode is changed above the tree view
     * list view.
     * @private
     */
    async _onClickBarcodeScannerStockQuantApply() {
        var self = this;
        const result = await this.rpc('/sh_barcode_scanner/sh_barcode_scanner_stock_quant_tree_btn_apply', { domain: this.props.domain });
        let error = false;

        let title = _t("Something went wrong");
        if (result && result.is_qty_applied) {
            title = _t("Inventory Succeed");
            await this.model.root.load();
            this.render(true);
        } else {
            title = _t("Something went wrong");
            error = true;
        }
        this.dialogService.add(AutoCloseDialog, {
            title: title,
            body: markup(`<p>${escape(result.message)}</p>`),
            autoCloseAfter: error && this.sh_inven_adjt_barcode_scanner_auto_close_popup > 0 ? this.sh_inven_adjt_barcode_scanner_auto_close_popup : 0,
            confirm: async () => { },
            cancel: () => { },
        });
        if (error) {
            if (!this.$scannerErrorAudio) { this.$scannerErrorAudio = $(this.shScannerContainer.el).find("#sh_barcode_scanner_error_sound"); }
            // Play Warning Sound
            if (this.sh_inven_adjt_barcode_scanner_warn_sound && this.$scannerErrorAudio) this.$scannerErrorAudio[0].play();
        }
    }

    /**
     * This method is called when location is changed above tree view
     * list view.
     * @private
     * @param {MouseEvent} ev
     */
    async _onChangeStockLocation(ev) {
        let location = $(ev.currentTarget).val();
        this.selectedStockLocationId = location !== undefined && !isNaN(location) ? parseInt(location) : 0;
        browser.localStorage.setItem('sh_barcode_scanner_location_selected', this.selectedStockLocationId);
    }

    /**
     * @private
     * @param {Event} ev 
     */
    async _onChangeScanNegativeStock(ev) {
        if ($(ev.currentTarget).prop('checked')) {
            this.sh_scan_negative_stock = true;
        } else {
            this.sh_scan_negative_stock = false;
        }
        browser.localStorage.setItem('sh_barcode_scanner_is_scan_negative_stock', this.sh_scan_negative_stock);
    }

}

InventoryAdjustmentBarcodeScannerListController.template = "sh_barcode_scanner.InventoryAdjustmentListView";
InventoryReportListView.Controller = InventoryAdjustmentBarcodeScannerListController