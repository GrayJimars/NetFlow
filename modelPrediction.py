import pandas as pd
import joblib
cleaned_col = ['Bwd PSH Flags', 'Bwd URG Flags', 'Fwd Avg Bytes/Bulk', 'Fwd Avg Packets/Bulk',
               'Fwd Avg Bulk Rate', 'Bwd Avg Bytes/Bulk', 'Bwd Avg Packets/Bulk', 'Bwd Avg Bulk Rate']

mapping = {
    0: "BENIGN",
    1: "Bot",
    2: "DDoS",
    3: "DoS GoldenEye",
    4: "DoS Hulk",
    5: "DoS Slowhttptest",
    6: "DoS Slowloris",
    7: "FTP-Patator",
    8: "Heartbleed",
    9: "Infiltration",
    10: "PortScan",
    11: "SSH-Patator",
    12: "Web Attack ⛏ Brute Force",
    13: "Web Attack ⛏ Sql Injection",
    14: "Web Attack ⛏ XSS"
}


def Prediction(data_path, model_path, pre_result_path):
    data_test = pd.read_csv(data_path)
    data_test = data_test.drop(columns=cleaned_col)
    data_test_pro = data_test.copy()
    data_test_pro.columns = ["processed_" +
                             col for col in data_test_pro.columns]

    X_test = data_test_pro
    # 加载模型
    model = joblib.load(model_path)
    # 预测
    y_pred = model.predict(X_test)
    # 保存预测结果
    y_pred_df = pd.DataFrame(y_pred, columns=['predicted_label'])
    data_test['predicted_label'] = y_pred_df['predicted_label']

    # 保存结果到 CSV 文件
    data_test['predicted_label'] = data_test['predicted_label'].replace(
        mapping)
    data_test.to_csv(pre_result_path, index=False)
