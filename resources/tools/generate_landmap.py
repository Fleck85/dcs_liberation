import pickle

import dcs

m = dcs.Mission()
m.load_file("./cau_terrain.miz")

landmap = []
for plane_group in m.country("USA").plane_group:
    landmap.append([(x.position.x, x.position.y) for x in plane_group.points])


# Lake geometry is defined by Russian A-50 groups
lakemap = []
for plane_group in m.country("Russia").plane_group:
    if plane_group.units[0].unit_type == dcs.planes.A_50:
        lakemap.append([(x.position.x, x.position.y) for x in plane_group.points])

with open("../caulandmap.p", "wb") as f:
    pickle.dump(landmap, f)

with open("../caulakemap.p", "wb") as f:
    pickle.dump(lakemap, f)

print(lakemap)