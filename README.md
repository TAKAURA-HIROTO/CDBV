# 物体検知を用いた航空写真からの車速と断面交通量の算出  
都市環境評価のための騒音計算は、車速と断面交通量などがわかれば簡易的に計算することができます。これを利用して、航空写真から効率的に交通情報を手に入れ、騒音を推計することが可能です。
車速や断面交通量を計算するには、対象区間の車両台数、車間距離、道路長などが必要です。ここでは航空写真の前処理から物体検知モデルを利用して、航空写真からそれらを計算するプログラムを載せています。
<br>

### 目次  
### 1. [理論](#anchor1)
### 2. [検出から車間距離計算までの流れ](#anchor2)
### 2. [画像の下処理](#anchor2)
### 3. [車両の検出](#anchor3)
### 4. [検出したBBOXのピクセルから緯度経度への座標変換](#anchor4)
### 5. [重なった or 小さいBBOXの除去](#anchor5)
### 6. [車線データの作成](#anchor6)
### 7. [車両のペアリング](#anchor7)
### 8. [道路長の計算](#anchor8)
### 9. [車速の計算において注意すべき点](#anchor9)
### 10. [実行環境](#anchor10)

<br>

<a id="anchor1"></a>
###  1. 理論  
***  
* 自動車工学によれば、車速は車間距離から計算することができます。 
* また、車速と区間内の台数、区間長がわかれば、断面交通量を計算することができます。
* 車速と断面交通量、車両の大きさがわかれば路面から発生する道路交通騒音が簡易的に計算できます。  
<br>
<img width="1020" alt="スクリーンショット 2022-11-18 18 13 52" src="https://user-images.githubusercontent.com/81552631/202665644-7726f878-b081-4a78-aee6-1a94c8cc7909.png">  
<img width="930" alt="スクリーンショット 2022-11-18 18 14 06" src="https://user-images.githubusercontent.com/81552631/202665664-ba56e6c3-ad3f-4869-aeee-440e76546ba5.png">
<br>

<a id="anchor2"></a>

###  2. 検出から車間距離計算までの流れ  
***  
* 画像から車両を検出して車間距離を求めるまでのおおまかな流れは以下の画像のようになっています。次の章からそれぞれの処理を説明していきます。
 
![step1](https://user-images.githubusercontent.com/81552631/202680925-d00c8642-a429-4d2e-b727-5f2722cd1cb0.jpg)  
![step2](https://user-images.githubusercontent.com/81552631/202681118-8ad49b66-1831-4eeb-9d8e-940ab139df6d.png)  
![step3](https://user-images.githubusercontent.com/81552631/202681156-2e49868a-3f02-4e90-80c9-3f420fb2b869.png)  
![step4](https://user-images.githubusercontent.com/81552631/202681172-92b51794-63f9-41f3-8aad-f4609b4e54ed.png)  
<br>

<a id="anchor2"></a>
### 3. 画像の下処理
* 検出に使用する画像は[Qgis](https://www.qgis.org/en/site/)でGoogle Mapを読み込み座標情報を格納したTiff形式で書き出します。
* 国土地理院が配布している[道路輪郭線のデータ](https://fgd.gsi.go.jp/download/menu.php)をポリゴンデータに加工し、Qgis上で読み込むことで、駐車場などの不要な検出を取り除くことができます。  
![道路輪郭線](https://user-images.githubusercontent.com/81552631/202690110-1abc59f6-3daa-4acb-a90c-de141e98396e.png)

<a id="anchor3"></a>
### 3. 車両の検出

<a id="anchor4"></a>
### 4. 検出したBBOXのピクセルから緯度経度への座標変換

<a id="anchor5"></a>
### 5. 重なった or 小さいBBOXの除去

<a id="anchor6"></a>
### 6. 車線データの作成

<a id="anchor7"></a>
### 7. 車両のペアリング

<a id="anchor8"></a>
### 8. 道路長の計算

<a id="anchor9"></a>
### 8. 車速の計算において注意すべき点

<a id="anchor10"></a>
### 9. 実行環境
