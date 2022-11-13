import sys
sys.path.append("/Users/hirototakaura/opt/anaconda3/lib/python3.8/site-packages")
from osgeo import gdal, ogr
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from PIL import Image


class pixToCS:
    def __init__(self, xp_max, yp_max, xcs_max, ycs_max, xcs_min, ycs_min):
        self.xmax = xp_max
        self.ymax = yp_max
        self.Xmax = xcs_max#座標は左上から時計回り
        self.Ymax = ycs_max
        self.Xmin = xcs_min
        self.Ymin = ycs_min
        
    def convert_pixToCS(self, x, y):
        xcs = self.Xmin + (x / self.xmax) * (self.Xmax - self.Xmin)
        ycs = self.Ymax - (y / self.ymax) * (self.Ymax - self.Ymin)
        
        return xcs, ycs
    def translate_cood(self, cood):
        x = cood[0]
        y = cood[1]
        xcs, ycs = self.convert_pixToCS(x, y)
        return [xcs, ycs]
        
        
def strToList(xy):
    if isinstance(xy, int):
        pass
    else:
        if '[' in xy:
            xy = xy[1:-1]
        xypair = xy.split(",")
        xypair = [float(i) for i in xypair]
    return xypair


#座標からLINESTRINGを作成。LINESTRINGオブジェクトを返す
def PointToLine(xypair):
    xlist = []
    ylist = []
    #各点をリストに
    for pair in xypair:
        xlist.append(pair[0])
        ylist.append(pair[1])
        
    xlist.append(xypair[0][0])
    ylist.append(xypair[0][1])
    #ラインを作成
    line = ogr.Geometry(ogr.wkbLineString)
    for x, y in zip(xlist, ylist):
        if (isinstance(x, float)) and (isinstance(y, float)):
            pass
        else:
            x = float(x)
            y = float(y)
            
        line.AddPoint(x, y)
        
    return line


def MakeBoxLayer(inputfile, imgpath, tifpath):
    #Giotiffから座標を読み取る
    ds = gdal.Open(tifpath)
    width = ds.RasterXSize
    height = ds.RasterYSize
    gt = ds.GetGeoTransform()
    minx = gt[0]
    miny = gt[3] + width*gt[4] + height*gt[5]
    maxx = gt[0] + width*gt[1] + height*gt[2]
    maxy = gt[3] 
    #入力した画像を読み込む
    img = Image.open(imgpath)
    xmax, ymax = img.size
    #bboxを読み込む
    if '.csv' in inputfile:
        df = pd.read_csv(inputfile)
    elif '.txt' in inputfile:
        df = pd.read_table(inputfile, sep=' ', header=None)
    df = df.dropna(how='all', axis=1)
    label = ['x1y1', 'x2y2', 'x3y3', 'x4y4', 'classname', 'score']
    df = df.set_axis(label, axis='columns')

    dsCS = df.copy()
    ptc = pixToCS(xmax, ymax, maxx, maxy, minx, miny)
    for cood in ["x1y1", "x2y2", "x3y3", "x4y4"]:
        dsCS[cood] = dsCS[cood].map(lambda x : strToList(x))
        dsCS[cood] = dsCS[cood].map(lambda x: ptc.translate_cood(x))

    #bboxをLINESTRINGで描画するcsvを作成する
    #行と列で二重ループを回して各行の点をつなげたラインストリングをリストに書き出す
    strings =[]
    for col in range(len(dsCS['x1y1'])):
        points = [] 
        for pair in ['x1y1', 'x2y2', 'x3y3', 'x4y4']:
            points.append(dsCS[pair][col])
        strings.append(PointToLine(points))


    #リストからヘッダーWKTのdataframeを作成してcsvに書き出す
    dsCS['WKT'] = strings

    return dsCS.copy()
            
            
if __name__ == "__main__":
    #検出されたbboxのテキストファイル
    inputfile = '../RodeOutline_HigasiOsaka/bbox/bbox-txt/rd1256/rd1256_20200528_txt/rd1256_20200528_2_1500_out.txt'
    #緯度経度座標に変換したcsvファイルの保存場所
    outputfile = '../RodeOutline_HigasiOsaka/bbox/bbox-csv/rd1256/rd1256_20200528/rd1256_20200528_2_1500out.csv'
    #検出に使用した画像(jpg)
    imgpath = '../RodeOutline_HigasiOsaka/GoogleMap/Rd1256/glmap20210528/rd1256_20200528_2_1500.jpg'
    #検出に使用した画像(tiff)
    tifpath = '../RodeOutline_HigasiOsaka/GoogleMap/Rd1256/glmap20210528/rd1256_20200528_2.tif'

    output = MakeBoxLayer(inputfile, imgpath, tifpath)
    output.to_csv(outputfile)