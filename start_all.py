#<< 啟動器：同時開啟辨識介面與點名系統 >>
#:.bat 會依主控台碼頁去解讀檔案內容，中文檔名寫在 .bat 裡在不同情境下會變亂碼，
#:因此把檔名留在這支 Python（永遠以 UTF-8 讀原始碼），.bat 只保留純 ASCII。
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = ["RDR介面.py", "點名系統.py"]
MODEL = "cnn_mnist_model.h5"


def main():
    problems = []
    for name in SCRIPTS:
        if not os.path.exists(os.path.join(BASE_DIR, name)):
            problems.append(f"找不到 {name}（檔名是否被更動？）")
    if not os.path.exists(os.path.join(BASE_DIR, MODEL)):
        problems.append(f"找不到 {MODEL}，請先執行： python 訓練.py")

    if problems:
        print("[錯誤] 無法啟動：")
        for p in problems:
            print("  -", p)
        return 1

    #:用 pythonw 開圖形介面，不留主控台視窗
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    launcher = pythonw if os.path.exists(pythonw) else sys.executable

    for name in SCRIPTS:
        subprocess.Popen([launcher, os.path.join(BASE_DIR, name)], cwd=BASE_DIR)
        print(f"已啟動 {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
