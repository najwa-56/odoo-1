/** @odoo-module **/

import { DateTimePicker } from "@web/core/datetime/datetime_picker";

console.log("[web_datetime_picker_rounding_one] loaded");

// 1) Keep default minute step = 1 (helps when defaults are read)
DateTimePicker.defaultProps = {
    ...DateTimePicker.defaultProps,
    rounding: 1,
};

// 2) Safe monkey-patch: wrap the original onPropsUpdated and call it
const _orig_onPropsUpdated = DateTimePicker.prototype.onPropsUpdated;

DateTimePicker.prototype.onPropsUpdated = function (props) {
    // force 1-minute rounding
    props = { ...props, rounding: 1 };

    // call the original method (initializes focusDate, allowedPrecisionLevels, etc.)
    _orig_onPropsUpdated.call(this, props);

    // defensively rebuild minutes list (00..59) and hide seconds
    const MINUTES = [...Array(60).keys()].map((m) => [m, String(m).padStart(2, "0")]);
    this.availableMinutes = MINUTES;
    this.availableSeconds = [];
};
