// #target photoshop

/**
 * @title Module 2: CSV to PSD
 * @version 1.0
 * @author tlcpineda.projects@gmail.com
 * @description Transfer the contents of the CSV file to corresponding PSD files, ready for manual adjustments.
 * @param {Array} action_arr A 2D array describing the actions to be applied to the text layers. This is chapter- and language-sensitive.
 * @param {number} gen_scale Title-specific scale ratio, to compensate conversion from PSD to PDF (prior to writing comments): [0, 1) indicate a shrinkage; and [1, ) indicate a  dilation.
 */
function main(action_arr, gen_scale) {
    // var doc_units = toggle_doc_units();

    var doc = app.activeDocument;
    var doc_name = doc.name;
    var doc_path = doc.path;
    var parent_folder = doc_path.parent;

    // Fetch CSV file contents.
    var csv_file = new File(parent_folder + '/translations.csv');

    // Early termination if CSV file containing translations is not found.
    if (!csv_file.exists) {
        // toggle_doc_units(doc_units);
        return;
    }

    csv_file.open('r');
    csv_file.encoding = 'UTF-8';

    var csv_str = csv_file.read();

    csv_file.close();

    var csv_arr = parse_csv(csv_str);

    // Extract page marker from name of doc.
    var match = doc_name.match(/[\s_](\d{4})\.psd$/i);  // Get the page number, just before the extension name, and after the last underscore or space.
    var page_mark = match && match.length > 1 ? match[1] : null;

    // Early termination if page_mark on filename is not found.
    if (page_mark === null) {
        // toggle_doc_units(doc_units);
        return;
    }

    // Slice csv_arr for elements with matching page marker, before transfer text to currently open file.
    var doc_data = [];

    for (var i=0; i<csv_arr.length; i++) {
        if (csv_arr[i][0].toUpperCase() === page_mark.toUpperCase()) doc_data.push(csv_arr[i]);
    }

    for (var j=0; j<doc_data.length; j++) {
        var row = doc_data[j];

        transfer_text(
            doc,
            row[1] * gen_scale,
            row[2] * gen_scale,
            row[3] * gen_scale,
            row[4] * gen_scale,
            row[5]
        );
    }

    // Apply actions only if defined.
    if (action_arr && action_arr.length>0) {
        apply_actions_to_text_layers(doc, action_arr);
    }

    // toggle_doc_units(doc_units);
}


/**
 * Transfer the contents of the line from the CSV to the PSD file.
 * @param {Object} doc The currently open PSD file
 * @param {float} x0_norm x-coordinate of the text box, normalised to the width of the source PDF file.
 * @param {float} y0_norm y-coordinate of the text box, normalised to the height of the source PDF file.
 * @param {float} w_norm width of the text box, normalised to the width of the source PDF file.
 * @param {float} h_norm height of the text box, normalised to the height of the source PDF file.
 * @param {string} contents The contents of the text annotation from the PDF file.
 */
function transfer_text(doc, x0_norm, y0_norm, w_norm, h_norm, contents) {
    var text_group_name = "TEXT";
    var text_group = null;

    // Find Group with "TEXT" (case-insensitive) in the name; otherwise create Group.
    for (var i=0; i<doc.layerSets.length; i++) {
        if (doc.layerSets[i].name.toUpperCase().indexOf(text_group_name) !== -1) {
            text_group = doc.layerSets[i]
            break;
        }
    }

    if (text_group === null) {
        text_group = doc.layerSets.add();
        text_group.name = text_group_name;
    }

    // Create text layer within "TEXT" group.
    var new_layer = text_group.artLayers.add();

    new_layer.kind = LayerKind.TEXT;

    var text_layer = new_layer.textItem;

    text_layer.kind = TextType.PARAGRAPHTEXT;

    var w_doc = doc.width.as('px');
    var h_doc = doc.height.as('px');

    text_layer.width = w_norm * w_doc;
    text_layer.height = h_norm * h_doc;
    text_layer.position = [x0_norm * w_doc, y0_norm * h_doc];
    text_layer.contents = contents;
    text_layer.justification = Justification.CENTER;
}


/**
 * Transform the string content of a CSV file to an array.
 * @param {string} csv_str The contents of the CSV file
 * @returns {Array} csv_arr An array representing the contents of the CSV file with each line as an element of the array.
 */
function parse_csv(csv_str) {
    var csv_arr = [];
    var lines = csv_str.split(/\r\n|\n/);

    // Truncate header row.
    for (var i=1; i<lines.length; i++) {
        var lines_split = lines[i].split(',');

        if (lines_split.length<6) continue; // Stop processing the line, possibly malformed.

        var text = lines_split.slice(5).join(',');
        var replacement_arr = [
            ['""', '"'],
            ['<>', '\r'],
            ['(?<!\\.)(\\.\\.|\\.{4,})(?!\\.)', '...']  // Replace two dots, or 4 or more dots by proper ellipsis.
            // ['(\\?+)(!+)', '$2$1']  // Interchange position of marks. (not strict in SOLE)
        ]

        var line = lines_split.slice(0, 5);
        var is_valid = true;

        // Convert items to float, except the first (remains as string).
        for (var k=1; k<line.length; k++) {
            var val = parseFloat(line[k]);

            // Check if conversion
            if (isNaN(val)) {
                is_valid = false;
                break;
            } else {
                line[k] = val;
            }
        }

        if (!is_valid) continue; // Stop processing the line, possibly malformed.

        // Strip enclosing quotation marks.
        var text_terminal = text.length - 1;

        if (text.charAt(0)==='"' && text.charAt(text_terminal)==='"') {
            text = text.substring(1, text_terminal);
        }

        // Clean up text.
        for (var j=0; j<replacement_arr.length; j++ ) {
            text = text.replace(new RegExp(replacement_arr[j][0], 'g'), replacement_arr[j][1]);
        }

        csv_arr.push(line.concat([text]));
    }

    return csv_arr
}


/**
 * Change the ruler units to PIXELS, if not set already.
 * @param {Enumerator} curr_units The current unit that is set.
 * @returns {Enumerator} doc_units The unit to be set
 */
function toggle_doc_units(curr_units) {
    var app_pref = app.preferences;
    var doc_units = app_pref.rulerUnits;

    if (typeof curr_units === 'undefined' || curr_units === null) {
        // Set up to Units.PIXELS, if not yet set.
        if (doc_units !== Units.PIXELS) app_pref.rulerUnits = Units.PIXELS;
    } else {
        // Revert to original app setting
        app_pref.rulerUnits = curr_units;
    }

    return doc_units;
}


/**
 * Apply pre-defined actions to each text layer.
 * @param {Document} doc The currently active file
 * @param {Array} action_groups A 2D array (chapter- and language-sensitive) describing the actions to be applied to each text layer.
 */
function apply_actions_to_text_layers(doc, action_arr) {
    var text_group_name = "TEXT";
    var text_group = null;

    // Find Group with "TEXT" (case-insensitive) in the name.
    for (var i=0; i<doc.layerSets.length; i++) {
        if (doc.layerSets[i].name.toUpperCase().indexOf(text_group_name) !== -1) {
            text_group = doc.layerSets[i]
            break;
        }
    }

    if (!text_group) return; // Early termination if "TEXT" group is not found; not expected.

    // Loop through layers in the group, and apply action(s).
    var layers = text_group.artLayers;
    for (var j=0; j<layers.length; j++) {
        doc.activeLayer = layers[j];

        // Loop through each action, and apply to current layer.
        for (var k=0; k<action_arr.length; k++) {
            app.doAction(action_arr[k][0], action_arr[k][1])
        }
    }
}


// Run the main function.
main(
[
    ["Main Font", "AMIMARU - 2"]
],
    1.0
);

