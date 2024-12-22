import livef1
import pandas as pd

session = livef1.get_session(season=2024, meeting_identifier="Monza", session_identifier="Race")
res = session.get_data(dataName="Car_Data")
# print(pd.DataFrame(res.value).head().to_markdown())

print(res.value[0:5])

# adapter = livef1.adapters.livetimingf1_adapter.LivetimingF1adapters()
# adapter.get("deneme.json")