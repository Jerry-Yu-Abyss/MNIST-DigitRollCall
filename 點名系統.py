import tkinter as tk
import random
import os
import time
from threading import Thread
import tkinter.font as tkfont

#:與辨識程式共用同一個暫存檔路徑
CODE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recognized_code.txt")

#函數：隨機產生簽到密碼
def generate_password():
    password = ''.join(random.choices('0123456789', k=4))
    label_password.config(text=password)

#函數：簽到畫面跳轉
def show_recognition_screen():
    ##:從函數：隨機產生簽到密碼 中拿變數(label_password)
    password = label_password.cget("text") or "0000"
    new_window = tk.Toplevel(root)
    new_window.title("簽到畫面")
    new_window.geometry("500x320")

    styles = ["Arial", "Times", "Courier", "Snell Roundhand", "Party LET", "Prociono", "Skia", "Tauri", "Trattatello"]
    ##styles = ["Arial", "Times", "Courier"]
    style = random.choice(styles)
    tk.Label(new_window, text=password, font=(style, 120, "bold")).pack(pady=50)

    entry_input = tk.Entry(new_window, font=("Arial", 14), width=4, justify="center")
    entry_input.pack(pady=1)

    #函數：認證簽到密碼
    def submit_password():
        ##:從函數：簽到畫面跳轉 中拿變數(entry_input)
        input_code = entry_input.get()
        if input_code == password:
            label_status.config(text="簽到成功", fg="green")
        else:
            label_status.config(text="密碼錯誤", fg="red")
        entry_input.config(state="disabled")
        new_window.after(1000, new_window.destroy)

    tk.Button(new_window, text="確認送出", command=submit_password).pack(pady=1)

    #將 entry 和 submit 函數綁定到窗口以便外部訪問
    new_window.entry_input = entry_input
    new_window.submit_password = submit_password

    #啟動外部輸入檢查函數(確認外掛程式是否輸入簽到密碼)
    check_external_input(new_window)

def check_external_input(window):
    def check_loop():
        while True:
            if not window.winfo_exists():
                break
            try:
                if os.path.exists(CODE_FILE):
                    with open(CODE_FILE, "r") as f:
                        code = f.read().strip()
                    if code and window.winfo_exists():
                        window.entry_input.delete(0, tk.END)
                        window.entry_input.insert(0, code)
                        window.submit_password()
                        os.remove(CODE_FILE)  #:刪除臨時檔案
                        break
            except Exception:
                pass
            time.sleep(0.5)  #:每0.5秒檢查一次
    Thread(target=check_loop, daemon=True).start()
def quit_button_action():
    root.destroy()  

#GUI 設置
root = tk.Tk()
root.title("創課點名系統")
root.geometry("600x400")

left_frame = tk.Frame(root, width=250, height=400, bg="#D3D3D3")
left_frame.pack(side=tk.LEFT, fill=tk.Y)
tk.Label(left_frame, text="<<創課點名系統>>", font=("Arial", 16, "bold"), bg="#D3D3D3").pack(pady=10)
tk.Button(left_frame, text="隨機生成簽到密碼", width=20, height=2, command=generate_password).pack(pady=5)
tk.Button(left_frame, text="顯示簽到畫面", width=20, height=2, command=show_recognition_screen).pack(pady=5)
tk.Label(left_frame, text="確認狀態：", font=("Arial", 14, "bold"), bg="#D3D3D3").pack(pady=10)
tk.Button(left_frame,text="退出系統",width=20, height=2,command=quit_button_action).pack(pady=5)


right_frame = tk.Frame(root, width=350, height=400, bg="#D3D3D3")
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
tk.Label(right_frame, text="(눈‸눈)", font=("Arial", 20, "bold"), bg="#D3D3D3").pack(pady=10)
label_password = tk.Label(right_frame, text="0000", font=("Arial", 20, "bold"), bg="#A9A9A9", width=4)
label_password.pack(pady=10)
tk.Label(right_frame, text="(ﾒﾟДﾟ)ﾒ", font=("Arial", 20, "bold"), bg="#D3D3D3").pack(pady=10)
label_status = tk.Label(right_frame, text="尚未簽到", font=("Arial", 20))
label_status.pack(pady=10)

root.mainloop()