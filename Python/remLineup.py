def remLineup(df, RdCL_df):
    rem = []
    for id1 in df.index.to_numpy():
        if id1 in rem:
            continue
        pt1 = (df['fr_lat'][id1], df['fr_long'][id1])
        pt2 = (df['rear_lat'][id1], df['rear_long'][id1])
        for id2 in df.index.to_numpy():
            if id1 in rem or id2 in rem:
                break
            for direct in ['fr', 'rear']:
                if id1 in rem or id2 in rem:
                    break
                target = (df[f'{direct}_lat'][id2], df[f'{direct}_long'][id2])
                l1 = geodesic(target, pt1).m
                l2 = geodesic(target, pt2).m
                if l1 > l2:
                    #始点をpt1に
                    temp = pt1
                    pt1 = pt2
                    pt2 = temp
                if isDrawvertline(pt1, pt2, target) > 0:#並んでいるかどうか
                    #車線から遠い方を削除
                    vertL = [] #重心から中心線までの距離の初期化
                    for id3 in [id1, id2]:
                        target2 = (df['c_lat'][id3], df['c_long'][id3])
                        for id4 in RdCL_df.index.to_numpy():
                            linept1 = (RdCL_df['start_lat'][id4], RdCL_df['start_long'][id4])
                            linept2 = (RdCL_df['end_lat'][id4], RdCL_df['end_long'][id4])
                            l3 = geodesic(target2, linept1).m
                            l4 = geodesic(target2, linept2).m
                            if l3 > l4:
                                #始点をlinept1に
                                temp = linept1
                                linept1 = linept2
                                linept2 = temp
                            if isDrawvertline(linept1, linept2, target2) > 0:
                                print(id4)
                                L = calvertline(linept1, linept2, target2)
                                vertL.append((id3, L))
                    print(vertL)
                    if vertL[0][1] >= vertL[1][1]:
                        df.drop(vertL[0][0], inplace=True)
                        rem.append(vertL[0][0])
                        print('drop {}'.format(vertL[0][0]))
                        break
                    else:
                        df.drop(vertL[1][0], inplace=True)
                        rem.append(vertL[1][0])
                        print('drop {}'.format(vertL[1][0]))