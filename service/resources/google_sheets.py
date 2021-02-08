"""Google Sheets module"""
#pylint: disable=too-few-public-methods
import os
import json
import traceback
import falcon
import jsend
import gspread
from .hooks import validate_access

CREDENTIALS_FILE = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
ERR_MISSING_SPREADSHEET_KEY = 'Missing spreadsheet_key parameter in request'
ERR_MISSING_WORKSHEET_TITLE = 'Missing worksheet_title parameter in request'
ERR_MISSING_ID_COLUMN_LABEL = 'Missing id_column_label parameter in request'
ERR_MISSING_LABEL_VALUE_MAP = 'Missing label_value_map parameter in request'
ERR_MISSING_ROW_VALUES = 'Missing row_values parameter in request'
ERR_CELL_VALUE_NOT_FOUND = 'A cell with the corresponding value was not found'
ERR_MISSING_COLUMN = 'Missing column_label parameter in request'
ERR_MISSING_VALUE = 'Missing value parameter in request'

@falcon.before(validate_access)
class Rows():
    """Rows class"""
    def on_post(self, _req, resp):
        #pylint: disable=no-self-use
        """
            append a new row
        """
        print("Rows.on_post")
        request_params_json = None
        try:
            request_body = _req.bounded_stream.read()
            request_params_json = json.loads(request_body)
            self.validate_post_params(request_params_json)

            worksheet = get_spreadsheet(
                request_params_json['spreadsheet_key'],
                request_params_json['worksheet_title']
            )
            row = request_params_json['row_values']
            worksheet.append_rows(row)

            resp.body = json.dumps(jsend.success({
                'row': row
            }))

        except Exception as err:    # pylint: disable=broad-except
            resp = process_error(err, resp, request_params_json)

    def on_get(self, _req, resp):
        """search rows"""
        print("Rows.on_get")
        try:
            self.validate_get_params(_req.params)
            column = _req.get_param('column_label')
            value = _req.get_param('value')
            worksheet = get_spreadsheet(
                _req.get_param('spreadsheet_key'),
                _req.get_param('worksheet_title')
            )

            column_idx = gspread.utils.a1_to_rowcol(column + '1')[1]
            cells_found = worksheet.findall(value, in_column=column_idx)
            if len(cells_found) == 0:
                raise gspread.exceptions.CellNotFound

            rows_ids = list(map(lambda cell: cell.row, cells_found))
            last_col_idx = get_last_column_index(worksheet)

            ranges = []
            for row_id in rows_ids:
                ranges.append(
                    gspread.utils.rowcol_to_a1(row_id, 1) +
                    ':' +
                    gspread.utils.rowcol_to_a1(row_id, last_col_idx)
                )
            rows_found = worksheet.batch_get(ranges)
            # batch_get returns [[[a, b, c]], [[a, b, c]], [[a, b, c]]]
            rows = [row[0] for row in rows_found]

            resp.body = json.dumps(rows)
            resp.status = falcon.HTTP_200
        except gspread.exceptions.CellNotFound as err:
            print("{0}".format(err))
            print(traceback.format_exc())
            resp.body = json.dumps(
                jsend.error(
                    "{0} - column_label={1} value={2}".format(
                        ERR_CELL_VALUE_NOT_FOUND,
                        column,
                        value)
                )
            )
            resp.status = falcon.HTTP_404
        except Exception as err:    # pylint: disable=broad-except
            resp = process_error(err, resp, _req.params)

    @staticmethod
    def validate_post_params(params_json):
        """Enforce parameter inputs for post method"""
        validate_spreadsheet_params(params_json)

        if 'row_values' not in params_json:
            raise Exception(ERR_MISSING_ROW_VALUES)

    @staticmethod
    def validate_get_params(params):
        """Enforce parameter inputs for get method"""
        validate_spreadsheet_params(params)

        if 'column_label' not in params:
            raise Exception(ERR_MISSING_COLUMN)

        if 'value' not in params:
            raise Exception(ERR_MISSING_VALUE)

@falcon.before(validate_access)
class Row():
    """Row class"""
    def on_patch(self, _req, resp, row_id):
        #pylint: disable=no-self-use
        """
            update an existing row
        """
        print("Row.on_patch")
        request_body = _req.bounded_stream.read()
        request_params_json = json.loads(request_body)
        try:
            self.validate_patch_params(request_params_json)

            worksheet = get_spreadsheet(
                request_params_json['spreadsheet_key'],
                request_params_json['worksheet_title']
            )
            column_idx = gspread.utils.a1_to_rowcol(request_params_json['id_column_label'] + '1')[1]
            row_to_edit_idx = worksheet.find(row_id, in_column=column_idx).row
            updates = []
            for column_label, column_value in request_params_json['label_value_map'].items():
                updates.append({
                    'range': column_label + str(row_to_edit_idx),
                    'values': [[column_value]]
                })
            worksheet.batch_update(updates)

            resp.body = json.dumps(jsend.success({
                'updates': updates
            }))
            resp.status = falcon.HTTP_200
        except gspread.exceptions.CellNotFound as err:
            print("CellNotFound Error:")
            print("{0}".format(err))
            print(traceback.format_exc())
            resp.body = json.dumps(
                jsend.error(
                    "{0} - value={1}".format(ERR_CELL_VALUE_NOT_FOUND, row_id)))
            resp.status = falcon.HTTP_404
        except Exception as err:   # pylint: disable=broad-except
            resp = process_error(err, resp, request_params_json)

    def on_get(self, _req, resp, row_id):
        #pylint: disable=no-self-use
        """
            get row
        """
        print("Row.on_get")
        try:
            params = _req.params
            self.validate_get_params(params)

            worksheet = get_spreadsheet(
                params['spreadsheet_key'],
                params['worksheet_title']
            )
            column_idx = gspread.utils.a1_to_rowcol(params['id_column_label'] + '1')[1]
            row_idx = worksheet.find(row_id, in_column=column_idx).row
            row = worksheet.row_values(row_idx)
            resp.body = json.dumps(row)
            resp.status = falcon.HTTP_200
        except gspread.exceptions.CellNotFound as err:
            print("{0}".format(err))
            print(traceback.format_exc())
            resp.body = json.dumps(
                jsend.error(
                    "{0} - value={1}".format(ERR_CELL_VALUE_NOT_FOUND, row_id)))
            resp.status = falcon.HTTP_404
        except Exception as err:    # pylint: disable=broad-except
            resp = process_error(err, resp, params)

    @staticmethod
    def validate_patch_params(params_json):
        """Enforce parameter inputs for patch method"""
        validate_spreadsheet_params(params_json)

        if 'id_column_label' not in params_json:
            raise Exception(ERR_MISSING_ID_COLUMN_LABEL)

        if 'label_value_map' not in params_json:
            raise Exception(ERR_MISSING_LABEL_VALUE_MAP)

    @staticmethod
    def validate_get_params(params_json):
        """Enforce parameter inputs for get method"""
        validate_spreadsheet_params(params_json)

        if 'id_column_label' not in params_json:
            raise Exception(ERR_MISSING_ID_COLUMN_LABEL)

def process_error(err, resp, params):
    """ common error handler """
    err_msg = "{0}".format(err)
    print("Encountered an error:")
    print(err_msg)
    print(json.dumps(params))
    print(traceback.format_exc())
    resp.body = json.dumps(jsend.error(err_msg))
    resp.status = falcon.HTTP_500
    return resp

def get_spreadsheet(spreadsheet_key, worksheet):
    """ returns the specified worksheet """
    gc = gspread.service_account(filename=CREDENTIALS_FILE) # pylint: disable=invalid-name
    return gc.open_by_key(spreadsheet_key).worksheet(worksheet)

def validate_spreadsheet_params(params_json):
    """ Check parameters for accessing spreadsheet """
    if 'spreadsheet_key' not in params_json:
        raise Exception(ERR_MISSING_SPREADSHEET_KEY)

    if 'worksheet_title' not in params_json:
        raise Exception(ERR_MISSING_WORKSHEET_TITLE)

def get_last_column_index(worksheet):
    """
        return index of the last column
    """
    row = worksheet.row_values(1)
    return len(row)
