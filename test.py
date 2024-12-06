# import os

# def list_files(startpath):
#     for root, dirs, files in os.walk(startpath):
#         if "pyc" in root: continue
#         level = root.replace(startpath, '').count(os.sep)
#         indent = ' ' * 4 * (level)
#         print('{}{}/'.format(indent, os.path.basename(root)))
#         subindent = ' ' * 4 * (level + 1)
#         for f in files:
#             print('{}{}'.format(subindent, f))

# list_files("./livef1")

import livef1

session = livef1.get_meeting(season=2024, meeting_identifier="Spa")

# print(session.meeting_table)

# session = livef1.get_session(season=2024, meeting_identifier="Monza", session_identifier="Race")

# print(session.name)


# season = livef1.get_season(season=2021)

# print(season.meetings_table)
# print(season.season_table)
