#<< 多數字辨識 >>
import os
import cv2
import numpy as np
import tensorflow as tf
from collections import deque 

import camera_utils

#:模型檔與程式同層，避免因工作目錄不同而找不到檔案
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_NAME = "cnn_mnist_model.h5"   #:訓練.py 產出的模型檔

#:手機隔空拍螢幕時，曝光與數字大小會和預設值差很多，這些都可用環境變數覆寫
THRESH_VALUE = int(os.environ.get("RDR_THRESH", 200))   #:二值化閾值，畫面越亮要調越高
ROI_W_RATIO = float(os.environ.get("RDR_ROI_W", 0.15))  #:辨識框佔畫面的比例
ROI_H_RATIO = float(os.environ.get("RDR_ROI_H", 0.10))

#:單一數字的尺寸上限直接貼齊辨識框：四碼要並排塞進框裡，所以單一數字最寬是框寬的 1/4、
#:最高就是整個框高。這樣換鏡頭或改 ROI 比例時不必重調像素值。
DIGITS_PER_CODE = int(os.environ.get("RDR_DIGITS", 4))
MIN_W_FRAC = float(os.environ.get("RDR_MIN_W_FRAC", 0.20))   #:下限相對於單格寬度
MIN_H_FRAC = float(os.environ.get("RDR_MIN_H_FRAC", 0.40))   #:下限相對於框高

#:下面四個若有設定，會蓋掉依辨識框自動推算的像素值(排錯時手動鎖定用)
MIN_W_ABS = os.environ.get("RDR_MIN_W")
MAX_W_ABS = os.environ.get("RDR_MAX_W")
MIN_H_ABS = os.environ.get("RDR_MIN_H")
MAX_H_ABS = os.environ.get("RDR_MAX_H")

#:寬高比範圍，下限不能訂太高，否則細長的「1」會被整個濾掉
MIN_RATIO = float(os.environ.get("RDR_MIN_RATIO", 0.25))
MAX_RATIO = float(os.environ.get("RDR_MAX_RATIO", 2.0))

#:雙端佇列，用來儲存多筆結果做穩定化。

#函數：初始化攝影機並檢查是否成功開啟
def setup_camera(camera_index=None):
    #:優先挑名稱含 OBS 的虛擬攝影機；RDR_CAMERA 可強制指定索引
    if camera_index is not None:
        os.environ["RDR_CAMERA"] = str(camera_index)
    return camera_utils.open_camera()

#函數：提取畫面中間的 ROI(指定辨識範圍避免CPU資源浪費，和提升精度)
def get_roi(frame, roi_width_ratio=None, roi_height_ratio=None):
    roi_width_ratio = ROI_W_RATIO if roi_width_ratio is None else roi_width_ratio
    roi_height_ratio = ROI_H_RATIO if roi_height_ratio is None else roi_height_ratio
    height, width = frame.shape[:2]
    roi_w, roi_h = int(width * roi_width_ratio), int(height * roi_height_ratio)
    roi_x = int(width * 0.5 - roi_w * 0.5)  # 水平置中
    roi_y = int(height * 0.5 - roi_h * 0.5)  # 垂直置中
    roi = frame[roi_y:roi_y + roi_h, roi_x:roi_x + roi_w]
    return roi, roi_x, roi_y, roi_w, roi_h

#函數：處理 ROI、灰度轉換、二值化(thresh)和輪廓檢測(contours)
def process_roi(roi, threshold_value=None): #:設定二值化閾值(減少雜訊)
    threshold_value = THRESH_VALUE if threshold_value is None else threshold_value
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) #:灰階處理
    _, thresh = cv2.threshold(gray_roi, threshold_value, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #:只檢測外部輪廓（不包含內部洞）\只保留輪廓的關鍵點，節省記憶體
    return thresh, contours

#函數：把輪廓裁切出來的數字轉成 MNIST 格式的 28x28
def to_mnist_28x28(digit):
    #:等比縮到最長邊 20 再置中補邊。直接 resize 成 (20,20) 會把細長的「1」壓成方形，
    #:模型看到的形狀和 MNIST 訓練資料對不上，會系統性誤判成 7 或 3。
    h, w = digit.shape
    if w >= h:
        new_w, new_h = 20, max(1, round(h * 20 / w))
    else:
        new_h, new_w = 20, max(1, round(w * 20 / h))
    resized = cv2.resize(digit, (new_w, new_h), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((28, 28), dtype=resized.dtype)
    y0, x0 = (28 - new_h) // 2, (28 - new_w) // 2
    canvas[y0:y0 + new_h, x0:x0 + new_w] = resized
    return canvas


#函數：依辨識框大小推算單一數字的合格尺寸範圍
def digit_size_limits(roi_w, roi_h):
    max_w = roi_w / DIGITS_PER_CODE   #:四碼並排，單一數字最寬就是框寬的 1/4
    max_h = float(roi_h)              #:最高就是整個框高，等於邊線可以緊貼辨識框
    min_w = max_w * MIN_W_FRAC
    min_h = max_h * MIN_H_FRAC
    if MIN_W_ABS is not None: min_w = float(MIN_W_ABS)
    if MAX_W_ABS is not None: max_w = float(MAX_W_ABS)
    if MIN_H_ABS is not None: min_h = float(MIN_H_ABS)
    if MAX_H_ABS is not None: max_h = float(MAX_H_ABS)
    return min_w, max_w, min_h, max_h


#函數：對輪廓進行數字預測並排序
def predict_digits(contours, thresh, roi_x, roi_y, model):
    digits = []
    roi_h, roi_w = thresh.shape[:2]   #:thresh 就是 ROI 大小，直接拿來推算尺寸範圍
    min_w, max_w, min_h, max_h = digit_size_limits(roi_w, roi_h)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if min_w < w <= max_w and min_h < h <= max_h and MIN_RATIO < w/h < MAX_RATIO:
            #:digit 是 區域內用來臨時儲存輸入數據的常規化設定變數丟入model 中預測後將結果存入digits中
            digit = to_mnist_28x28(thresh[y:y+h, x:x+w])
            digit = digit.reshape(1, 28, 28, 1) / 255.0  #:CNN 吃 (28,28,1)，不是攤平的 784
            prediction = model.predict(digit, verbose=0)
            predicted_digit = np.argmax(prediction)
            digits.append((x + roi_x, y + roi_y, w, h, predicted_digit))
    digits.sort(key=lambda x: x[0])  #:按 x 座標排序辨識的數字組
    return digits

#函數：顯示檢測結果並更新穩定代碼
def display_results(frame, digits, result_queue, roi_x, roi_y, roi_w, roi_h):

    cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (255, 0, 0), 2)
    
    #: 如果辨識出至少 4 個數字
    if len(digits) >= 4:
        recognized_numbers = [str(digit[4]) for digit in digits[:4]]
        final_code = ''.join(recognized_numbers)
        
        #: 將每個數字的區域畫出來，顯示預測結果
        for x, y, w, h, pred in digits[:4]:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f'{pred}', (x, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        cv2.putText(frame, f'Code: {final_code}', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        result_queue.append(final_code)
        if len(result_queue) == result_queue.maxlen:
            #: 從最近幾次結果中，找出出現次數最多的代碼(加入結果佇列)
            final_code_stable = max(set(result_queue), key=result_queue.count)
            cv2.putText(frame, f'Stable Code {final_code_stable}', (10, 60),cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            print(f"Detected 4-digit code: {final_code_stable}")
            return True, final_code_stable
    else:
        cv2.putText(frame, f'Detected {len(digits)} digits, need 4', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    return False, None

def main():
    #:載入訓練.py 產出的 CNN 模型（檔名須與訓練.py 的 save_path 一致）
    model = tf.keras.models.load_model(os.path.join(BASE_DIR, MODEL_NAME))
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.0005),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    # 初始化攝影機與結果佇列
    cap = setup_camera()
    result_queue = deque(maxlen=15)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("無法獲取影像")
                return None

            #: 提取 ROI
            roi, roi_x, roi_y, roi_w, roi_h = get_roi(frame)

            #: 轉成黑白、找輪廓
            thresh, contours = process_roi(roi)

            #: 將處理好的數據，送入模型預測
            digits = predict_digits(contours, thresh, roi_x, roi_y, model)

            #: 顯示結果
            #: display_results() return= True, final_code_stable
            should_stop, stable_code = display_results(frame, digits, result_queue, roi_x, roi_y, roi_w, roi_h)
            
            #: 顯示畫面
            cv2.imshow('Output', frame)
            cv2.imshow('ROI Threshold', thresh)

            # 檢查是否停止並返回穩定代碼
            if should_stop:
                return stable_code

            #: 退出鍵
            if cv2.waitKey(1) & 0xFF == ord('q'):
                return None
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    result = main()
    if result:
        print(f"Main returned 4-digit code: {result}")
    else:
        print("No 4-digit code detected")