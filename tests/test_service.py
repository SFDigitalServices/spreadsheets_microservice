# pylint: disable=redefined-outer-name
"""Tests for microservice"""
import json
from unittest.mock import patch, Mock
import jsend
import pytest
from falcon import testing
import gspread
import mocks
import service.microservice
from service.resources.google_sheets import Rows, Row

CLIENT_HEADERS = {
    "ACCESS_KEY": "1234567"
}

@pytest.fixture()
def client():
    """ client fixture """
    return testing.TestClient(app=service.microservice.start_service(), headers=CLIENT_HEADERS)

@pytest.fixture
def mock_env_access_key(monkeypatch):
    """ mock environment access key """
    monkeypatch.setenv("ACCESS_KEY", CLIENT_HEADERS["ACCESS_KEY"])
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "google-credentials.json")

@pytest.fixture
def mock_env_no_access_key(monkeypatch):
    """ mock environment with no access key """
    monkeypatch.delenv("ACCESS_KEY", raising=False)

def test_default_error(client, mock_env_access_key):
    # pylint: disable=unused-argument
    """Test default error response"""
    response = client.simulate_get('/some_page_that_does_not_exist')

    assert response.status_code == 404

    expected_msg_error = jsend.error('404 - Not Found')
    assert json.loads(response.content) == expected_msg_error

def test_google_sheet_spreadsheet_params_validation():
    """ Test validate_spreadsheet_params """
    with pytest.raises(Exception):
        Rows.validate_post_params({
            k:v for k, v in mocks.ROW_POST_PARAMS.items() if k != 'spreadsheet_key'
        })

    with pytest.raises(Exception):
        Rows.validate_post_params({
            k:v for k, v in mocks.ROW_POST_PARAMS.items() if k != 'worksheet_title'
        })

def test_google_sheet_rows_post_validation():
    """Test rows post parameters validation"""
    with pytest.raises(Exception):
        Rows.validate_post_params({
            k:v for k, v in mocks.ROW_POST_PARAMS.items() if k != 'row_values'
        })

def test_google_sheet_rows_get_validation():
    """Test rows get parameter validation"""
    with pytest.raises(Exception):
        Rows.validate_get_params({
            k:v for k, v in mocks.ROWS_GET_PARAMS.items() if k != 'column_label'
        })

    with pytest.raises(Exception):
        Rows.validate_get_params({
            k:v for k, v in mocks.ROWS_GET_PARAMS.items() if k != 'value'
        })

def test_google_sheet_row_patch_validation():
    """Test row patch parameters validation"""
    with pytest.raises(Exception):
        Row.validate_patch_params({
            k:v for k, v in mocks.ROW_PATCH_PARAMS.items() if k != 'id_column_label'
        })

    with pytest.raises(Exception):
        Row.validate_patch_params({
            k:v for k, v in mocks.ROW_PATCH_PARAMS.items() if k != 'label_value_map'
        })

def test_google_sheet_row_get_validation():
    """Test row get parameter validation"""
    with pytest.raises(Exception):
        Row.validate_get_params({
            k:v for k, v in mocks.ROW_GET_PARAMS.items() if k != 'id_column_label'
        })

def test_google_sheet_post_no_access_key(mock_env_no_access_key, client):
    # pylint: disable=unused-argument
    # mock_env_no_access_key is a fixture and creates a false positive for pylint
    """Test welcome request with no ACCESS_key environment var set"""
    response = client.simulate_post(
        '/rows',
        json=mocks.ROW_POST_PARAMS
    )
    assert response.status_code == 403

def test_google_sheet_post(mock_env_access_key, client):
    # pylint: disable=unused-argument
    """Test post endpoint"""
    with patch('service.resources.google_sheets.gspread.service_account') as mock_client:
        # happy path
        resp = client.simulate_post(
            '/rows',
            json=mocks.ROW_POST_PARAMS
        )
        assert resp.status_code == 200

        # error in gspread
        mock_client.side_effect = Exception('Error in gspread')
        resp = client.simulate_post(
            '/rows',
            json=mocks.ROW_POST_PARAMS
        )
        assert resp.status_code == 500

def test_google_sheet_patch(mock_env_access_key, client):
    # pylint: disable=unused-argument
    """Test patch endpoint"""

    # happy path
    with patch('service.resources.google_sheets.gspread.service_account') as mock_client:
        resp = client.simulate_patch(
            '/rows/21',
            json=mocks.ROW_PATCH_PARAMS
        )
        assert resp.status_code == 200

    # error in gspread
    with patch('service.resources.google_sheets.gspread.service_account') as mock_client:
        mock_client.side_effect = Exception('Error in gspread')
        resp = client.simulate_patch(
            '/rows/1',
            json=mocks.ROW_PATCH_PARAMS
        )
        assert resp.status_code == 500

    # value not found
    with patch('service.resources.google_sheets.gspread.service_account') as mock_client:
        mock_client.return_value.open_by_key.return_value.worksheet.return_value.find.side_effect = gspread.exceptions.CellNotFound #pylint: disable=line-too-long
        resp = client.simulate_patch(
            '/rows/32',
            json=mocks.ROW_PATCH_PARAMS
        )
        assert resp.status_code == 404

def test_google_sheet_get(mock_env_access_key, client):
    # pylint: disable=unused-argument
    """Test get endpoint"""

    # happy path
    with patch('service.resources.google_sheets.gspread.service_account') as mock_client:
        mock_client.return_value.open_by_key.return_value.worksheet.return_value.row_values.return_value = mocks.ROW_VALUES #pylint: disable=line-too-long
        resp = client.simulate_get(
            '/rows/23',
            params=mocks.ROW_GET_PARAMS
        )
        assert resp.status_code == 200

    # value not found
    with patch('service.resources.google_sheets.gspread.service_account') as mock_client:
        mock_client.return_value.open_by_key.return_value.worksheet.return_value.find.side_effect = gspread.exceptions.CellNotFound #pylint: disable=line-too-long
        resp = client.simulate_get(
            '/rows/007',
            params=mocks.ROW_GET_PARAMS
        )
        assert resp.status_code == 404

    # generic error
    with patch('service.resources.google_sheets.gspread.service_account') as mock_client:
        mock_client.side_effect = Exception('Error in gspread')
        resp = client.simulate_get(
            '/rows/007',
            params=mocks.ROW_GET_PARAMS
        )
        assert resp.status_code == 500

def test_google_sheet_rows_get(mock_env_access_key, client):
    # pylint: disable=unused-argument
    """ Test the rows get functionality which is really a find """

    #happy path
    with patch('service.resources.google_sheets.gspread.service_account') as mock_client:
        obj1 = Mock()
        obj1.row = 1
        obj2 = Mock()
        obj2.row = 2
        mock_client.return_value.open_by_key.return_value.worksheet.return_value.findall.return_value = [   #pylint: disable=line-too-long
            obj1,
            obj2
        ]
        mock_client.return_value.open_by_key.return_value.worksheet.return_value.row_values.return_value = mocks.ROW_VALUES #pylint: disable=line-too-long
        mock_client.return_value.open_by_key.return_value.worksheet.return_value.batch_get.return_value = mocks.BATCH_GET #pylint: disable=line-too-long

        resp = client.simulate_get(
            '/rows',
            params=mocks.ROWS_GET_PARAMS
        )
        assert resp.status_code == 200

    # value not found
    with patch('service.resources.google_sheets.gspread.service_account') as mock_client:
        mock_client.return_value.open_by_key.return_value.worksheet.return_value.findall.return_value = [] #pylint: disable=line-too-long
        resp = client.simulate_get(
            '/rows',
            params=mocks.ROWS_GET_PARAMS
        )
        assert resp.status_code == 404

    # generic error
    with patch('service.resources.google_sheets.gspread.service_account') as mock_client:
        mock_client.side_effect = Exception('Error in gspread')
        resp = client.simulate_get(
            '/rows',
            params=mocks.ROWS_GET_PARAMS
        )
        assert resp.status_code == 500
