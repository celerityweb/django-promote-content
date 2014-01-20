function clearFk(win) {
    var name = windowname_to_id(win.name);
    var elem = document.getElementById(name);
    var selected_elem = document.getElementById("selected_" + name);
    console.log(selected_elem);
    if (elem) {
        elem.value = '';
    };
    if (selected_elem) {
        selected_elem.innerHTML = '';
    };
    win.close();
}


function dismissCurateModify(win, newId, newRepr) {
    newId = html_unescape(newId);
    newRepr = html_unescape(newRepr);
    var name = windowname_to_id(win.name);
    var name = name.replace(/^lookup_/, '');
    var elem = document.getElementById(name);
    var selected_elem = document.getElementById("selected_" + name);
    elem.value = newId;
    selected_elem.innerHTML = newRepr;
    win.close();
};

// function curationControls(win, isSet) {
//     var name = windowname_to_id(win.name);
//     var name = name.replace(/^lookup_id_/, '');
//     edit_controls = document.getElementById("edit_controls_" + name);
//     add_controls = document.getElementById("add_controls_" + name);
//     if (isSet) {
//         edit_controls.style.display = 'block';
//         add_controls.style.display = 'none';
//     } else {
//         edit_controls.style.display = 'none';
//         add_controls.style.display = 'block';
//     };
// };

function showCurateModify(triggeringLink) {
    var name = triggeringLink.id.replace(/^add_|edit_|delete_/, '');
    console.log(name);
    name = id_to_windowname(name);
    var href;
    if (triggeringLink.href.search(/\?/) >= 0) {
        href = triggeringLink.href + '&_popup=1';
    } else {
        href = triggeringLink.href + '?_popup=1';
    }
    var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
    win.focus();
    return false;
};
