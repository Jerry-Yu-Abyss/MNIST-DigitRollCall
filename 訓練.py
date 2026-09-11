#<< CNN基礎訓練 >>
import os
import logging
import tensorflow as tf
import keras
from keras import layers

# 設定日誌
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

try:
    # 載入資料並預處理
    logger.info("載入 MNIST 資料集...")
    (x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()
    x_train = x_train.astype("float32") / 255.0
    x_test = x_test.astype("float32") / 255.0
    x_train = x_train[..., tf.newaxis]  # (28, 28, 1)
    x_test = x_test[..., tf.newaxis]
    
    num_classes = 10
    y_train = keras.utils.to_categorical(y_train, num_classes)
    y_test = keras.utils.to_categorical(y_test, num_classes)
    # 建立 CNN 模型
    model = keras.Sequential([
        keras.Input(shape=(28, 28, 1)),
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Flatten(),
        layers.Dropout(0.5),
        layers.Dense(128, activation='relu'),
        layers.Dense(num_classes, activation='softmax')
    ])
    model.summary()

    # 編譯模型
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    # 設定回調函式
    callbacks = [
        keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2)
    ]

    # 訓練模型
    logger.info("開始訓練模型...")
    history = model.fit(
        x_train, y_train,
        validation_split=0.1,
        epochs=50,
        batch_size=128,
        callbacks=callbacks,
        verbose=1
    )

    # 評估模型
    test_loss, test_acc = model.evaluate(x_test, y_test, verbose=0)
    logger.info(f'測試集準確度: {test_acc:.4f}, 測試集損失: {test_loss:.4f}')

    # 輸出訓練記錄
    for epoch in range(len(history.history['accuracy'])):
        logger.info(
            f"Epoch {epoch + 1}: "
            f"acc={history.history['accuracy'][epoch]:.4f}, "
            f"val_acc={history.history['val_accuracy'][epoch]:.4f}, "
            f"loss={history.history['loss'][epoch]:.4f}, "
            f"val_loss={history.history['val_loss'][epoch]:.4f}"
        )

    # 儲存模型（儲存在與程式同層資料夾）
    save_path = os.path.join(os.path.dirname(__file__), "cnn_mnist_model.h5")
    model.save(save_path)
    logger.info(f"模型已儲存到 {save_path}")

except Exception as e:
    logger.error(f"程式執行失敗: {str(e)}")
    raise