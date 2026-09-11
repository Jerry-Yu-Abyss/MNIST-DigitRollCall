#<< 多數字辨識CNN介面 >>
import os
import tkinter as tk
from tkinter import messagebox

#:簽到碼暫存檔固定放程式同層，讓 點名系統.py 一定讀得到
CODE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recognized_code.txt")
import RDR多數字 as RDR


#: 全域狀態
recognized_code = None

#函數：開始辨識
def start_recognition():
    global recognized_code
    try:
        btn_start.config(state="disabled")  
        btn_stop.config(state="normal")     

        recognized_code = RDR.main() #:調用 RDR.main() 並更新辨識結果
        if recognized_code:
            label_result.config(text=recognized_code) #:顯示辨識碼
            btn_auto.config(state="normal") #:啟用「自動點名」按鈕
        else:
            label_result.config(text="未檢測到代碼")
            btn_auto.config(state="disabled")
    except Exception as e:
        messagebox.showerror("錯誤", f"辨識時發生錯誤：\n{e}")
        label_result.config(text="未檢測到代碼")
        btn_auto.config(state="disabled")
    finally:
        btn_start.config(state="normal")
        btn_stop.config(state="disabled")

#函數：停止辨識
def stop_recognition():
    #:模擬停止辨識(RDR多數字 無 stop_flag 僅重置狀態)
    global recognized_code
    recognized_code = None
    label_result.config(text="已停止")
    btn_auto.config(state="disabled")
    btn_start.config(state="normal")
    btn_stop.config(state="disabled")

#函數：提醒
def check_tronclass():
    #:提醒 TronClass 流程
    return messagebox.askyesno("確認", "請確認 TronClass 已開啟並生成簽到密碼，是否繼續？")

#函數：關閉窗口
def on_closing():
    root.destroy()

#函數：自動點名
def auto_attendance():
    if recognized_code and check_tronclass():
        #:將辨識到的代碼寫入臨時檔案
        with open(CODE_FILE, "w") as f:
            f.write(recognized_code)
        #:提醒 已提交密碼
        messagebox.showinfo("自動點名", f"已提交密碼: {recognized_code}")

def quit_button_action():
    root.destroy() 
    
#GUI 設置
root = tk.Tk()
root.title("數字點名辨識系統")
root.geometry("800x300")
root.protocol("WM_DELETE_WINDOW", on_closing)

#:標題
tk.Label(root, text="<<數字點名辨識系統>>", font=("Arial", 14, "bold")).pack(pady=10)

#:狀態顯示
tk.Label(root, text="識別結果:", font=("Arial", 12)).pack()
label_result = tk.Label(root, text="0000", font=("Arial", 20, "bold"), width=4, bg="#D3D3D3")
label_result.pack(pady=10)

#:按鈕設置
button_frame = tk.Frame(root)
button_frame.pack(pady=20)
btn_start = tk.Button(button_frame, text="開啟鏡頭識別", command=start_recognition, width=15)
btn_start.grid(row=0, column=0, padx=5)
btn_stop = tk.Button(button_frame, text="停止識別", command=stop_recognition, width=15, state="disabled")
btn_stop.grid(row=0, column=1, padx=5)
btn_auto = tk.Button(button_frame, text="自動點名", command=auto_attendance, width=15, state="disabled")
btn_auto.grid(row=0, column=2, padx=5)
btn_quit = tk.Button(button_frame, text="退出系統", command=quit_button_action, width=15)
btn_quit.grid(row=0, column=3, padx=5)

root.mainloop()