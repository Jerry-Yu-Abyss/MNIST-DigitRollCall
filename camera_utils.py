#<< 攝影機工具：挑選 OBS 虛擬攝影機 >>
import os
import cv2

#:同一支鏡頭在不同後端的行為會差很多(實測 Camo 在 DSHOW 下全黑、MSMF 下才有畫面)，兩種都試過再決定
BACKENDS = [cv2.CAP_MSMF, cv2.CAP_DSHOW] if os.name == "nt" else [cv2.CAP_ANY]
BACKEND_NAMES = {cv2.CAP_MSMF: "MSMF", cv2.CAP_DSHOW: "DSHOW", cv2.CAP_ANY: "ANY"}

#:無訊號的虛擬攝影機仍會吐出全黑影格，只檢查 read() 成功會選到看不見東西的鏡頭
MIN_STD = float(os.environ.get("RDR_MIN_STD", 2.0))
WARMUP_FRAMES = int(os.environ.get("RDR_WARMUP", 12))


#函數：列出系統上所有影像裝置 [(索引, 名稱), ...]
def list_devices():
    #:pygrabber 沒裝或非 Windows 時，回傳空清單讓後續流程用索引硬試
    try:
        from pygrabber.dshow_graph import FilterGraph
        return list(enumerate(FilterGraph().get_input_devices()))
    except Exception:
        return []


#函數：決定要嘗試開啟的攝影機索引順序
def _candidate_indices(prefer_name):
    #:RDR_CAMERA 可強制指定索引，跳過所有自動判斷
    if os.environ.get("RDR_CAMERA"):
        return [int(os.environ["RDR_CAMERA"])]

    devices = list_devices()
    if devices:
        #:名稱含關鍵字(預設 OBS)的排前面，其餘依序當備援
        key = (prefer_name or "").lower()
        matched = [i for i, n in devices if key and key in n.lower()]
        return matched + [i for i, _ in devices if i not in matched]

    #:列不到裝置時，硬試前四個索引
    return [0, 1, 2, 3]


#函數：抓幾張影格讓自動曝光穩定，回傳最後一張與它的對比度
def _grab(cap):
    frame = None
    for _ in range(WARMUP_FRAMES):
        ok, f = cap.read()
        if ok and f is not None:
            frame = f
    return frame, (float(frame.std()) if frame is not None else 0.0)


#函數：開啟攝影機並設定解析度，失敗則丟出帶診斷訊息的例外
def open_camera(prefer_name=None, width=1280, height=720):
    #:RDR_CAMERA_NAME 可改要優先比對的裝置名稱
    prefer_name = prefer_name or os.environ.get("RDR_CAMERA_NAME", "OBS")
    names = dict(list_devices())
    tried = []

    for idx in _candidate_indices(prefer_name):
        for backend in BACKENDS:
            label = f"[{idx}] {names.get(idx, '未知裝置')} / {BACKEND_NAMES.get(backend, backend)}"
            cap = cv2.VideoCapture(idx, backend)
            if not cap.isOpened():
                tried.append(f"{label}：開不起來")
                cap.release()
                continue

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            frame, std = _grab(cap)
            if frame is None:
                tried.append(f"{label}：讀不到影格")
            elif std < MIN_STD:
                #:全黑或純色，通常是虛擬攝影機沒開串流、或裝置被其他程式佔用
                tried.append(f"{label}：無訊號(對比 {std:.1f})")
            else:
                actual = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                          int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
                print(f"使用攝影機 {label}  解析度 {actual[0]}x{actual[1]}  對比 {std:.1f}")
                return cap
            cap.release()

    raise RuntimeError(
        "無法開啟有畫面的攝影機。嘗試過：\n  " + "\n  ".join(tried)
        + "\n請確認 OBS 已按下「啟動虛擬攝影機」、來源畫面不是黑的，"
          "或用環境變數 RDR_CAMERA 指定索引（RDR_MIN_STD 可放寬無訊號判定）。"
    )


if __name__ == "__main__":
    devices = list_devices()
    if not devices:
        print("偵測不到任何影像裝置")
    for i, n in devices:
        mark = "  <-- 虛擬攝影機" if "obs" in n.lower() else ""
        print(f"[{i}] {n}{mark}")
