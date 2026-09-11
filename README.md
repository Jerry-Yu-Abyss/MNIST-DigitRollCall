# DigitRollCall

用 CNN 辨識點名系統畫面上的四位數簽到碼，自動完成簽到。

手機透過 Camo 當作視訊來源 → OBS 虛擬攝影機輸出 → OpenCV 取畫面 →
本地訓練的 CNN 逐字辨識 → 四位數字組成簽到碼 → 自動回填點名系統。

## 專案結構

```
digit-rollcall/
├── 訓練.py              CNN 訓練腳本，產出 cnn_mnist_model.h5
├── camera_utils.py      攝影機選擇工具，優先挑 OBS 虛擬攝影機
├── RDR多數字.py          核心辨識模組，main() 回傳穩定的四位數碼
├── RDR單數字.py          單數字辨識，除錯／對照用
├── RDR介面.py            辨識端 GUI
├── 點名系統.py           點名端 GUI（模擬 TronClass），出題並等待簽到
├── start_all.py         啟動器，檢查檔案齊全後開啟兩支 GUI
└── try-CNN.bat          Windows 一鍵啟動
```

兩支 GUI 是獨立行程，透過 `recognized_code.txt` 交握（點名端讀到即刪檔）。

## 環境

Conda，Python 3.11：

```bash
conda create -n mnist-rdr python=3.11
conda activate mnist-rdr
pip install tensorflow opencv-python numpy pillow pygrabber
```

`pygrabber` 用來列舉 DirectShow 裝置名稱，缺少時會退化成硬試索引 0~3。

## 使用

1. 手機連上 Camo，OBS 以 Camo 為來源並按下「啟動虛擬攝影機」
2. 執行 `try-CNN.bat`（或 `python start_all.py`）
3. 點名端按「隨機生成簽到密碼」→「顯示簽到畫面」
4. 手機對準畫面，讓四位數字落在藍框內
5. 辨識端按「開啟鏡頭識別」，連續 15 張讀到同一組碼即回填

模型未附帶時先執行 `python 訓練.py`（CPU 約 8 分鐘）。

## 模型

Conv32 → BN → MaxPool → Conv64 → BN → MaxPool → Flatten → Dropout(0.5) → Dense128 → Dense10

MNIST 訓練，`EarlyStopping` 在第 15 epoch 停止並還原第 10 epoch 權重，
**測試集準確度 99.35%**。

## 已知限制

- MNIST 是手寫數字，而簽到畫面是印刷字體 + 手機隔空拍攝，存在 domain shift，
  實際辨識率低於測試集數字。合成印刷體畫面實測四碼全對率 100%，但不含失焦與反光。
- 辨識迴圈跑在 GUI 主執行緒上，辨識期間介面會凍結，「停止識別」按鈕無法真正中斷
  （需按 OpenCV 視窗的 `q`）。

辨識不準時優先調整環境變數 `RDR_THRESH`（二值化閾值）與 `RDR_ROI_W`／`RDR_ROI_H`
（辨識框大小），完整參數表見 [CLAUDE.md](CLAUDE.md)。
