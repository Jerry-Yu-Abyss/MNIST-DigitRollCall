## 專案簡介
使用CNN本地訓練MNIST資料集，再將模型進行視覺辨識處裡後，接入OBS串接camo使用手機來辨識點名系統中的四位數字，完成簽到

## 資料結構

專案為單層平放，所有程式與模型檔同層。各程式一律用
`BASE_DIR = os.path.dirname(os.path.abspath(__file__))` 組路徑，不依賴工作目錄，
因此從 .bat、VS Code 或任意資料夾啟動都讀得到檔案。

```
MNIST數字辨視點名系統/
├── 訓練.py              CNN 訓練腳本，產出 cnn_mnist_model.h5
├── camera_utils.py      攝影機選擇工具，優先挑名稱含 OBS 的虛擬攝影機
├── RDR多數字.py          核心辨識模組：四位數字辨識，main() 回傳穩定碼
├── RDR單數字.py          單數字辨識，除錯／對照用，不在主流程上
├── RDR介面.py            辨識端 GUI，呼叫 RDR多數字.main()，寫出 recognized_code.txt
├── 點名系統.py           點名端 GUI（模擬 TronClass），出題並輪詢 recognized_code.txt
├── fonts/               簽到密碼字體(5 種 TTF + 各自的 OFL 授權檔)
├── start_all.py         啟動器，檢查檔案齊全後開啟上面兩支 GUI
├── try-CNN.bat          一鍵啟動，內容必須維持純 ASCII（原因見下）
└── .vscode/settings.json 指定 conda 直譯器
```

### 執行期產生的檔案（不隨專案附帶，需自行生成）
| 檔案 | 產生者 | 使用者 | 說明 |
|---|---|---|---|
| `cnn_mnist_model.h5` | `訓練.py` | `RDR多數字.py`、`RDR單數字.py` | 唯一的模型檔，三處共用同一檔名常數 `MODEL_NAME` |
| `recognized_code.txt` | `RDR介面.py` | `點名系統.py` | 兩支 GUI 間唯一的溝通媒介，點名端讀到後立即刪除 |

### 模組相依
```
訓練.py ──(cnn_mnist_model.h5)──┐
                                ▼
camera_utils.py ──────► RDR多數字.py ──► RDR介面.py ──(recognized_code.txt)──► 點名系統.py
                └─────► RDR單數字.py
```
`訓練.py`、`點名系統.py` 彼此獨立，不 import 任何自寫模組；
`RDR介面.py` 是唯一把辨識結果送出去的出口。

### 資料流（一次簽到）
1. `點名系統.py` 隨機產生 4 位數密碼 → 以隨機字體放大顯示在「簽到畫面」。
2. 手機經 Camo 當作攝影機 → OBS 取畫面 → 開啟「啟動虛擬攝影機」輸出。
3. `camera_utils.open_camera()` 掃描裝置清單，挑名稱含 `OBS` 的索引開啟（1280×720）。
4. `RDR多數字.py` 取畫面中央 ROI → 灰階 → 二值化 `THRESH_BINARY_INV` → `findContours`。
5. 依寬高與長寬比篩出數字輪廓 → `to_mnist_28x28()` 等比縮放置中 → `reshape(1,28,28,1)/255.0` 丟模型。
6. 輪廓依 x 座標排序取前 4 碼組成字串，存入 `deque(maxlen=15)`；
   佇列滿後取**眾數**當穩定碼並回傳，避免單張誤判。
7. `RDR介面.py` 顯示穩定碼 →「自動點名」→ 確認對話框 → 寫入 `recognized_code.txt`。
8. `點名系統.py` 的背景執行緒每 0.5 秒輪詢該檔，讀到就填入輸入框、送出、刪檔。

### 可調參數（環境變數覆寫，不必改程式碼）
| 變數 | 預設 | 位置 | 用途 |
|---|---|---|---|
| `RDR_CAMERA` | 無 | camera_utils | 強制指定攝影機索引，跳過自動判斷 |
| `RDR_CAMERA_NAME` | `OBS` | camera_utils | 改成要優先比對的裝置名稱（如 `Camo`） |
| `RDR_THRESH` | `200` | RDR多數字 | 二值化閾值，畫面越亮要調越高 |
| `RDR_ROI_W` / `RDR_ROI_H` | `0.15` / `0.10` | RDR多數字 | 中央辨識框佔畫面的比例（1280×720 下為 192×72） |
| `RDR_DIGITS` | `4` | RDR多數字 | 一組密碼幾位數，決定單一數字的寬度上限 |
| `RDR_MIN_W_FRAC` | `0.20` | RDR多數字 | 寬度下限，相對於單格寬度（框寬 ÷ 位數） |
| `RDR_MIN_H_FRAC` | `0.40` | RDR多數字 | 高度下限，相對於框高 |
| `RDR_MIN_W` / `RDR_MAX_W` | 自動推算 | RDR多數字 | 有設定才會蓋掉自動推算的像素值 |
| `RDR_MIN_H` / `RDR_MAX_H` | 自動推算 | RDR多數字 | 有設定才會蓋掉自動推算的像素值 |
| `RDR_MIN_RATIO` / `RDR_MAX_RATIO` | `0.25` / `2.0` | RDR多數字 | 輪廓寬高比範圍，下限訂太高會濾掉細長的「1」 |
| `RDR_MIN_STD` | `2.0` | camera_utils | 畫面對比低於此值視為無訊號，換下一支鏡頭 |
| `RDR_WARMUP` | `12` | camera_utils | 判定前先抓幾張影格等自動曝光穩定 |

## 實作需求

### 模型端（訓練.py）
- 輸入 `(28, 28, 1)`、像素除以 255 正規化、標籤 one-hot（`categorical_crossentropy`）。
- 架構：Conv32 → BN → MaxPool → Conv64 → BN → MaxPool → Flatten → Dropout(0.5) → Dense128 → Dense10。
- `EarlyStopping(patience=5, restore_best_weights)` ＋ `ReduceLROnPlateau`，上限 50 epochs。
- 存檔名稱必須與辨識端的 `MODEL_NAME` 一致（目前為 `cnn_mnist_model.h5`）。

### 辨識端（RDR多數字.py）
- 預處理必須與訓練一致，且**要等比縮放**：`to_mnist_28x28()` 把最長邊縮到 20 再置中補成 28×28。
  直接 `resize(20,20)` 會把寬高比 0.44 的「1」壓成方形，模型系統性誤判成 7 或 3
  （實測印刷體四碼正確率 76% → 100%）。
- 送模型的形狀是 `(1, 28, 28, 1)`，不是攤平的 784。
- 單一數字的尺寸上限由 `digit_size_limits()` 依辨識框推算，不寫死像素：
  四碼要並排塞進框裡，所以**最寬是框寬的 1/4、最高就是框高**，比較用 `<=`，
  讓剛好填滿的數字邊線可以緊貼藍框。改 ROI 比例或換鏡頭時不必重調像素值。
- 必須湊滿 4 個合格輪廓才組碼；不足時畫面提示 `Detected N digits, need 4`。
- 穩定碼採 15 張的眾數，回傳後 `main()` 即結束並釋放攝影機。

### 介面端
- `RDR介面.py` 與 `點名系統.py` 是兩個獨立的 tkinter 行程，**不共享記憶體**，
  只透過 `recognized_code.txt` 交握；新增功能時勿改動這個檔名與「讀完即刪」的約定。
- `RDR多數字.main()` 是阻塞式迴圈（跑在 GUI 主執行緒上），辨識期間介面會凍結；
  目前「停止識別」只重設狀態，無法真正中斷迴圈，需要中斷鍵時請按 OpenCV 視窗的 `q`。

### 已知的環境地雷
- **`try-CNN.bat` 不可含中文**。cmd 依「執行當下的主控台碼頁」解讀 .bat，雙擊開啟是 cp950、
  從終端機執行可能是 65001，中文檔名無論存成哪種編碼都會有一邊變亂碼、
  導致 `start` 靜默失敗。中文檔名一律放在 `start_all.py` 裡。
- **不要只用 `cv2.CAP_DSHOW`**。同一支鏡頭在不同後端差很多，實測 Camo 在 DSHOW 下是全黑、
  MSMF 下才有畫面，`camera_utils` 因此兩種後端都會試。
- **`cap.read()` 成功不等於有畫面**。沒開串流的虛擬攝影機照樣回傳全黑影格，
  必須再檢查對比度（`RDR_MIN_STD`），否則會選到一支看不見東西的鏡頭卻毫無錯誤訊息。
- **`pythonw.exe` 沒有主控台**，任何例外都是無聲關閉。排錯時改用 `python.exe` 直接跑。
- **tkinter 找不到字體時不會報錯**，只會默默改用預設字體。原本的字體清單有 7 種是
  macOS 專屬字體，在 Windows 上等於隨機字體功能失效卻毫無徵兆。新增字體後務必用
  `tkfont.families()` 確認家族名(是「Playfair Display」不是檔名「PlayfairDisplay」)。

### 環境前置
- OBS 須先按「啟動虛擬攝影機」，否則 `open_camera()` 會丟出 `RuntimeError` 並列出偵測到的裝置。
- 手機端 Camo 先連上，讓 OBS 抓得到畫面來源。
- 直接執行 `python camera_utils.py` 可列出所有攝影機索引與名稱，用來排查抓錯鏡頭。

## 開發環境
使用Conda env

- 環境名稱 `mnist-rdr`，Python 3.11
- 直譯器路徑：`%USERPROFILE%\anaconda3\envs\mnist-rdr\python.exe`（`.vscode/settings.json` 與 `try-CNN.bat` 都用環境變數組出來，不寫死使用者名稱）
- 套件：tensorflow 2.21 / keras 3.15 / opencv 5.0 / numpy 2.4 / pygrabber（列舉 DirectShow 裝置用，缺少時會退化成硬試索引 0~3）
- 啟動方式：`try-CNN.bat`（用 `pythonw.exe` 開，不留主控台視窗）
