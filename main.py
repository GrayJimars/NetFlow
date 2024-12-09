from Ui_GUI import Ui_mainGUI
import sys
import asyncio
import qasync
from PyQt5.QtWidgets import *
from capturePacket import Capture
import psutil
import time
import cicflowmeter
from PyQt5.QtCore import pyqtSignal


class appMain(Ui_mainGUI, QMainWindow):
    logSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.appendLog('欢迎使用Netflow')
        self.appendLog('正在获取网络接口列表')
        self.getNetworkInterfaceList()
        self.appendLog('网络接口列表获取完成')
        self.browseTshark.clicked.connect(self.browseTsharkClicked)
        self.browseSave.clicked.connect(self.browseSaveClicked)
        self.browseModel.clicked.connect(self.browseModelClicked)
        self.controlButton.clicked.connect(self.controlButtonClicked)
        windump_path = './Windump/WinDump.exe'
        sys.path.append(windump_path)
        self.runningtask = []
        self.logSignal.connect(self.appendLog)

    def browseTsharkClicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None, "选择tshark路径", "", "Executable Files (*.exe)")
        if file_path:
            self.tsharkPath.setText(file_path)

    def browseSaveClicked(self):
        dir_path = QFileDialog.getExistingDirectory(None, "选择保存文件夹")
        if dir_path:
            self.savePath.setText(dir_path)

    def browseModelClicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None, "选择模型路径", "", "Joblib Files (*.joblib)")
        if file_path:
            self.modelPath.setText(file_path)

    def controlButtonClicked(self):
        if self.controlButton.text() == '开始监控':
            self.changeGUIonStart()
            asyncio.create_task(self.createCapture())
        elif self.controlButton.text() == '停止监控':
            asyncio.create_task(self.closeCapture())

    def changeGUIonStart(self):
        self.controlButton.setText('停止监控')
        self.browseTshark.setEnabled(False)
        self.browseSave.setEnabled(False)
        self.browseModel.setEnabled(False)
        self.timeInput.setEnabled(False)
        self.tsharkPath.setEnabled(False)
        self.savePath.setEnabled(False)
        self.modelPath.setEnabled(False)
        self.interfaceCombo.setEnabled(False)

    def changeGUIonStop(self):
        self.controlButton.setText('开始监控')
        self.browseTshark.setEnabled(True)
        self.browseSave.setEnabled(True)
        self.browseModel.setEnabled(True)
        self.timeInput.setEnabled(True)
        self.tsharkPath.setEnabled(True)
        self.savePath.setEnabled(True)
        self.modelPath.setEnabled(True)
        self.interfaceCombo.setEnabled(True)

    async def createCapture(self):
        self.logSignal.emit('实时网络监控已开始')
        while self.controlButton.text() == '停止监控':
            self.logSignal.emit('创建一个捕获任务')
            self.taskisrunning = True
            interface = self.interfaceCombo.currentText()
            time_duration = self.timeInput.value()
            tsharkPath = self.tsharkPath.text()
            model_path = self.modelPath.text()
            task_id = time.time()
            asyncio.create_task(self.runCapture(
                interface, time_duration, tsharkPath, model_path, task_id))
            self.runningtask.append(str(task_id))
            for i in range(time_duration):
                if self.controlButton.text() != '停止监控':
                    break
                self.setWindowTitle(f'距离下一个任务还有 {time_duration - i} 秒')
                await asyncio.sleep(1)

    async def runCapture(self, interface, time_duration, tsharkPath, model_path, task_id):
        try:
            cp = Capture(self, model_path, task_id, tsharkPath)
            await asyncio.get_event_loop().run_in_executor(None, cp.start, interface, time_duration)
        except Exception as e:
            self.logSignal.emit(f'任务 {task_id} 出错:\n{e}')
        finally:
            self.runningtask.remove(str(task_id))
            self.logSignal.emit(f'任务: {task_id}, 任务结束')

    async def closeCapture(self):
        self.controlButton.setEnabled(False)
        self.controlButton.setText('停止中')

        if self.runningtask:
            self.logSignal.emit('监控停止中，等待下列任务结束: ')
            self.logSignal.emit(','.join(self.runningtask))
            while self.runningtask:
                await asyncio.sleep(0.1)

        self.changeGUIonStop()
        self.logSignal.emit('实时网络监控已停止')
        self.controlButton.setEnabled(True)

    def getNetworkInterfaceList(self):
        interfaces = psutil.net_if_addrs()
        self.interfaceCombo.addItems(list(interfaces.keys()))

    def appendLog(self, message):
        self.textOutput.append(message)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainGUI = appMain()
    mainGUI.show()

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_forever()
