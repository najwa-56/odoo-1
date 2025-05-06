/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Model } from "@web/model/model";
import { browser } from "@web/core/browser/browser";
import { formatDateTime, parseDate, parseDateTime } from "@web/core/l10n/dates";
import { KeepLast } from "@web/core/utils/concurrency";
import { useService } from "@web/core/utils/hooks";

export class MapModel extends Model {
    setup(params, { notification, http }) {
        this.notification = notification;
        this.orm = useService("orm");
        this.http = http;

        this.metaData = {
            ...params,
        };

        this.data = {
            count: 0,
            locatedRecordsCount: 0,
            isFetchingCoordinates: false,
            coordinateFetchRequired: true,
            groupByKey: false,
            isGrouped: false,
            partnerIds: [],
            partners: [],
            partnerToCache: [],
            recordGroups: [],
            records: [],
        };
        this.keepLast = new KeepLast();
    }

    async load(params) {
        const metaData = {
            ...this.metaData,
            ...params,
        };

        metaData.groupBy = (metaData.groupBy || []).filter((groupBy) => {
            const [fieldName] = groupBy.split(".");
            const field = metaData.fields[fieldName];
            return field?.type !== "properties";
        });
        this.data = await this._fetchData(metaData);
        this.metaData = metaData;

        this.notify();
    }

    async _fetchData(metaData) {
        const data = {
            count: 0,
            locatedRecordsCount: 0,
            isFetchingCoordinates: false,
            coordinateFetchRequired: true,
            groupByKey: metaData.groupBy.length ? metaData.groupBy[0] : false,
            isGrouped: metaData.groupBy.length > 0,
            partnerIds: [],
            partners: [],
            partnerToCache: [],
            recordGroups: [],
            records: [],
        };
        if (!metaData.resPartnerField) {
            data.recordGroups = [];
            data.records = [];
            return this.keepLast.add(Promise.resolve(data));
        }
        const results = await this.keepLast.add(this._fetchRecordData(metaData, data));
        const datetimeTypeFields = metaData.fieldNames.filter(
            (name) => metaData.fields[name].type == "datetime"
        );
        for (const record of results.records) {
            for (const field of datetimeTypeFields) {
                if (record[field]) {
                    const dateUTC = luxon.DateTime.fromFormat(record[field], "yyyy-MM-dd HH:mm:ss",{ zone: "UTC" });
                    record[field] = formatDateTime(dateUTC, { format: "yyyy-MM-dd HH:mm:ss" });
                }
            }
        }

        if (results.records){
            data.records = results.records;
        }else{
            data.records = [];
        }
        if (results.length){
            data.count = results.length;
        }else{
            data.count = 0;
        }
        if (data.isGrouped) {
            data.recordGroups = await this._getRecordGroups(metaData, data);
        } else {
            data.recordGroups = [];
        }

        data.partnerIds = [];
        if (metaData.resModel === "res.partner" && metaData.resPartnerField === "id") {
            for (const record of data.records) {
                data.partnerIds.push(record.id);
                record.partner_id = [record.id];
            }
        } else {
            this._retrievePartnerIds(metaData, data);
        }
        data.partnerIds = Array.from(new Set(data.partnerIds));
        await this._fetchPartnerData(metaData, data);

        return data;
    }

    async _fetchPartnerData(metaData, data) {
        data.partners = data.partnerIds.length
            ? await this.keepLast.add(this._fetchRecordsPartner(metaData, data, data.partnerIds))
            : [];
        this._addPartnerToRecord(metaData, data);
    }

    _addPartnerToRecord(metaData, data) {
        for (const record of data.records) {
            for (const partner of data.partners) {
                let partnerRecordId;
                if (metaData.resModel === "res.partner" && metaData.resPartnerField === "id") {
                    partnerRecordId = record.id;
                } else {
                    partnerRecordId = record[metaData.resPartnerField].id;
                }
                if (partnerRecordId == partner.id) {
                    record.partner = partner;
                    data.locatedRecordsCount++;
                }
            }
        }
    }

    _fetchRecordData(metaData, data) {
        try {
            const fieldNames = data.groupByKey 
                ? [...metaData.fieldNames, data.groupByKey.split(":")[0]] 
                : metaData.fieldNames;

            const specification = this._buildFieldSpecification(metaData, fieldNames);
            const orderBy = this._buildOrderByClause(metaData);

            return this.orm.webSearchRead(metaData.resModel, metaData.domain, {
                specification,
                limit: metaData.limit,
                offset: metaData.offset,
                order: orderBy.join(" "),
                context: metaData.context,
            }).then((response) => {
                return response;
            }).catch((error) => {
                throw error;
            });
        } catch (error) {
            throw error;
        }
    }

    _buildFieldSpecification(metaData, fieldNames) {
        const specification = {};
        for (const fieldName of fieldNames) {
            specification[fieldName] = {};
            if (["many2one", "one2many", "many2many"].includes(metaData.fields[fieldName].type)) {
                specification[fieldName].fields = { display_name: {} };
            }
        }
        return specification;
    }

    _buildOrderByClause(metaData) {
        const orderBy = [];
        if (metaData.defaultOrder) {
            orderBy.push(metaData.defaultOrder.name);
            if (metaData.defaultOrder.asc) {
                orderBy.push("ASC");
            }
        }
        return orderBy;
    }

    async _fetchRecordsPartner(metaData, data, ids) {
        try {
            const domain = [
                ["complete_contact_address", "!=", "False"],
                ["id", "in", ids],
            ];
            const fields = ["complete_contact_address", "partner_latitude", "partner_longitude"];
            const records = await this.orm.searchRead("res.partner", domain, fields);
            return records;
        } catch (error) {
            throw error;
        }
    }

    _retrievePartnerIds(metaData, data) {
        const partnerField = metaData.resPartnerField;
        const uniquePartnerIds = new Set();
    
        for (const record of data.records) {
            const partner = record[partnerField];
            if (partner?.id) {
                uniquePartnerIds.add(partner.id);
            }
        }
    
        data.partnerIds = Array.from(uniquePartnerIds);
    }

    _getEmptyGroupLabel(fieldName) {
        const fieldSpecificLabels = {};
        return fieldSpecificLabels[fieldName] || _t("None");
    }

    async _getRecordGroups(metaData, data) {
        const [fieldName, subGroup] = data.groupByKey.split(":");
        const fieldType = metaData.fields[fieldName].type;
        const groups = {};
        function addToGroup(id, name, record) {
            if (!groups[id]) {
                groups[id] = {
                    name,
                    records: [],
                };
            }
            groups[id].records.push(record);
        }
        for (const record of data.records) {
            const value = record[fieldName];
            let id, name;
            if (["one2many", "many2many"].includes(fieldType)) {
                if (value.length) {
                    for (const r of value) {
                        addToGroup(r.id, r.display_name, record);
                    }
                } 
                else {
                    id = name = this._getEmptyGroupLabel(fieldName);
                    addToGroup(id, name, record);
                }
            } else {
                if (["date", "datetime"].includes(fieldType) && value) {
                    const date = fieldType === "date" ? parseDate(value) : parseDateTime(value);
                    const GROUP_DATE_FORMATS = {
                        year: "yyyy",
                        quarter: "'Q'q yyyy",
                        month: "MMMM yyyy",
                        week: "'W'WW yyyy",
                        day: "dd MMM yyyy",
                    };
                    id = name = date.toFormat(GROUP_DATE_FORMATS[subGroup]);
                } 
                else if (fieldType === "boolean") {
                    id = name = value ? _t("Yes") : _t("No");
                } 
                else if (fieldType === "selection") {
                    const selected = metaData.fields[fieldName].selection.find((o) => o[0] === value);
                    id = name = selected ? selected[1] : value;
                } 
                else if (fieldType === "many2one" && value) {
                    id = value.id;
                    name = value.display_name;
                } 
                else {
                    id = value;
                    name = value;
                }
                if (!id && !name) {
                    id = name = this._getEmptyGroupLabel(fieldName);
                }
                addToGroup(id, name, record);
            }
        }
        return groups;
    }
}

MapModel.services = ["notification", "http"];
MapModel.COORDINATE_FETCH_TIMEOUT = 1000;