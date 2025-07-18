import livef1

s = livef1.get_session(
    2025,
    "British",
    "Race"
)


# _create_table(self, level, table_name, source_tables, include_session=False):

@s.create_silver_table(
    table_name = "goktug",
    source_tables = ["WeatherData"],
    include_session = True
)
def weather_process(WeatherData, session):
    print(WeatherData)


s.generate()