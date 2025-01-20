import livef1
from livef1.utils.constants import interpolation_map

import pandas as pd
import numpy as np
s
import matplotlib.pyplot as plt

session = livef1.get_session(season=2024, meeting_identifier="Spa", session_identifier="Race")
session.data_lake.silver_lake.generate_table("Lap")