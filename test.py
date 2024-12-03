import livef1

# df = livef1.get_session(
#     2024,
#     "Monza",
#     "Race"
# )

# df = livef1.get_meeting(
#     2024,
#     "Monza"
# )

# session = livef1.get_session(2021, "emilian", "practice 2")
# print(session.meeting.name, session.name)

# print(help(livef1.get_session))

# meeting = livef1.get_meeting(2024, "Emmilian")
# print(meeting.name)

# import os

# def list_files(startpath):
#     for root, dirs, files in os.walk(startpath):
#         if "__pycache__" in root: continue
#         level = root.replace(startpath, '').count(os.sep)
#         indent = ' ' * 4 * (level)
#         print('{}{}/'.format(indent, os.path.basename(root)))
#         subindent = ' ' * 4 * (level + 1)
#         for f in files:
#             print('{}{}'.format(subindent, f))

# print(list_files("./livef1"))

meeting = livef1.get_meeting(season=2024, meeting_identifier="spas")