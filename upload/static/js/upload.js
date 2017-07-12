function uploadFormHandler(event) {
    var form, finput, form_data,
        p_message;
    event.preventDefault();
    form = $('#upload_form');
    finput = $('#upload_form input[type=file]');
    form_data = new FormData(form.get(0));
    
    $.ajax({
        url: form.attr('action'),
        type: form.attr('method'),
        contentType: false,
        processData: false,
        data: form_data,
        datatype: 'json',
        success: messages
    });
    p_message = $('#message');
    p_message.html("File for uploading:" + form.find('[name=uploadfile]').val());
    setTimeout(clearMessage, 3000);
}

function messages(data) {
    var p_message;
    p_message = $('#message');
    if ( data.error !== undefined ) {
        p_message.html(Object.keys(data.error).map(function (key) {return key + ":" + data.error[key];}).join(', '));
    }
    setTimeout(clearMessage, 3000);
}

function clearMessage() {
    var p_message;
    p_message = $('#message');
    p_message.html("");
}

function progressViewLoadRequest() {
    $.get({
        url: '/result_data/',
        datatype: 'json',
        success: progressViewLoadData
    });
}

function progressViewLoadData(data) {
    var upload_table, process_table, result_table,
        process_list, file_list,
        tr, td_id, td_name, td_val, val,
        i;
    process_list = data.process_list;
    file_list = data.file_list;
    upload_table = $('#upload_table');
    process_table = $('#process_table');
    result_table = $('#result_table');
    upload_table.find('tr.data-row').remove();
    process_table.find('tr.data-row').remove();
    for (key in process_list) {
        val = process_list[key];
        tr = $('<tr>').attr('id', val['key']).addClass('data-row');
        td_id = $('<td>').html(val['key']);
        td_name = $('<td>').html(val['name']).addClass('data-row');
        td_val = $('<td>').html(val['progress']);
        tr.append(td_id);
        tr.append(td_name);
        tr.append(td_val);
        if (val['process'] == 'upload') {
            upload_table.append(tr);
        } else {
            process_table.append(tr);
        }
    };
    result_table.find('tr.data-row').remove();
    for (i=0; i<file_list.length; ++i) {
        f = file_list[i];
        tr = $('<tr>').attr('id', f['id']).addClass('data-row');
        td_id = $('<td>').html(f['id']);
        td_name = $('<td>').html(f['name']);
        td_val = $('<td>').html(f['result']);
        tr.append(td_id);
        tr.append(td_name);
        tr.append(td_val);
        result_table.append(tr);
    }
}

$(document).ready(function() {
    $('#upload_form').submit(uploadFormHandler);
    setInterval(progressViewLoadRequest, 5000);
});
