import pyshark
import time
import os
from defines import *
from pandas import read_csv
from modelPrediction import Prediction
import asyncio  # 引入 asyncio


class Capture:
    def __init__(self, GUI, model_path, task_id, tshark_path='E:\\CTFTools\\WiresharkPortable64\\App\\Wireshark\\tshark.exe'):
        self.tshark_path = tshark_path
        self.GUI = GUI
        self.model_path = model_path
        self.task_id = task_id

    def capture_packet(self, output_file, interface, sniff_time):
        capture = pyshark.LiveCapture(
            output_file=output_file, interface=interface, tshark_path=self.tshark_path)
        capture.sniff(timeout=sniff_time)

    def start(self, interface, sniff_time):
        # 设置新的事件循环
        asyncio.set_event_loop(asyncio.new_event_loop())

        now_time = time.strftime(
            '%Y-%m-%d_%H-%M-%S', time.localtime(self.task_id))

        self.GUI.logSignal.emit(f'任务: {self.task_id}, 开始抓包, 时间{now_time}')
        shark_output_file = now_time + '_shark' + '.pcap'
        self.capture_packet(shark_output_file, interface, sniff_time)
        self.GUI.logSignal.emit(f'任务: {self.task_id}, 抓包结束, 时长为{sniff_time}秒')

        self.GUI.logSignal.emit(f'任务: {self.task_id}, 开始CIC转换')
        cic_output_file = now_time + '_cic' + '.csv'
        os.system("cicflowmeter -f " + shark_output_file +
                  " -c " + cic_output_file)

        self.GUI.logSignal.emit(f'任务: {self.task_id}, 开始格式化转换')
        format_output_file = now_time + '_format' + '.csv'
        df = read_csv(cic_output_file)
        df.rename(columns=column_mapping, inplace=True)
        df = df[target_columns]
        df.to_csv(format_output_file, index=False)

        self.GUI.logSignal.emit(f'任务: {self.task_id}, 开始模型预测')
        prediction_output_file = now_time + '_prediction' + '.csv'
        Prediction(format_output_file, self.model_path, prediction_output_file)

        self.GUI.logSignal.emit(f'任务: {self.task_id}, 整理预测结果')
        df = read_csv(prediction_output_file)
        predicted_labels = df['predicted_label'].tolist()
        good_result = True
        for i in range(len(predicted_labels)):
            if predicted_labels[i] != 'BENIGN':
                good_result = False
                self.GUI.logSignal.emit(
                    f'任务: {self.task_id}, 发现异常流量{predicted_labels[i]}')
                self.GUI.logSignal.emit(
                    f'任务: {self.task_id}, 异常数据: {df.iloc[i].to_dict()}')
        if good_result:
            self.GUI.logSignal.emit(f'任务: {self.task_id}, 一切正常！')

        os.remove(shark_output_file)
        os.remove(cic_output_file)
        os.remove(format_output_file)
        if good_result:
            os.remove(prediction_output_file)
            self.GUI.logSignal.emit(f'任务: {self.task_id}, 已删除全部中间文件')
        else:
            self.GUI.logSignal.emit(
                f'任务: {self.task_id}, 流量数据已保存至{prediction_output_file}')
