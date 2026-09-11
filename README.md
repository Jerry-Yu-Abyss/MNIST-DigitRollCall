# DigitRollCall

用 CNN 辨識點名系統畫面上的四位數簽到碼，自動完成簽到。

手機透過 Camo 當作視訊來源 → OBS 虛擬攝影機輸出 → OpenCV 取畫面 →
本地訓練的 CNN 逐字辨識 → 四位數字組成簽到碼 → 自動回填點名系統。

## 專案結構

```
MNIST-DigitRollCall/
├── 訓練.py              CNN 訓練腳本，產出 cnn_mnist_model.h5
├── camera_utils.py      攝影機選擇工具，優先挑 OBS 虛擬攝影機
├── RDR多數字.py          核心辨識模組，main() 回傳穩定的四位數碼
├── RDR單數字.py          單數字辨識，除錯／對照用
├── RDR介面.py            辨識端 GUI
├── 點名系統.py           點名端 GUI（模擬 TronClass），出題並等待簽到
├── fonts/               簽到密碼用的五種字體（SIL OFL 授權，隨專案附帶）
├── start_all.py         啟動器，檢查檔案齊全後開啟兩支 GUI
├── try-CNN.bat          Windows 一鍵啟動
├── environment.yml      conda 環境定義
├── requirements.txt     pip 相依清單
└── cnn_mnist_model.h5   訓練好的模型，已隨倉庫附上
```

兩支 GUI 是獨立行程，透過 `recognized_code.txt` 交握（點名端讀到即刪檔）。

### 簽到密碼字體

每次顯示簽到畫面會從五種字體隨機挑一種，讓辨識條件更接近真實情境：

| 字體 | 風格 | 辨識實測（字高 45／60 px） |
|---|---|---|
| Playfair Display | 高對比襯線 | 7/8、8/8 |
| Comfortaa | 圓潤幾何 | 8/8、8/8 |
| Anton | 極粗壓縮 | 8/8、7/8 |
| Lobster | 書法連筆 | 6/8、7/8 |
| Oswald | 窄長無襯線 | 7/8、7/8 |

字體以 `AddFontResourceEx` 的 `FR_PRIVATE` 模式**只註冊給該行程**，
不寫入系統字體目錄也不動登錄檔，關掉程式即失效，無需管理員權限。

## 在新電腦上啟動（完整步驟）

### 1. 取得程式碼

```bash
git clone https://github.com/Jerry-Yu-Abyss/MNIST-DigitRollCall.git
cd MNIST-DigitRollCall
```

### 2. 建立 Python 環境

需要 **Python 3.11**（TensorFlow 2.21 尚未支援更新的版本）。用 conda：

```bash
conda env create -f environment.yml
conda activate mnist-rdr
```

或用既有環境搭 pip：

```bash
pip install -r requirements.txt
```

驗證安裝：

```bash
python -c "import tensorflow, cv2, numpy; print(tensorflow.__version__, cv2.__version__, numpy.__version__)"
```

應印出 `2.21.0 5.0.0 2.4.6`。第一次 import TensorFlow 會有一串 oneDNN／CPU 指令集的訊息，那是正常的提示不是錯誤。

### 3. MNIST 資料集

**不需要手動下載，也不在本倉庫裡。** `訓練.py` 執行時 `keras.datasets.mnist.load_data()`
會自動抓取並快取到使用者家目錄：

| 系統 | 快取位置 |
|---|---|
| Windows | `%USERPROFILE%\.keras\datasets\mnist.npz` |
| macOS / Linux | `~/.keras/datasets/mnist.npz` |

檔案約 11 MB，內含 `x_train` (60000, 28, 28)、`y_train`、`x_test` (10000, 28, 28)、`y_test`，
全部是 uint8 灰階 0~255。之後每次執行都直接讀快取，不會重複下載。

想先下載好（例如之後要離線作業）：

```bash
python -c "import keras; keras.datasets.mnist.load_data(); print('MNIST 已快取')"
```

若要改變快取位置，設定 `KERAS_HOME` 環境變數即可。

### 4. 模型

`cnn_mnist_model.h5` 已隨倉庫附上，**clone 下來就能直接用**，不必重新訓練。

想自己訓練（CPU 約 8 分鐘，會覆蓋現有模型）：

```bash
python 訓練.py
```

訓練會在 `val_loss` 連續 5 個 epoch 沒有改善時提早停止，並還原到最佳那一輪的權重。

### 5. 設定手機鏡頭

1. 電腦與手機各安裝 [Camo](https://reincubate.com/camo/)，用線或 Wi-Fi 連上
2. 開啟 OBS，新增「視訊擷取裝置」來源，選擇 **Camo**
3. 在 OBS 右下角控制列按 **啟動虛擬攝影機**

第 3 步最常被忘記。沒按的話 OBS Virtual Camera 雖然列得出來，但**開不起來或只有全黑畫面**。

### 6. 確認鏡頭抓得到

```bash
python camera_utils.py
```

會列出所有影像裝置與索引，例如：

```
[0] USB2.0 HD UVC WebCam
[1] Camo
[2] OBS Virtual Camera  <-- 虛擬攝影機
```

程式預設自動挑名稱含 `OBS` 的裝置。若自動挑選抓錯鏡頭，用環境變數強制指定：

```bash
set RDR_CAMERA=2
```

### 7. 啟動

```bash
python start_all.py
```

Windows 也可直接雙擊 `try-CNN.bat`。接著：

1. 點名端按「隨機生成簽到密碼」→「顯示簽到畫面」
2. 手機對準該畫面，讓四位數字落在藍框內（框佔畫面 15% × 10%，數字約佔框寬的六到八成最佳）
3. 辨識端按「開啟鏡頭識別」，連續 15 張讀到同一組碼即自動回填

辨識期間介面會凍結，這是正常的；要中斷請按 OpenCV 視窗的 `q`。

### 排錯速查

| 症狀 | 檢查 |
|---|---|
| `RuntimeError: 無法開啟有畫面的攝影機` | OBS 是否按了「啟動虛擬攝影機」；錯誤訊息會列出每支鏡頭失敗的原因 |
| 畫面一直顯示 `Detected 0 digits, need 4` | 看 `ROI Threshold` 視窗，數字要是清楚白色、背景全黑；太亮就調高 `RDR_THRESH` |
| 數字框不到 | 手機距離不對，數字太小或太大都會被尺寸篩選擋掉 |
| 雙擊 `try-CNN.bat` 沒反應 | 改用 `python start_all.py` 執行，才看得到錯誤訊息 |

## 模型架構

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
