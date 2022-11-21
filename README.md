# 深層学習による物体検知モデルを用いて航空写真から車速と断面交通量を推計する  
都市環境評価のための騒音計算は、車速と断面交通量などがわかれば簡易的に計算することができます。これを利用して、航空写真から効率的に交通情報を手に入れ、騒音を推計することが可能です。
車速や断面交通量を計算するには、対象区間の車両台数、車間距離、道路長などが必要です。つまり、 **車間距離、車両台数、車両の大きさ、道路長から道路の騒音を推定することができます。** ここでは航空写真の前処理から物体検知モデルを利用して、航空写真からそれらを計算するプログラムを載せています。
<br>

### 目次  
### 1. [理論](#anchor1)
### 2. [検出から車間距離計算までの流れ](#anchor2)
### 3. [画像の下処理](#anchor3)
### 4. [車両の検出に使用したモデル](#anchor4)
### 5. [検出したBBOXの座標をピクセルから緯度経度へ変換する](#anchor5)
### 6. [重なった or 小さいBBOXの除去](#anchor6)
### 7. [車線データの作成](#anchor7)
### 8. [車両のグループ分け](#anchor8)
### 9. [車両のペアリング](#anchor9)
### 10. [道路長の計算](#anchor10)
### 11. [車速の計算において注意すべき点](#anchor11)
### 12. [実行環境](#anchor12)

<br>

<a id="anchor1"></a>

###  1. 理論  
***  
* 自動車工学(江森一郎、自動車事故工学、技術書院、1993)によれば、車速は車間距離から計算することができます。 
* また、車速と区間内の台数、区間長がわかれば、断面交通量を計算することができます。
* 車速と断面交通量、車両の大きさがわかれば路面から発生する道路交通騒音がASJ RTN-Modelによって簡易的に計算できます(日本音響学会道路交通騒音調査研究委員会、道路交通騒音の予測モデルASJ RTN-Model 2018、日本音響学会誌、vol75(4)、2019)。  
<br>
<img width="1020" alt="スクリーンショット 2022-11-18 18 13 52" src="https://user-images.githubusercontent.com/81552631/202665644-7726f878-b081-4a78-aee6-1a94c8cc7909.png">  
<img width="930" alt="スクリーンショット 2022-11-18 18 14 06" src="https://user-images.githubusercontent.com/81552631/202665664-ba56e6c3-ad3f-4869-aeee-440e76546ba5.png">
<br>

<a id="anchor2"></a>

###  2. 検出から車間距離計算までの流れ  
***  
* 画像から車両を検出して車間距離を求めるまでのおおまかな流れは以下の画像のようになっています。次の章からそれぞれの処理を説明していきます。
 
![step1](https://user-images.githubusercontent.com/81552631/202680925-d00c8642-a429-4d2e-b727-5f2722cd1cb0.jpg)  
![step2](https://user-images.githubusercontent.com/81552631/202853420-53629a17-e5be-4eba-bd4d-ab0e407ba79e.png)  
![step3](https://user-images.githubusercontent.com/81552631/202681156-2e49868a-3f02-4e90-80c9-3f420fb2b869.png)  
![step4](https://user-images.githubusercontent.com/81552631/202681172-92b51794-63f9-41f3-8aad-f4609b4e54ed.png)  
<br>

<a id="anchor3"></a>
### 3. 画像の下処理
***
* 検出に使用する画像は[Qgis](https://www.qgis.org/en/site/)でGoogle Mapを読み込み座標情報を格納したTiff形式で書き出します。  
* 計算したい区間をいくつかの画像に分けて書き出し、それぞれで検出されたBBOXを緯度経度の座標に変換する(5章)ことでまとめるて扱うことができます。  
  <img width="771" alt="画像分割" src="https://user-images.githubusercontent.com/81552631/202855383-c56cde94-c54c-4867-a72f-2cac446a3340.png">  

* 国土地理院が配布している[道路輪郭線のデータ](https://fgd.gsi.go.jp/download/menu.php)をポリゴンデータに加工し、Qgis上で読み込むことで、駐車場などの不要な検出を取り除くことができます。    
![道路輪郭線](https://user-images.githubusercontent.com/81552631/202690110-1abc59f6-3daa-4acb-a90c-de141e98396e.png)
<br>

<a id="anchor4"></a>
### 4. 車両の検出に使用したモデル
***
* 車両の検出には、[ReDET](https://github.com/csuhan/ReDet)を採用し、航空写真から360度回転する物体を検出するタスク(Oriented Object Deteection)をこなします。
* 学習に使われている[DOTA](https://captain-whu.github.io/DOTA/dataset.html)では15種類の分類対象がラベル付されていて、今回は車両を検出したBBOXのみ出力させています。
<br>

<a id="anchor5"></a>  

### 5. 検出したBBOXの座標をピクセルから緯度経度へ変換する  
***  
* 目的
    * それぞれの画像で検出したBBOXは、画像上のピクセル座標で記録されています。これを緯度経度の座標に変換することで、すべてのBBOXの位置関係、距離、BBOXの大きさなどの計算が可能になります。
* 方法
    * Tiff画像の四隅の緯度経度座標を利用して、BBOXの四隅の座標を変換します。

<br>
<a id="anchor6"></a>

### 6. 重なった or 小さいBBOXの除去
***
* 目的
    * 出力されたBBOXには、同じ場所に2つ以上重なったものや、小さいものが含まれています。これを閾値を設定して取り除いていきます。
* 小さいBBOXの除去
    * 最小クラスの軽自動車(縦3.0m、幅1.4m)より小さいBBOXは取り除きます。
* 重なったBBOXの除去
    * 重なったBBOXに対して、(重なった面積/合計の面積)が50%を超えた場合、小さい方のBBOXを取り除きます。  
  
![BBOX除去](https://user-images.githubusercontent.com/81552631/202734109-2887f321-d6db-44e6-a1e4-97707b87046d.png)

<br>
<a id="anchor7"></a>

### 7. 車線データの作成
***
* 目的
    * 車間距離を測るにはまず車両の前後を、識別しなければいけません。また、現状検出モデルは車両の向きについて学習していません。加えて、それぞれの車両がどの車線を走行しているかをグループ分けする必要があります。そこで手作業で進行方向の情報を含んだ車線のデータを作成することで、これらの問題点を解決しました。
    * 車線データをグループ分けする(10章)ことで、対象区間の道路長を計算することもできます。
    * 一度、車線データを作成すると、異なる日付の画像に対しても、道路の場所は変わらないので、再利用することができます。
    
* 作成方法
    * 車線は緯度経度座標で表される点データの集まりとして表されます。
    * 進行方向に向かって始点から終点へと線を引くことで、車両の進む向きを決定します。  
    * 車線は各交差点で区切ります。
  
![車線](https://user-images.githubusercontent.com/81552631/202734859-5136ef21-cd2a-4c1d-a757-6eacaa44254c.png)  
![車間距離計算](https://user-images.githubusercontent.com/81552631/202756381-c2ef7ee9-eb28-45bc-8e8d-a800d7005a24.png)

<br>

<a id="anchor8"></a>

### 8. 車両のグループ分け
***
* 目的
    * 検出した車両に対しどの車線を走っているか振り分けます。  
    
* 方法
    * 作成した車線データを1mバッファさせその範囲にBBOXの中心が入ったものを、その車線を走る車両とします。
    * BBOXが並んでしまった場合、車線データから遠い方を取り除きます。(この処理は車線変更や路上駐車に有効です)  
  
![バッファ](https://user-images.githubusercontent.com/81552631/202741165-2d0b3d7e-d233-422f-a3db-71b4d85f5315.png)

<br>
<a id="anchor9"></a>

### 9. 車両のペアリング
***
* 目的
    * 車間距離を計算するために、前後の車両がどれか、ペアを探す必要があります。
    
* 方法
![ペアリング](https://user-images.githubusercontent.com/81552631/202740871-de891c86-39c2-44d7-9ef7-7674f867a180.png)
  
* また交差点内に車両が存在するかどうかで、端の車両の走行状況を決定します。 
* 交差点内に車両が存在する場合、端の車両とペアリングします。 
  
![交差点に存在](https://user-images.githubusercontent.com/81552631/202749030-846229ad-be72-43c5-8318-cd60be6c3378.png)  
* 交差点内に車両が存在せず、交差点から5m以内の場合、端の車両は停止(赤信号)しているとして、車速を0にします。 5m以上の場合は交差点までを車間距離に設定します。
    
![交差点に存在しない](https://user-images.githubusercontent.com/81552631/202749043-07349a7d-f21a-4c68-addf-3c9a910e1944.png)



<br>
<a id="anchor10"></a>

### 10. 道路長の計算
***
* 目的と方法
    * 対象区間の道路長を計算します。車線データは並列しているので、その中から一番長いもの以外を取り除き、残った車線を繋げることで区間長を計算します。
    * ある車線に注目し、それに並列する車線を探索します。長い方を親、短いものを子としてUnion Find木を構成します。最後にそれぞれのグループの親同士を繋げて長さを計算します。
    * 計算結果をpklに保存するので2度目以降の計算はすぐに終わります。
  
![道路長計算](https://user-images.githubusercontent.com/81552631/202748293-7c918254-7844-464f-97f6-c9452c396da4.png)

<br>
<a id="anchor11"></a>

### 11. 車速の計算において注意すべき点
***
* 車間距離から車速を計算する場合、２つ問題点が挙げられます。実際の交通調査をもとに、それぞれについて現状とっている対策を書いていきます。
    1. 信号で停止していると思われる車両でも車間距離は空いているので、速度を計算してしまう  
        -> 速度が15km/h以下の車両は速度0としています　。     
    2. 車間距離が大きく開いている車両の車速が極端に大きくなる  
        -> 法定速度へ調整しています。
  
![スクリーンショット 2022-11-19 2 03 25](https://user-images.githubusercontent.com/81552631/202760914-a54124ba-e658-4145-8977-30f17d7fc89d.png)
  
<br>
<a id="anchor12"></a>

### 12. 実行環境
***
* Python 3.7
* PyTorch 1.1
* Torchvision 0.30
* Ubuntu 18.04
* CUDA 10.0
* QGIS 3.20
* GDAL 3.0.12
* OGR 3.0.12
* OSR 3.0.12

<br>
