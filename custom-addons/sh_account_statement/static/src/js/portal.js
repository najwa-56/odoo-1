$(document).ready(function (e) {
    var customer_start_date = $('#sh_start_date').val();
    var customer_end_date = $('#sh_end_date').val();
    var vendor_start_date = $('#sh_vendor_start_date').val();
    var vendor_end_date = $('#sh_vendor_end_date').val();
	$("#send_cust_btn").on("click", function () {
		$.ajax({
            url: "/my/customer_statements/send",
            data: {'customer_send_statement':true},
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                if (datas.msg){
                	alert(datas.msg);
                }
            },
        });
	});
	$("#send_cust_due_btn").on("click", function () {
		$.ajax({
            url: "/my/customer_statements/send",
            data: {'customer_send_overdue_statement':true},
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                if (datas.msg){
                	alert(datas.msg);
                }
            },
        });
	});
	$("#send_vendor_btn").on("click", function () {
		$.ajax({
            url: "/my/vendor_statements/send",
            data: {'vendor_send_statement':true},
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                if (datas.msg){
                	alert(datas.msg);
                }
            },
        });
	});
	$("#send_vendor_due_btn").on("click", function () {
		$.ajax({
            url: "/my/vendor_statements/send",
            data: {'vendor_send_overdue_statement':true},
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                if (datas.msg){
                	alert(datas.msg);
                }
            },
        });
	});
    $("#filter_send_cust_btn").on("click", function () {
		$.ajax({
            url: "/my/customer_statements/send",
            data: {'customer_send_filter_statement':true},
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                if (datas.msg){
                	alert(datas.msg);
                }
            },
        });
	});
    $('#sh_start_date').on("change",function(){
        selected_start_date = $('#sh_start_date').val();
        selected_end_date = $('#sh_end_date').val();
        if (new Date(selected_start_date) > new Date(selected_end_date)){
            alert('Date from should be less than or equal Date to');
            $('#sh_start_date').val(customer_start_date);
            $('#sh_end_date').val(customer_end_date);
        }
        else if(new Date(selected_end_date) < new Date(selected_start_date)){
            alert('Date to should be greater than or equal Date from');
            $('#sh_start_date').val(customer_start_date);
            $('#sh_end_date').val(customer_end_date);
        }
    });
    $('#sh_end_date').on("change",function(){
        selected_start_date = $('#sh_start_date').val();
        selected_end_date = $('#sh_end_date').val();
        if (new Date(selected_start_date) > new Date(selected_end_date)){
            alert('Date from should be less than or equal Date to');
            $('#sh_start_date').val(customer_start_date);
            $('#sh_end_date').val(customer_end_date);
        }
        else if(new Date(selected_end_date) < new Date(selected_start_date)){
            alert('Date to should be greater than or equal Date from');
            $('#sh_start_date').val(customer_start_date);
            $('#sh_end_date').val(customer_end_date);
        }
    });
    $("#filter_get_statement").on("click", function () {
		$.ajax({
            url: "/my/customer_statements/get",
            data: {'start_date':$('#sh_start_date').val(),'end_date':$('#sh_end_date').val()},
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                location.reload(true);
            },
        });
	});
    $("#filter_send_vend_btn").on("click", function () {
		$.ajax({
            url: "/my/vendor_statements/send",
            data: {'vendor_send_filter_statement':true},
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                if (datas.msg){
                	alert(datas.msg);
                }
            },
        });
	});
    $('#sh_vendor_start_date').on("change",function(){
        vendor_selected_start_date = $('#sh_vendor_start_date').val();
        vendor_selected_end_date = $('#sh_vendor_end_date').val();
        if (new Date(vendor_selected_start_date) > new Date(vendor_selected_end_date)){
            alert('Date from should be less than or equal Date to');
            $('#sh_vendor_start_date').val(vendor_start_date);
            $('#sh_vendor_end_date').val(vendor_end_date);
        }
        else if(new Date(vendor_selected_end_date) < new Date(vendor_selected_start_date)){
            alert('Date to should be greater than or equal Date from');
            $('#sh_vendor_start_date').val(vendor_start_date);
            $('#sh_vendor_end_date').val(vendor_end_date);
        }
    });
    $('#sh_vendor_end_date').on("change",function(){
        vendor_selected_start_date = $('#sh_vendor_start_date').val();
        vendor_selected_end_date = $('#sh_vendor_end_date').val();
        if (new Date(vendor_selected_start_date) > new Date(vendor_selected_end_date)){
            alert('Date from should be less than or equal Date to');
            $('#sh_vendor_start_date').val(vendor_start_date);
            $('#sh_vendor_end_date').val(vendor_end_date);
        }
        else if(new Date(vendor_selected_end_date) < new Date(vendor_selected_start_date)){
            alert('Date to should be greater than or equal Date from');
            $('#sh_vendor_start_date').val(vendor_start_date);
            $('#sh_vendor_end_date').val(vendor_end_date);
        }
    });
    $("#filter_get_vendor_statement").on("click", function () {
		$.ajax({
            url: "/my/vendor_statements/get",
            data: {'start_date':$('#sh_vendor_start_date').val(),'end_date':$('#sh_vendor_end_date').val()},
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                location.reload(true);
            },
        });
	});
});