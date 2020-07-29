"""Mock objects for testing"""

ROW_POST_PARAMS = {
    "spreadsheet_key": "1234567",
    "worksheet_title": "Tab1",
    "row_values": [
        ["r1c1", "r1c2", "r1c3"],
        ["r2c1", "r2c2", "r2c3"]
    ]
}

ROW_PATCH_PARAMS = {
    "spreadsheet_key": "1234567",
    "worksheet_title": "Tab1",
    "id_column_label": "A",
    "label_value_map": {
        "B": "hello",
        "C": "world"
        }
}

ROW_GET_PARAMS = {
    "spreadsheet_key": "1234567",
    "worksheet_title": "Tab1",
    "id_column_label": "A"
}

ROW_VALUES = ['A', 'B', 'C', 'D', 'E']
