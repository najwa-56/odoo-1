/** @odoo-module **/

import { Component, useState, onWillUpdateProps, onWillStart } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { useGetDomainTreeDescription } from "@web/core/domain_selector/utils";
import { Domain } from "@web/core/domain";
import { treeFromDomain } from "@web/core/tree_editor/condition_tree";
import { setObjectInSession, getObjectFromSession, eraseSessionItem } from "@ks_dashboard_ninja/js/cookies";


export class PreDefinedFilterDropdown extends Component{
    static template = "ks_dashboard_ninja.pre_defined_filter_dropdown"
    static props = {
        dropdown_items: { type: Array },
        onDropDownSelect: { type: Function },
        removeAllFilters: { type: Boolean, optional: true }
    };
    static components = { DropdownItem }
    setup(){
        this.state = useState({
            searchText: '',
        });
    }

    get dropdown_items(){
        let searchedFilters = this.props.dropdown_items.filter(
            (item) => item.name.toLowerCase().includes(this.state.searchText.toLowerCase()) || item.type === 'separator')
        while(this.state.searchText && searchedFilters.length && searchedFilters[searchedFilters.length - 1].type === 'separator')
                searchedFilters.pop();
        while(this.state.searchText && searchedFilters.length && searchedFilters[0].type === 'separator')   searchedFilters.shift();
        return searchedFilters;
    }
}

export class PreDefinedFilter extends Component{
    static template = "ks_dashboard_ninja.pre_defined_filter"
    static props = {
        domain: { type: String, optional: true },
        update: { type: Function, optional: true },
        removeAllFilters: { type: Boolean, optional: true },
        remove: { type: Function, optional: true },
        options: { type: Object, optional: true },  // Tobe used for extra data provides to the component
        filters_data: { type: Object, optional: true },
    };
    static defaultProps = {

    };
    static components = { Dropdown, PreDefinedFilterDropdown }

    setup(){
        this.getDomainTreeDescription = useGetDomainTreeDescription();
        this.defaultState = {"Select Filter": { model_name: 'Select Filter', groups: {}}}
        this.state = useState({
            activeFilterModels : {"Select Filter": { model_name: 'Select Filter', groups: {}}},
        });
        this.filter_id = 0
        this.filters_data = this.props.filters_data;

        onWillStart( () => {
            this.setObjFromCookies();
            this.filters_data_list = Object.values(this.filters_data).sort(function(a, b){return a.sequence - b.sequence})
        })
        onWillUpdateProps((nextProps) => this.onPropsUpdated(nextProps))

    }

    onPropsUpdated(nextProps){
        if(nextProps.removeAllFilters)
            this.clearFilters()
    }

    setObjFromCookies(){
        let activeFilterModels_from_cky = getObjectFromSession('PFilter' + this.props.options.ks_dashboard_id)
        let filters_data_from_cky = getObjectFromSession('PFilterDataObj' + this.props.options.ks_dashboard_id)
        this.state.activeFilterModels = activeFilterModels_from_cky ?? {"Select Filter": { model_name: 'Select Filter', groups: {}}}
        if(!activeFilterModels_from_cky)    this.setActiveFilters()
        this.filters_data = filters_data_from_cky ?? this.filters_data
    }

    setActiveFilters(){
        Object.values(this.filters_data).forEach((filter) => {
            if(filter.active){
                this.addFilter(filter.id, filter.categ, filter.model)
            }
        })
    }

    clearFilters(){
        Object.values(this.filters_data).forEach( (filter) => { filter.active = false })
        this.state.activeFilterModels = {"Select Filter": { model_name: 'Select Filter', groups: {}}}
        eraseSessionItem('PFilter' + this.props.options.ks_dashboard_id)
        eraseSessionItem('PFilterDataObj' + this.props.options.ks_dashboard_id)
    }

    onPredefinedFilterSelect(filterId, filterCategory, filterModel){
        let isAppliedFilter = this.state.activeFilterModels[filterModel]?.groups?.[filterCategory]?.filters?.[filterId]
        isAppliedFilter ? this.removeFilter(filterId, filterCategory, filterModel) : this.addFilter(filterId, filterCategory, filterModel)
    }

    async removeFilter(filterId, filterCategory, filterModel){
        delete this.state.activeFilterModels[filterModel].groups[filterCategory].filters[filterId]
        this.filters_data[filterId].active = false
        await this.update(filterModel, filterCategory, filterId)
        this.pruneEmptyFilterGroups(this.state.activeFilterModels, filterModel, filterCategory)
    }


    addFilter(filterId, filterCategory, filterModel){
        if (this.state.activeFilterModels["Select Filter"]) {
            delete this.state.activeFilterModels["Select Filter"];
        }
        this.filters_data[filterId].active = true
        this.state.activeFilterModels[filterModel] ??= { model_name: this.filters_data[filterId].model_name, groups: {} };
        this.state.activeFilterModels[filterModel].groups[filterCategory] ??= {filters: {}, label: ''};

        this.state.activeFilterModels[filterModel].groups[filterCategory].filters[filterId] = this.filters_data[filterId].domain;

//        this.state.activeFilterModels[filterModel].groups[filterCategory].label = this.filters_data[filterId].domain;

        this.update(filterModel, filterCategory, filterId);
    }

    makeLabelForModelGroup(model, group){
        let filters = this.state.activeFilterModels[model]?.groups?.[group]?.filters
        let labels = ''
        if(filters){
            labels = Object.keys(filters).map(filterId => this.filters_data[filterId].name).join(' or ');
        }
        return labels ? labels : 'Applied Filter'
    }

     update(model, group , filter_id){
        eraseSessionItem('PFilter' + this.props.options.ks_dashboard_id)
        eraseSessionItem('PFilterDataObj' + this.props.options.ks_dashboard_id)
        let domainToUpdate = { [model]: { [group]: {}}}
        let domain = Domain.or([ ...Object.values(this.state.activeFilterModels[model].groups[group].filters) ]).toList();
        let label = this.makeLabelForModelGroup(model, group)
        domainToUpdate[model][group].domain = domain
        this.state.activeFilterModels[model].groups[group].label = label === '' ? this.filters_data[filter_id].name : label
        this.state.activeFilterModels[model].groups[group].domain = domain
        setObjectInSession('PFilter' + this.props.options.ks_dashboard_id, this.state.activeFilterModels, 1)
        setObjectInSession('PFilterDataObj' + this.props.options.ks_dashboard_id, this.filters_data, 1)
        this.props.update(domainToUpdate)
    }

    pruneEmptyFilterGroups(filterData, modelName, groupName){
        if(!Object.values(this.state.activeFilterModels[modelName].groups[groupName]?.filters ?? {}).length)
            delete this.state.activeFilterModels[modelName].groups[groupName]
        if(!Object.values(this.state.activeFilterModels[modelName].groups).length)
            delete this.state.activeFilterModels[modelName]
        if(!Object.values(this.state.activeFilterModels).length)
            this.state.activeFilterModels = {"Select Filter": { model_name: 'Select Filter', groups: {}}}
    }

    removeGroup(model, group){
        eraseSessionItem('PFilter' + this.props.options.ks_dashboard_id)
        eraseSessionItem('PFilterDataObj' + this.props.options.ks_dashboard_id)
        let model_group = this.state.activeFilterModels[model].groups[group]
        Object.keys(model_group.filters).forEach( (filter_id) => this.filters_data[filter_id].active = false)
        delete this.state.activeFilterModels[model].groups[group]
        this.pruneEmptyFilterGroups(this.state.activeFilterModels, model, group)
        setObjectInSession('PFilter' + this.props.options.ks_dashboard_id, this.state.activeFilterModels, 1)
        setObjectInSession('PFilterDataObj' + this.props.options.ks_dashboard_id, this.filters_data, 1)
        this.props.remove([model], [group])
    }


}


