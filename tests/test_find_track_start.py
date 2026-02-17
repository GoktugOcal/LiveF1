# """Tests for livef1.data.find_track_start."""
# import pytest
# import pandas as pd
# import numpy as np
# from unittest.mock import patch, MagicMock
# from livef1.data.find_track_start import get_circuit_data, find_starting_coordinates


# def test_get_circuit_data_success():
#     with patch("livef1.data.find_track_start.requests.get") as mock_get:
#         mock_resp = MagicMock()
#         mock_resp.status_code = 200
#         mock_resp.json.return_value = {"circuit_1": {"name": "Sakhir", "years": [2024]}}
#         mock_get.return_value = mock_resp
#         result = get_circuit_data()
#     assert result == {"circuit_1": {"name": "Sakhir", "years": [2024]}}


# def test_get_circuit_data_failure():
#     with patch("livef1.data.find_track_start.requests.get") as mock_get:
#         mock_resp = MagicMock()
#         mock_resp.status_code = 404
#         mock_get.return_value = mock_resp
#         result = get_circuit_data()
#     assert result is None


# def test_find_starting_coordinates():
#     mock_session = MagicMock()
#     car_tel = pd.DataFrame({
#         "LapNo": [1, 1, 2, 2],
#         "DriverNo": [1, 1, 1, 1],
#         "X": [100.0, 200.0, 105.0, 205.0],
#         "Y": [50.0, 60.0, 52.0, 62.0],
#     })
#     mock_session.carTelemetry = car_tel.copy()
#     mock_session.carTelemetry["driver_lap_tuple"] = list(zip(car_tel["DriverNo"], car_tel["LapNo"]))
#     laps = pd.DataFrame({
#         "DriverNo": [1, 1],
#         "LapNo": [1, 2],
#         "PitIn": [None, None],
#         "PitOut": [None, None],
#         "IsDeleted": [False, False],
#     })
#     mock_session.laps = laps
#     start_x, start_y, x_coeff, y_coeff = find_starting_coordinates(mock_session)
#     assert np.isscalar(start_x)
#     assert np.isscalar(start_y)
#     assert x_coeff in (-1.0, 1.0)
#     assert y_coeff in (-1.0, 1.0)
