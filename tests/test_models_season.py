"""Tests for livef1.models.season.Season."""
from unittest.mock import patch

from livef1.models.season import Season
from livef1.utils.helper import json_parser_for_objects


def test_season_load_skips_jolpica_when_unavailable(season_data):
    """Livetiming-only seasons must not call Jolpica during load()."""
    with patch("livef1.models.season.jolpica_client") as mock_client:
        with patch("livef1.models.circuit.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "Sakhir": {"start_coordinates": [100.0, 50.0], "start_direction": [1.0, 1.0]}
            }
            season = Season(**json_parser_for_objects(season_data))

    mock_client.query.assert_not_called()
    assert len(season.meetings) == 1
    assert season.drivers == {}
    assert season.constructors == {}
    assert season.is_jolpica_available is False
    assert season.is_livetiming_available is True
