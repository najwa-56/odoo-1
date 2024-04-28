/** @odoo-module */

import { registry } from "@web/core/registry";


export default class PrintActionHandler {
  constructor() {
    this.wkhtmltopdfStateProm = null;
  }

  async printOrDownloadReport(action, options, env) {
    if (typeof window.PrintPDF === 'undefined') {
      return false;
    }

    let download_only = false;

    if (options.download || (action.context && action.context.download_only)) {
      download_only = true;
    }

    if (action.report_type === "qweb-pdf") {
      return this._triggerDownload(action, options, "pdf", env);
    } else if (action.report_type === 'qwweb-html') {
      return this._triggerDownload(action, options, "html", env);
    } else if (action.report_type === 'qwweb-text') {
      return this._triggerDownload(action, options, "text", env);
    }
  }

  _getReportUrl(action, type, env) {
    let url = `/report/${type}/${action.report_name}`;
    const actionContext = action.context || {};

    if (action.data && JSON.stringify(action.data) !== "{}") {
      const options = encodeURIComponent(JSON.stringify(action.data));
      const context = encodeURIComponent(JSON.stringify(actionContext));
      url += `?options=${options}&context=${context}`;
    } else {
      if (actionContext.active_ids) {
        url += `/${actionContext.active_ids.join(",")}`;
      }

      if (type === "html") {
        const context = encodeURIComponent(JSON.stringify(env.services.user.context));
        url += `?context=${context}`;
      }
    }

    // Return true to avoid the default behavior (which will try to download report file)
    return url;
  }

  async _triggerDownload(action, options, type, env) {
    var url = this._getReportUrl(action, type, env);
    const rtype = 'qweb-' + url.split('/')[2];
    var result = true;
    env.services.ui.block();
    fetch(url)
      .then(res => res.blob())
      .then(blob => {
        var reader = new window.FileReader();
        reader.readAsDataURL(blob);
        reader.onloadend = function () {
          var base64data = reader.result;
          const args = [{
                base64data: base64data,
                type: blob.type,
            }];
    result = window.PrintPDF.callHandler('PrintPDF', ...args);
          // result = window.PrintPDF(base64data, blob.type);
          env.services.ui.unblock();
        }
      })
      .catch((error) => {
        console.log(error);
        env.services.ui.unblock();
      });;
    return result;
  }


}


const handler = new PrintActionHandler();

function print_or_download_report_handler(action, options, env) {
  return handler.printOrDownloadReport(action, options, env);
}

registry
  .category("ir.actions.report handlers")
  .add('direct_print_report', print_or_download_report_handler, { sequence: 0 });
