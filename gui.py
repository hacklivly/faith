"""
Faith - GUI.

Draggable, resizable, always-on-top window with:
- Video background (videoplayback.mp4) with audio toggle
- Text input for typing messages
- Mic toggle
- Drag anywhere, resize freely
"""
import os
import queue
import subprocess
import threading
import tkinter as tk

import cv2
from PIL import Image, ImageTk

import config

VOLUME_FILE = os.path.join(config.DATA_DIR, "music_volume.txt")

def set_music_volume(vol: int):
    global _music_on
    target_vol = vol if _music_on else 0
    try:
        os.makedirs(os.path.dirname(VOLUME_FILE), exist_ok=True)
        with open(VOLUME_FILE, "w", encoding="utf-8") as f:
            f.write(str(target_vol))
    except Exception:
        pass

_mic_on = True
_music_on = True
_status = "Listening..."
_root = None
_status_label = None
_mic_btn = None
_music_btn = None
_text_entry = None
_video_label = None
_text_queue = queue.Queue()

VIDEO_PATH = os.path.join(os.path.dirname(__file__), "vide2.webm")

# Drag state
_drag_x = 0
_drag_y = 0


def set_status(text: str):
    global _status
    _status = text
    
    # Duck music volume if status is active
    if text in ("Listening...", "Speaking...", "Thinking..."):
        set_music_volume(5)
    else:
        set_music_volume(30)

    if _status_label and _root:
        try:
            _root.after(0, lambda: _status_label.config(text=text))
        except (RuntimeError, tk.TclError):
            pass


def get_mic_status() -> bool:
    return _mic_on


def get_text_message() -> str | None:
    try:
        return _text_queue.get_nowait()
    except queue.Empty:
        return None


def _toggle_mic():
    global _mic_on
    _mic_on = not _mic_on
    if _mic_btn:
        if _mic_on:
            _mic_btn.config(text="🎙️ ON", bg="#4CAF50")
        else:
            _mic_btn.config(text="🎙️ OFF", bg="#f44336")
    set_status("Listening..." if _mic_on else "Idle")


def _toggle_music():
    global _music_on
    _music_on = not _music_on
    if _music_btn:
        if _music_on:
            _music_btn.config(text="🎵 ON", bg="#9C27B0")
            _start_audio()
        else:
            _music_btn.config(text="🎵 OFF", bg="#555")
            _stop_audio()


def _send_text(event=None):
    if not _text_entry:
        return
    text = _text_entry.get().strip()
    if text:
        _text_queue.put(text)
        _text_entry.delete(0, tk.END)


# --- Drag window ---
def _start_drag(event):
    global _drag_x, _drag_y
    _drag_x = event.x
    _drag_y = event.y


def _do_drag(event):
    x = _root.winfo_x() + event.x - _drag_x
    y = _root.winfo_y() + event.y - _drag_y
    _root.geometry(f"+{x}+{y}")


# --- Video ---
_video_cap = None
_video_running = False
_frame_ready = None
_frame_lock = threading.Lock()
_target_fps = 24  # smooth enough for background, easy on i3


def _start_video():
    global _video_cap, _video_running
    if not os.path.exists(VIDEO_PATH):
        return
    _video_cap = cv2.VideoCapture(VIDEO_PATH)
    # Let OpenCV use hardware-friendly settings
    _video_cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
    _video_running = True
    threading.Thread(target=_video_worker, daemon=True).start()
    _poll_frame()


def _video_worker():
    """Decode and resize frames in background thread."""
    global _frame_ready, _video_cap
    import time

    vid_fps = _video_cap.get(cv2.CAP_PROP_FPS) or 30
    # Skip ratio: if video is 30fps but we target 24, we show ~4 out of 5 frames
    skip = max(1, round(vid_fps / _target_fps))
    delay = 1.0 / _target_fps

    cached_w, cached_h = 0, 0
    frame_count = 0

    while _video_running and _video_cap:
        t0 = time.perf_counter()

        ret, frame = _video_cap.read()
        if not ret:
            _video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = _video_cap.read()
            if not ret:
                time.sleep(delay)
                continue

        # Skip frames to match target fps
        frame_count += 1
        if frame_count % skip != 0:
            continue

        try:
            w = _root.winfo_width()
            h = _root.winfo_height()
        except Exception:
            break
        if w < 10 or h < 10:
            time.sleep(delay)
            continue

        # Render at half resolution then let Tk stretch — massive speedup
        rw, rh = w // 2, h // 2
        if rw < 10 or rh < 10:
            rw, rh = w, h

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (rw, rh), interpolation=cv2.INTER_NEAREST)
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)

        with _frame_lock:
            _frame_ready = imgtk
            cached_w, cached_h = w, h

        elapsed = time.perf_counter() - t0
        sleep_time = delay - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)


def _poll_frame():
    """Pick up the latest decoded frame on the main thread (cheap)."""
    global _frame_ready
    if not _video_running:
        return

    with _frame_lock:
        imgtk = _frame_ready
        _frame_ready = None

    if imgtk and _video_label:
        _video_label.imgtk = imgtk
        _video_label.config(image=imgtk)

    _root.after(30, _poll_frame)  # poll at ~33fps — plenty smooth for display


# --- Audio ---
_audio_proc = None


def _start_audio():
    global _audio_proc
    _stop_audio()
    if not os.path.exists(VIDEO_PATH):
        return
    try:
        vbs_path = os.path.join(config.DATA_DIR, "_bg_music.vbs")
        os.makedirs(config.DATA_DIR, exist_ok=True)
        
        # Initialize volume file
        set_music_volume(30)
        
        vbs_video_path = VIDEO_PATH.replace('"', '""')
        vbs_vol_file = VOLUME_FILE.replace('"', '""')
        my_pid = os.getpid()
        
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(
                f'Set WMP = CreateObject("WMPlayer.OCX")\n'
                f'WMP.URL = "{vbs_video_path}"\n'
                f'WMP.settings.volume = 30\n'
                f'WMP.settings.setMode "loop", True\n'
                f'WMP.controls.play\n'
                f'Set fso = CreateObject("Scripting.FileSystemObject")\n'
                f'Set service = GetObject("winmgmts:")\n'
                f'Do While True\n'
                f'  WScript.Sleep 500\n'
                f'  \n'
                f'  \' Check if python parent process is still alive\n'
                f'  Set query = service.ExecQuery("Select * from Win32_Process Where ProcessID = {my_pid}")\n'
                f'  If query.Count = 0 Then\n'
                f'    Exit Do\n'
                f'  End If\n'
                f'  \n'
                f'  \' Read dynamic volume\n'
                f'  If fso.FileExists("{vbs_vol_file}") Then\n'
                f'    On Error Resume Next\n'
                f'    Set txtFile = fso.OpenTextFile("{vbs_vol_file}", 1)\n'
                f'    vol_str = txtFile.ReadLine\n'
                f'    txtFile.Close\n'
                f'    If IsNumeric(vol_str) Then\n'
                f'      WMP.settings.volume = CInt(vol_str)\n'
                f'    End If\n'
                f'    On Error GoTo 0\n'
                f'  End If\n'
                f'Loop\n'
            )
        _audio_proc = subprocess.Popen(
            ["wscript", vbs_path],
            creationflags=0x08000000,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"[Faith] Audio: {e}")


def _stop_audio():
    global _audio_proc
    if _audio_proc and _audio_proc.poll() is None:
        _audio_proc.terminate()
        _audio_proc = None


def _on_close():
    global _video_running
    _video_running = False
    _stop_audio()
    if _video_cap:
        _video_cap.release()
    _root.destroy()


def run_gui():
    global _root, _status_label, _mic_btn, _music_btn, _text_entry, _video_label

    _root = tk.Tk()
    _root.title("Faith ♡")
    _root.geometry("480x350+100+100")
    _root.minsize(300, 200)
    _root.overrideredirect(False)  # Native window borders for snap and edge resizing
    _root.attributes("-topmost", True)
    _root.configure(bg="#111")
    _root.protocol("WM_DELETE_WINDOW", _on_close)

    # Video background
    _video_label = tk.Label(_root, bg="#000")
    _video_label.place(x=0, y=0, relwidth=1, relheight=1)

    # Bottom controls
    bottom = tk.Frame(_root, bg="#111")
    bottom.pack(fill="x", side="bottom")

    # Status
    _status_label = tk.Label(bottom, text="Listening..." if _mic_on else "Idle", font=("Segoe UI", 9),
                             fg="#888", bg="#111")
    _status_label.pack(anchor="w", padx=10, pady=(4, 0))

    # Input row
    input_row = tk.Frame(bottom, bg="#111")
    input_row.pack(fill="x", padx=8, pady=6)

    _mic_btn = tk.Button(input_row, text="🎙️ ON" if _mic_on else "🎙️ OFF", font=("Segoe UI", 9, "bold"),
                         bg="#4CAF50" if _mic_on else "#f44336", fg="white", width=6,
                         relief=tk.FLAT, command=_toggle_mic)
    _mic_btn.pack(side="left", padx=(0, 4))

    _music_btn = tk.Button(input_row, text="🎵 ON", font=("Segoe UI", 9, "bold"),
                           bg="#9C27B0", fg="white", width=6,
                           relief=tk.FLAT, command=_toggle_music)
    _music_btn.pack(side="left", padx=(0, 6))

    _text_entry = tk.Entry(input_row, font=("Segoe UI", 10),
                           bg="#222", fg="white", insertbackground="white",
                           relief=tk.FLAT, bd=4)
    _text_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
    _text_entry.bind("<Return>", _send_text)

    send_btn = tk.Button(input_row, text="➤", font=("Segoe UI", 11, "bold"),
                         bg="#4CAF50", fg="white", width=3,
                         relief=tk.FLAT, command=_send_text)
    send_btn.pack(side="right")

    # Start video + audio
    _root.after(100, _start_video)
    if _music_on:
        _root.after(500, _start_audio)

    _root.mainloop()
