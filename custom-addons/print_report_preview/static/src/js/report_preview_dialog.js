/** @odoo-module **/

import { Dialog } from "@web/core/dialog/dialog";
import { onWillStart, onMounted, useState, useRef, Component } from "@odoo/owl";

export class ReportPreviewDialog extends Component {
    setup() {
        this.iframeRef = useRef("iframe");
        this.state = useState({
            title: this.props.title || _t("Report"),
            reportUrl: this.props.reportUrl || false,
        })

        onWillStart(async () => {
            if (this.state.reportUrl){
                var viewerURL = "/web/static/lib/pdfjs/web/viewer.html?file=";
                viewerURL += encodeURIComponent(this.state.reportUrl).replace(/'/g,"%27").replace(/"/g,"%22") + "#page=1&zoom=100";
                this.state.url = viewerURL;
            }else{
                this.state.url = '';
            }
        });

        onMounted(async () => {
            await this.afterloadPDF();
        });

        
    }
    afterloadPDF(){   
        var self = this; 
        this.$iframe = $(this.iframeRef.el);
        var nbPrint = this.$iframe.contents().find('#print');
        var nbDownload = this.$iframe.contents().find('#download');
        var nbViewer = this.$iframe.contents().find('#viewer');
        if(nbPrint.length > 0 && nbDownload.length > 0 && nbViewer.length > 0) {
            nbPrint.hide();
            nbDownload.hide();
            nbViewer.bind('contextmenu', function(e) {
                return false;
            }); 
        } 
        else {
            setTimeout(function() {
                self.afterloadPDF();
            }, 10);
        }
    }
    close() {
        this.props.close && this.props.close();
    }
}
ReportPreviewDialog.components = { Dialog };
ReportPreviewDialog.template = "ReportPreviewDialog";
ReportPreviewDialog.defaultProps = {
    defaultName: "",
};
