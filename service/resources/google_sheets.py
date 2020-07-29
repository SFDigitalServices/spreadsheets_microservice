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

@falcon.before(validate_access)
class Rows():
    """Rows class"""
    def on_patch(self, _req, resp, row_id):
        #pylint: disable=no-self-use
        """
            update an existing row
        """
        print("Rows.on_patch")
        try:
            request_body = _req.bounded_stream.read()
            request_params_json = json.loads(request_body)
            validate_patch_params(request_params_json)

            gc = gspread.service_account(filename=CREDENTIALS_FILE) # pylint: disable=invalid-name
            worksheet = gc.open_by_key(
                request_params_json['spreadsheet_key']
            ).worksheet(
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
            err_msg = "{0}".format(err)
            print(err_msg)
            print(traceback.format_exc())
            resp.body = json.dumps(jsend.error(err_msg))
            resp.status = falcon.HTTP_500

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
            validate_post_params(request_params_json)

            gc = gspread.service_account(filename=CREDENTIALS_FILE) # pylint: disable=invalid-name
            worksheet = gc.open_by_key(
                request_params_json['spreadsheet_key']
            ).worksheet(
                request_params_json['worksheet_title']
            )
            row = request_params_json['row_values']
            worksheet.append_rows(row)

            resp.body = json.dumps(jsend.success({
                'row': row
            }))

        except Exception as err:    # pylint: disable=broad-except
            err_msg = "{0}".format(err)
            print("Encountered error:")
            print(err_msg)
            print(json.dumps(request_params_json))
            print(traceback.format_exc())
            resp.body = json.dumps(jsend.error(err_msg))
            resp.status = falcon.HTTP_500

    def on_get(self, _req, resp, row_id):
        #pylint: disable=no-self-use
        """
            get row
        """
        print("Rows.on_get")
        try:
            request_body = _req.bounded_stream.read()
            request_params_json = json.loads(request_body)
            validate_get_params(request_params_json)

            gc = gspread.service_account(filename=CREDENTIALS_FILE) # pylint: disable=invalid-name
            worksheet = gc.open_by_key(
                request_params_json['spreadsheet_key']
            ).worksheet(
                request_params_json['worksheet_title']
            )
            column_idx = gspread.utils.a1_to_rowcol(request_params_json['id_column_label'] + '1')[1]
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
            err_msg = "{0}".format(err)
            print("Encountered error:")
            print(err_msg)
            print(json.dumps(request_params_json))
            print(traceback.format_exc())
            resp.body = json.dumps(jsend.error(err_msg))
            resp.status = falcon.HTTP_500

def validate_spreadsheet_params(params_json):
    """ Check parameters for accessing spreadsheet """
    if 'spreadsheet_key' not in params_json:
        raise Exception(ERR_MISSING_SPREADSHEET_KEY)

    if 'worksheet_title' not in params_json:
        raise Exception(ERR_MISSING_WORKSHEET_TITLE)

def validate_patch_params(params_json):
    """Enforce parameter inputs for patch method"""
    validate_spreadsheet_params(params_json)

    if 'id_column_label' not in params_json:
        raise Exception(ERR_MISSING_ID_COLUMN_LABEL)

    if 'label_value_map' not in params_json:
        raise Exception(ERR_MISSING_LABEL_VALUE_MAP)

def validate_post_params(params_json):
    """Enforce parameter inputs for post method"""
    validate_spreadsheet_params(params_json)

    if 'row_values' not in params_json:
        raise Exception(ERR_MISSING_ROW_VALUES)

def validate_get_params(params_json):
    """Enforce parameter inputs for get method"""
    validate_spreadsheet_params(params_json)

    if 'id_column_label' not in params_json:
        raise Exception(ERR_MISSING_ID_COLUMN_LABEL)
