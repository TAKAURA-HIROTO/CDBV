import sys
sys.path.append("/Users/hirototakaura/opt/anaconda3/lib/python3.8/site-packages")
from osgeo import gdal, ogr, osr
from pyproj import Transformer
from geopy.distance import geodesic
import pandas as pd
import re
import numpy as np
from math import *
import argparse


'''
Vincenty法(順解法)
始点の座標(緯度経度)と方位角と距離から、終点の座標と方位角を求める
:param lat: 緯度
:param lon: 経度
:param azimuth: 方位角
:param distance: 距離
:param ellipsoid: 楕円体
:return: 終点の座標、方位角
'''
def vincenty_direct(lat, lon, azimuth, distance, ellipsoid=None):
    ELLIPSOID_GRS80 = 1 # GRS80
    ELLIPSOID_WGS84 = 2 # WGS84

    # 楕円体ごとの長軸半径と扁平率
    GEODETIC_DATUM = {
        ELLIPSOID_GRS80: [
            6378137.0,         # [GRS80]長軸半径
            1 / 298.257222101, # [GRS80]扁平率
        ],
        ELLIPSOID_WGS84: [
            6378137.0,         # [WGS84]長軸半径
            1 / 298.257223563, # [WGS84]扁平率
        ],
    }

    # 反復計算の上限回数
    ITERATION_LIMIT = 1000

    # 計算時に必要な長軸半径(a)と扁平率(ƒ)を定数から取得し、短軸半径(b)を算出する
    # 楕円体が未指定の場合はGRS80の値を用いる
    a, ƒ = GEODETIC_DATUM.get(ellipsoid, GEODETIC_DATUM.get(ELLIPSOID_GRS80))
    b = (1 - ƒ) * a

    # ラジアンに変換する(距離以外)
    φ1 = radians(lat)
    λ1 = radians(lon)
    α1 = radians(azimuth)
    s = distance

    sinα1 = sin(α1)
    cosα1 = cos(α1)

    # 更成緯度(補助球上の緯度)
    U1 = atan((1 - ƒ) * tan(φ1))

    sinU1 = sin(U1)
    cosU1 = cos(U1)
    tanU1 = tan(U1)

    σ1 = atan2(tanU1, cosα1)
    sinα = cosU1 * sinα1
    cos2α = 1 - sinα ** 2
    u2 = cos2α * (a ** 2 - b ** 2) / (b ** 2)
    A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))

    # σをs/(b*A)で初期化
    σ = s / (b * A)

    # 以下の計算をσが収束するまで反復する
    # 地点によっては収束しないことがあり得るため、反復回数に上限を設ける
    for i in range(ITERATION_LIMIT):
        cos2σm = cos(2 * σ1 + σ)
        sinσ = sin(σ)
        cosσ = cos(σ)
        Δσ = B * sinσ * (cos2σm + B / 4 * (cosσ * (-1 + 2 * cos2σm ** 2) - B / 6 * cos2σm * (-3 + 4 * sinσ ** 2) * (-3 + 4 * cos2σm ** 2)))
        σʹ = σ
        σ = s / (b * A) + Δσ

        # 偏差が.000000000001以下ならbreak
        if abs(σ - σʹ) <= 1e-12:
            break
    else:
        # 計算が収束しなかった場合はNoneを返す
        return None

    # σが所望の精度まで収束したら以下の計算を行う
    x = sinU1 * sinσ - cosU1 * cosσ * cosα1
    φ2 = atan2(sinU1 * cosσ + cosU1 * sinσ * cosα1, (1 - ƒ) * sqrt(sinα ** 2 + x ** 2))
    λ = atan2(sinσ * sinα1, cosU1 * cosσ - sinU1 * sinσ * cosα1)
    C = ƒ / 16 * cos2α * (4 + ƒ * (4 - 3 * cos2α))
    L = λ - (1 - C) * ƒ * sinα * (σ + C * sinσ * (cos2σm + C * cosσ * (-1 + 2 * cos2σm ** 2)))
    λ2 = L + λ1

    α2 = atan2(sinα, -x) + pi

    return {
        'lat': degrees(φ2),     # 緯度
        'lon': degrees(λ2),     # 経度
        'azimuth': degrees(α2), # 方位角
    }




'''
Vincenty法(逆解法)
2地点の座標(緯度経度)から、距離と方位角を計算する
:param lat1: 始点の緯度
:param lon1: 始点の経度
:param lat2: 終点の緯度
:param lon2: 終点の経度
:param ellipsoid: 楕円体
:return: 距離と方位角
'''
def vincenty_inverse(lat1, lon1, lat2, lon2, ellipsoid=None):

    ELLIPSOID_GRS80 = 1 # GRS80
    ELLIPSOID_WGS84 = 2 # WGS84

    # 楕円体ごとの長軸半径と扁平率
    GEODETIC_DATUM = {
        ELLIPSOID_GRS80: [
            6378137.0,         # [GRS80]長軸半径
            1 / 298.257222101, # [GRS80]扁平率
        ],
        ELLIPSOID_WGS84: [
            6378137.0,         # [WGS84]長軸半径
            1 / 298.257223563, # [WGS84]扁平率
        ],
    }

# 反復計算の上限回数
    ITERATION_LIMIT = 1000

    # 差異が無ければ0.0を返す
    if isclose(lat1, lat2) and isclose(lon1, lon2):
        return {
            'distance': 0.0,
            'azimuth1': 0.0,
            'azimuth2': 0.0,
        }

    # 計算時に必要な長軸半径(a)と扁平率(ƒ)を定数から取得し、短軸半径(b)を算出する
    # 楕円体が未指定の場合はGRS80の値を用いる
    a, ƒ = GEODETIC_DATUM.get(ellipsoid, GEODETIC_DATUM.get(ELLIPSOID_GRS80))
    b = (1 - ƒ) * a

    φ1 = radians(lat1)
    φ2 = radians(lat2)
    λ1 = radians(lon1)
    λ2 = radians(lon2)

    # 更成緯度(補助球上の緯度)
    U1 = atan((1 - ƒ) * tan(φ1))
    U2 = atan((1 - ƒ) * tan(φ2))

    sinU1 = sin(U1)
    sinU2 = sin(U2)
    cosU1 = cos(U1)
    cosU2 = cos(U2)

    # 2点間の経度差
    L = λ2 - λ1

    # λをLで初期化
    λ = L

    # 以下の計算をλが収束するまで反復する
    # 地点によっては収束しないことがあり得るため、反復回数に上限を設ける
    for i in range(ITERATION_LIMIT):
        sinλ = sin(λ)
        cosλ = cos(λ)
        sinσ = sqrt((cosU2 * sinλ) ** 2 + (cosU1 * sinU2 - sinU1 * cosU2 * cosλ) ** 2)
        cosσ = sinU1 * sinU2 + cosU1 * cosU2 * cosλ
        σ = atan2(sinσ, cosσ)
        sinα = cosU1 * cosU2 * sinλ / sinσ
        cos2α = 1 - sinα ** 2
        cos2σm = cosσ - 2 * sinU1 * sinU2 / cos2α
        C = ƒ / 16 * cos2α * (4 + ƒ * (4 - 3 * cos2α))
        λʹ = λ
        λ = L + (1 - C) * ƒ * sinα * (σ + C * sinσ * (cos2σm + C * cosσ * (-1 + 2 * cos2σm ** 2)))

        # 偏差が.000000000001以下ならbreak
        if abs(λ - λʹ) <= 1e-12:
            break
    else:
        # 計算が収束しなかった場合はNoneを返す
        return None

    # λが所望の精度まで収束したら以下の計算を行う
    u2 = cos2α * (a ** 2 - b ** 2) / (b ** 2)
    A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    Δσ = B * sinσ * (cos2σm + B / 4 * (cosσ * (-1 + 2 * cos2σm ** 2) - B / 6 * cos2σm * (-3 + 4 * sinσ ** 2) * (-3 + 4 * cos2σm ** 2)))

    # 2点間の楕円体上の距離
    s = b * A * (σ - Δσ)

    # 各点における方位角
    α1 = atan2(cosU2 * sinλ, cosU1 * sinU2 - sinU1 * cosU2 * cosλ)
    α2 = atan2(cosU1 * sinλ, -sinU1 * cosU2 + cosU1 * sinU2 * cosλ) + pi

    if α1 < 0:
        α1 = α1 + pi * 2

    return {
        'distance': s,           # 距離
        'azimuth1': degrees(α1), # 方位角(始点→終点)
        'azimuth2': degrees(α2), # 方位角(終点→始点)
    }


'''
MULTILINEからLINESTRINGに変換する関数
multiline : 変換対象のオブジェクト
df: 変換対象のオブジェクトを含むdataframe
crt : 変換対象のオブジェクトを含む行番号
'''
def ConvertMultiToLineString(multiline, df, crt):
    line_list = []
    list_x = []
    list_y = []
    for line in multiline:
        line_list.append(line)
        #lineの座標をリストに格納
        for count in range(line.GetPointCount()): 
            cood = line.GetPoint(count)
            list_x.append(cood[0])
            list_y.append(cood[1])
     #linestringに点を追加
    linestring = ogr.Geometry(ogr.wkbLineString)
    for x, y in zip(list_x, list_y):
        linestring.AddPoint(x, y)
    #元のdfにLINESTRINGを書き込む
    df.at[crt, "WKT"] = linestring


#セットバックしたラインを作成
'''
LINESTRINGを始点からを1.75m移動してかえす
line: 移動するLINESTRING
point: 始点を始点と終点を結んだ線の方位角に対して垂直な方向へ移動させた点 #[long, lat]
注意：始点の上下左右はラインによって変化する
'''
def setbackline(line, point, diff):
    line_long = []
    line_lat = []
    
    for count in range(line.GetPointCount()): 
        cood = line.GetPoint(count)
        line_long.append(cood[0])
        line_lat.append(cood[1])
    
    sb_x = np.array(line_long) + diff[0]
    sb_y = np.array(line_lat) + diff[1]
    
    line_sb = ogr.Geometry(ogr.wkbLineString)
    for x, y in zip(sb_x, sb_y):
        line_sb.AddPoint(x, y)
    
    return line_sb

'''
引数: LINESTRING(WGS84)
返り値: LINESTRING(ESPG6674)
'''
def LineConvert_lal_to_xy(line, n: int):
    transformer = Transformer.from_crs("epsg:4326", f"epsg:{n+6668}")
    pt_stock = []
    new = ogr.Geometry(ogr.wkbLineString)
    for count in range(line.GetPointCount()):
        pt = line.GetPoint(count)
        pt_stock.append((pt[1], pt[0])) #transformは緯度、経度の順番で渡す
    pt_stock.reverse() #AddPointは最後に加えた点が先頭になるためリストを逆にしないと点の順番が逆順になる
    for pt in transformer.itransform(pt_stock):
        new.AddPoint(pt[1], pt[0])
        
    return new


'''
引数: polygonのwkt(ESPG6674)のstring
返り値: POLYGON
''' 
def PolyConvert_xy_to_lal(wkt, n: int):
    transformer = Transformer.from_crs(f"epsg:{n+6668}", "epsg:4326")
    pt_stock = []
    new = ogr.Geometry(ogr.wkbLinearRing)
    pts = re.split('[()]', wkt)[2].split(',') #polyの座標リストを無理矢理Wktの文字列からつくる
    
    for pt in pts:
        pair = list(map(float, pt.split()))
        pt_stock.append((pair[1], pair[0])) #transformは緯度、経度の順番で渡す
    pt_stock.reverse()
    for pt in transformer.itransform(pt_stock):
        new.AddPoint(pt[1], pt[0])
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(new)
    return poly

    
'''
引数: polygon
返り値: polygonの座標を左回りに格納したリスト
'''
def PolygonToList(ring):
    wkt = ring.ExportToWkt()
    ring_cood = {'long':[],'lat':[]}
    #Polygonの座標をリストに
    for cood in wkt[10:-2].split(','): 
        pair = cood.split()
        ring_cood['long'].append(float(pair[0]))
        ring_cood['lat'].append(float(pair[1]))
        
    return ring_cood


'''
点ptsの参照座標系を変換する
pts(lat, long)
'''
def transcood(pts, n):
    transformer = Transformer.from_crs("epsg:4326", f"epsg:{n+6668}")
    pt_new = []
    for pt in transformer.itransform(pts):
        pt_new.append(pt)
    return pt_new


'''
点targetから線分に垂線を下すことができるかどうか調べる
線分の端点はpt1とpt2
'''
def isDrawvertline(pt1, pt2, target):
    l1 = geodesic(target, pt1).m
    l2 = geodesic(target, pt2).m
    if l1 > l2:
        #始点をpt1に
        temp = pt1
        pt1 = pt2
        pt2 = temp    
        
    c = np.array(target)
    a = np.array(pt1)
    b = np.array(pt2)
    x = c - a
    y = b - a
    dp = np.dot(x, y)
    x_norm = np.linalg.norm(x)
    y_norm = np.linalg.norm(y)
    cos = dp / (x_norm * y_norm  + 1e-10)
    return cos


'''
点targetからpt1とpt2を繋ぐ線分に下ろした垂線の長さを求める
'''
def calvertline(pt1, pt2, target):
    pt1 = transcood([pt1], 6)[0]
    pt2 = transcood([pt2], 6)[0]
    target = transcood([target], 6)[0]
    
    c = np.array(target)
    a = np.array(pt1)
    b = np.array(pt2)
    x = c - a
    y = b - a
    x_norm = np.linalg.norm(x)
    y_norm = np.linalg.norm(y)
    L = np.cross(x, y) / (y_norm) #外積から二つのベクトルのなす角のsinをもとめる
    if L < 0:
        L = -L
    
    return L
