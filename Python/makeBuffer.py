import sys
sys.path.append("/Users/hirototakaura/opt/anaconda3/lib/python3.8/site-packages")
from osgeo import gdal, ogr, osr
from pyproj import Transformer
import re
import numpy as np
from math import *

from utils import LineConvert_lal_to_xy, PolyConvert_xy_to_lal, PolygonToList

'''
引数: LINESTRINGS(WGS84)
返り値: bufferの座標(WGS84)を左回りに格納した辞書。フォーマットは以下の通り
    cood = {
        'long':[]
        'lat':[]
    }

'''
def makeBuffer(line, sb):
    line_6674 = LineConvert_lal_to_xy(line, 6)
    buffer_6674 = line_6674.Buffer(sb)
    buffer_84 = PolyConvert_xy_to_lal(buffer_6674.ExportToWkt(), 6)
    buffercood_84 = PolygonToList(buffer_84)

    return buffercood_84

if __name__ == '__main__':
    line = ogr.Geometry(ogr.wkbLineString)
    line.AddPoint(135.576042827, 34.657422595805)
    line.AddPoint(135.576152480754, 34.6574106926014)

    cood = makeBuffer(line, 1.75)
    print(cood)
