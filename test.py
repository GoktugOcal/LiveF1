from livef1.adapters import livetimingf1_adapter, livetimingF1_request
from livef1.adapters.jolpicaf1_adapter import jolpica_client
from urllib.parse import urljoin


season_identifier = 2025
season_data_livetiming = livetimingF1_request(urljoin(str(season_identifier) + "/", "Index.json"))
season_races = jolpica_client.query().season(season_identifier).get_races().data.races

print(season_data_livetiming)
print(season_races)