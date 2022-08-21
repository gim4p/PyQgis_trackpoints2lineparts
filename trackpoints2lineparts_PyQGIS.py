import qgis.core
from PyQt5.QtCore import QVariant
import numpy as np

##### SET what we need
nth_points2line = 20  ##########!!!!!!!!! manually SPECIFY every nth points is one profile

#####
# laye_r = QgsProject.instance().mapLayersByName("path/shapefilename.shp")[0]
layer_in = iface.activeLayer()
feature_s = layer_in.getFeatures()
layer_provider = layer_in.dataProvider()

field_name = "X_coo"
field_index = layer_in.fields().indexFromName(field_name)
if field_index == -1:
    layer_provider.addAttributes([QgsField("X_coo", QVariant.Double), QgsField("Y_coo", QVariant.Double)])
    layer_in.updateFields()
layer_in.commitChanges()
feature_s = layer_in.getFeatures()

#####
X_calc = []
Y_calc = []
points_calc = []
lineidx_list = []
time_list = []
comment_list = []
cnt = 0

layer_in.startEditing()
for fea_t in feature_s:
    geom = fea_t.geometry().asPoint()
    fea_t["X_coo"] = geom[0]
    fea_t["Y_coo"] = geom[1]
    layer_in.updateFeature(fea_t)

    X_calc.append(geom[0])
    Y_calc.append(geom[1])
    points_calc.append(QgsPoint(geom))

    time_list.append(fea_t["time"])
    comment_list.append(fea_t["comment"])

    if round(cnt / nth_points2line) == cnt / nth_points2line:
        lineidx_list.append(cnt)

    cnt = cnt + 1

layer_in.commitChanges()

if cnt == len(layer_in) and lineidx_list[-1] != len(layer_in):
    lineidx_list.append(cnt)

#### insert idices into index list for coordinates that have big gaps inbetween
gaps = np.sqrt((np.diff(X_calc)) ** 2 + (np.diff(Y_calc)) ** 2)
idx_gaps = list(np.where(gaps > np.median(gaps) * 3)[0]) ##########!!!!!!!!! manually SPECIFY how big the gap can be
lineidx_list = np.sort(lineidx_list + [x + 1 for x in idx_gaps])

#### create temporary line shapefile and put lines and attributes into it
layer_out = QgsVectorLayer("LineString?crs=epsg:4326", "temp", "memory")
pr = layer_out.dataProvider()
pr.addAttributes([
    QgsField("time", QVariant.Double),
    QgsField("comment", QVariant.String)])
layer_out.updateFields()

QgsProject.instance().addMapLayer(layer_out) # add the layer in QGIS project
layer_out.startEditing()  # start editing layer
feat = QgsFeature(layer_out.fields())  # Create the feature

#### make line parts as single objects in shapefile
lines = range(len(lineidx_list) - 1)
lines_shape = []

for line in lines:
    feat["time"] = time_list[lineidx_list[line]]
    feat["comment"] = comment_list[lineidx_list[line]]
    feat.setGeometry( QgsGeometry.fromPolyline(points_calc[lineidx_list[line]: lineidx_list[line + 1]]) )
    layer_out.addFeature(feat)  # add the feature to the layer

layer_out.endEditCommand()  # stop editing
layer_out.commitChanges()  # save changes


