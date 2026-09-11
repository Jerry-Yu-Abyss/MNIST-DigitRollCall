#<< 單數字辨識 >>
import os
import cv2
import numpy as np
import tensorflow as tf
from collections import deque

import camera_utils
import RDR多數字 as RDR   #:共用 to_mnist_28x28 前處理

#:與 RDR多數字.py 共用同一個 CNN 模型
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_NAME = "cnn_mnist_model.h5"   #:訓練.py 產出的模型檔

model = tf.keras.models.load_model(os.path.join(BASE_DIR, MODEL_NAME))
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])  # 消除警告

result_queue = deque(maxlen=15)
# 使用 OBS 虛擬攝影機，調整索引 (例如 1，需測試)
cap = camera_utils.open_camera()

while True:
    ret, frame = cap.read()
    if not ret:
        print("無法獲取影像")
        break

    # ROI處理
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255,
                                 cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY_INV, 11, 2)

    # 輪廓檢測
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        cnt = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(cnt)
        
        if w > 15 and h > 15:
            digit = RDR.to_mnist_28x28(thresh[y:y+h, x:x+w])

            # 預測
            digit = digit.reshape(1, 28, 28, 1) / 255.0  #:CNN 吃 (28,28,1)，不是攤平的 784
            prediction = model.predict(digit, verbose=0)
            result_queue.append(np.argmax(prediction))
            
            # 顯示結果
            if len(result_queue) == result_queue.maxlen:
                final_num = max(set(result_queue), key=result_queue.count)
                cv2.putText(frame, f'Number: {final_num}', (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    cv2.imshow('Output', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()