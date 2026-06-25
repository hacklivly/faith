#Requires AutoHotkey v2.0
#SingleInstance Force
Persistent

; ═══════════════════════════════════════════════════════════════
; ISABELLA HOTKEYS — Full Laptop Automation Suite
; ═══════════════════════════════════════════════════════════════
; Features: Isabella comm, window management, clipboard history,
;           app launcher, DND mode, quick notes, media, snap zones,
;           auto-arrange, always-on-top toggle, quick search
; ═══════════════════════════════════════════════════════════════

PIPE_FILE := "C:\faith\data\ahk_pipe.txt"
NOTES_FILE := "C:\faith\data\quick_notes.txt"

; State
global dndMode := false
global clipHistory := []
global MAX_CLIP_HISTORY := 20

; Ensure data dir
if !DirExist("C:\faith\data")
    DirCreate("C:\faith\data")

; ═══════════════════════════════════════════════════════════════
; TRAY MENU
; ═══════════════════════════════════════════════════════════════
A_IconTip := "Isabella Hotkeys ♡"
tray := A_TrayMenu
tray.Delete()
tray.Add("📊 System Status", (*) => SendPipe("system_status"))
tray.Add("🧹 Cleanup", (*) => SendPipe("run_cleanup"))
tray.Add("⚡ Optimize", (*) => SendPipe("auto_optimize"))
tray.Add("📋 Clipboard History", (*) => ShowClipboard())
tray.Add("📝 Quick Notes", (*) => OpenNotes())
tray.Add()
tray.Add("🔕 Toggle DND", (*) => ToggleDND())
tray.Add("🔄 Reload Script", (*) => Reload())
tray.Add("❌ Quit", (*) => ExitApp())
tray.Default := "📊 System Status"

; Auto-start shortcut
startupLink := A_Startup "\Isabella Hotkeys.lnk"
if !FileExist(startupLink)
    FileCreateShortcut(A_ScriptFullPath, startupLink)

; ═══════════════════════════════════════════════════════════════
; CORE: PIPE COMMUNICATION
; ═══════════════════════════════════════════════════════════════
SendPipe(cmd) {
    try FileAppend(cmd "`n", PIPE_FILE)
    ShowToast("Isabella", cmd, 1200)
}

ShowToast(title, msg, duration := 1500) {
    ToolTip(title ": " msg)
    SetTimer(() => ToolTip(), -duration)
}

; ═══════════════════════════════════════════════════════════════
; ISABELLA COMMANDS (Ctrl+Alt combos)
; ═══════════════════════════════════════════════════════════════
^!i::SendPipe("toggle_listen")          ; Toggle Isabella listening
^!s::SendPipe("screenshot_analyze")     ; Screenshot + AI analyze
^!m::SendPipe("toggle_mic")             ; Toggle mic
^!q::SendPipe("system_status")          ; Quick status
^!c::SendPipe("run_cleanup")            ; Clean temp files
^!o::SendPipe("auto_optimize")          ; Kill heavy apps + optimize
^!p::SendPipe("top_processes")          ; What's eating resources

; Lock PC + tell Isabella
#+l:: {
    SendPipe("locking")
    Sleep(500)
    DllCall("LockWorkStation")
}

; Ask Isabella anything (opens input box)
^!a:: {
    ib := InputBox("Ask Isabella:", "Isabella", "w400 h100")
    if ib.Result = "OK" && ib.Value != ""
        SendPipe("ask:" ib.Value)
}

; ═══════════════════════════════════════════════════════════════
; WINDOW MANAGEMENT (Win+key combos)
; ═══════════════════════════════════════════════════════════════

; Always on top toggle
#^t:: {
    WinSetAlwaysOnTop(-1, "A")
    state := WinGetExStyle("A") & 0x8 ? "ON" : "OFF"
    ShowToast("Always On Top", state)
}

; Center window on screen
#c:: {
    try {
        WinGetPos(, , &w, &h, "A")
        mon := MonitorGetPrimary()
        MonitorGetWorkArea(mon, &ml, &mt, &mr, &mb)
        x := ml + ((mr - ml) - w) // 2
        y := mt + ((mb - mt) - h) // 2
        WinMove(x, y, , , "A")
        ShowToast("Window", "Centered")
    }
}

; Move window to next monitor
#+m:: {
    try {
        WinGetPos(&wx, &wy, &ww, &wh, "A")
        monCount := MonitorGetCount()
        if monCount > 1 {
            cur := MonitorGetPrimary()
            next := cur = monCount ? 1 : cur + 1
            MonitorGetWorkArea(next, &ml, &mt, &mr, &mb)
            WinMove(ml + 50, mt + 50, , , "A")
            ShowToast("Window", "Moved to monitor " next)
        }
    }
}

; Resize window to common sizes
#!1::WinMove(, , 1280, 720, "A")  ; 720p
#!2::WinMove(, , 1920, 1080, "A") ; 1080p
#!3:: {                            ; Half screen left
    mon := MonitorGetPrimary()
    MonitorGetWorkArea(mon, &ml, &mt, &mr, &mb)
    WinMove(ml, mt, (mr-ml)//2, mb-mt, "A")
}
#!4:: {                            ; Half screen right
    mon := MonitorGetPrimary()
    MonitorGetWorkArea(mon, &ml, &mt, &mr, &mb)
    WinMove(ml + (mr-ml)//2, mt, (mr-ml)//2, mb-mt, "A")
}

; Maximize/Restore toggle
#!f::WinGetMinMax("A") = 1 ? WinRestore("A") : WinMaximize("A")

; Minimize to tray (hide window)
#!h:: {
    WinMinimize("A")
    ShowToast("Window", "Minimized")
}

; Close active window
#!w::WinClose("A")

; Snap: arrange 2 windows side by side (last 2 active)
#!s:: {
    mon := MonitorGetPrimary()
    MonitorGetWorkArea(mon, &ml, &mt, &mr, &mb)
    halfW := (mr - ml) // 2
    fullH := mb - mt
    
    ; Get active window (left side)
    activeWin := WinGetID("A")
    WinMove(ml, mt, halfW, fullH, activeWin)
    
    ; Get previous window (right side)
    Send("!{Tab}")
    Sleep(200)
    prevWin := WinGetID("A")
    if prevWin != activeWin
        WinMove(ml + halfW, mt, halfW, fullH, prevWin)
    
    ShowToast("Snap", "2 windows side by side")
}

; ═══════════════════════════════════════════════════════════════
; CLIPBOARD HISTORY (auto-captures, Ctrl+Alt+V to browse)
; ═══════════════════════════════════════════════════════════════

; Monitor clipboard changes
OnClipboardChange(ClipChanged)
ClipChanged(dtype) {
    global clipHistory, MAX_CLIP_HISTORY
    if dtype = 1 && A_Clipboard != "" {
        ; Don't store duplicates
        if clipHistory.Length > 0 && clipHistory[1] = A_Clipboard
            return
        clipHistory.InsertAt(1, A_Clipboard)
        if clipHistory.Length > MAX_CLIP_HISTORY
            clipHistory.Pop()
    }
}

; Show clipboard history GUI
^!v::ShowClipboard()

ShowClipboard() {
    global clipHistory
    if clipHistory.Length = 0 {
        ShowToast("Clipboard", "History empty")
        return
    }
    
    menuItems := ""
    for i, item in clipHistory {
        preview := StrLen(item) > 60 ? SubStr(item, 1, 60) "..." : item
        preview := StrReplace(preview, "`n", " ↵ ")
        menuItems .= i ". " preview "`n"
        if i >= 10
            break
    }
    
    ib := InputBox("Pick # to paste:`n`n" menuItems, "Clipboard History", "w500 h400")
    if ib.Result = "OK" && ib.Value != "" {
        idx := Integer(ib.Value)
        if idx >= 1 && idx <= clipHistory.Length {
            A_Clipboard := clipHistory[idx]
            Send("^v")
            ShowToast("Clipboard", "Pasted item #" idx)
        }
    }
}

; ═══════════════════════════════════════════════════════════════
; QUICK NOTES (Ctrl+Alt+N — instant note capture)
; ═══════════════════════════════════════════════════════════════
^!n:: {
    ib := InputBox("Quick note (Isabella saves it):", "Isabella Notes", "w450 h100")
    if ib.Result = "OK" && ib.Value != "" {
        timestamp := FormatTime(, "yyyy-MM-dd HH:mm")
        FileAppend(timestamp " | " ib.Value "`n", NOTES_FILE)
        SendPipe("note_saved:" ib.Value)
        ShowToast("Note saved", ib.Value, 2000)
    }
}

; Open notes file
OpenNotes() {
    if FileExist(NOTES_FILE)
        Run("notepad.exe " NOTES_FILE)
    else
        ShowToast("Notes", "No notes yet")
}

; ═══════════════════════════════════════════════════════════════
; DO NOT DISTURB MODE (Win+Alt+D)
; ═══════════════════════════════════════════════════════════════
#!d::ToggleDND()

ToggleDND() {
    global dndMode
    dndMode := !dndMode
    if dndMode {
        SendPipe("dnd_on")
        ShowToast("DND", "ON — Isabella will stay quiet", 2000)
        ; Mute system notifications
        Run('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]0x00)"', , "Hide")
    } else {
        SendPipe("dnd_off")
        ShowToast("DND", "OFF — Isabella is back", 2000)
    }
}

; ═══════════════════════════════════════════════════════════════
; APP LAUNCHER (Win+Space — fuzzy app search)
; ═══════════════════════════════════════════════════════════════
#Space:: {
    ib := InputBox("Launch app/url:", "Quick Launch", "w350 h80")
    if ib.Result != "OK" || ib.Value = ""
        return
    
    query := ib.Value
    
    ; URL detection
    if InStr(query, ".") && !InStr(query, " ") {
        if !InStr(query, "://")
            query := "https://" query
        Run(query)
        ShowToast("Opened", query)
        return
    }
    
    ; App map
    apps := Map(
        "chrome", "chrome",
        "browser", "chrome",
        "notepad", "notepad",
        "code", "code",
        "vscode", "code",
        "terminal", "wt",
        "cmd", "cmd",
        "explorer", "explorer",
        "files", "explorer",
        "calc", "calc",
        "calculator", "calc",
        "paint", "mspaint",
        "spotify", "spotify",
        "discord", "discord",
        "telegram", "telegram",
        "task", "taskmgr",
        "settings", "ms-settings:",
        "control", "control",
    )
    
    lower := StrLower(query)
    for name, exe in apps {
        if InStr(lower, name) {
            Run(exe)
            ShowToast("Launched", name)
            return
        }
    }
    
    ; Fallback: try running as-is
    try {
        Run(query)
        ShowToast("Launched", query)
    } catch {
        ; Search it
        Run("https://www.google.com/search?q=" query)
        ShowToast("Searching", query)
    }
}

; ═══════════════════════════════════════════════════════════════
; MEDIA CONTROLS (Ctrl+Alt+arrows)
; ═══════════════════════════════════════════════════════════════
^!Up::Send("{Volume_Up 3}")
^!Down::Send("{Volume_Down 3}")
^!Left::Send("{Media_Prev}")
^!Right::Send("{Media_Next}")
^!Enter::Send("{Media_Play_Pause}")

; ═══════════════════════════════════════════════════════════════
; QUICK SEARCH (select text + Ctrl+Alt+G = Google it)
; ═══════════════════════════════════════════════════════════════
^!g:: {
    old := A_Clipboard
    A_Clipboard := ""
    Send("^c")
    ClipWait(1)
    if A_Clipboard != "" {
        Run("https://www.google.com/search?q=" A_Clipboard)
        ShowToast("Googling", A_Clipboard)
    }
    A_Clipboard := old
}

; Select + Ctrl+Alt+Y = YouTube search
^!y:: {
    old := A_Clipboard
    A_Clipboard := ""
    Send("^c")
    ClipWait(1)
    if A_Clipboard != "" {
        Run("https://www.youtube.com/results?search_query=" A_Clipboard)
        ShowToast("YouTube", A_Clipboard)
    }
    A_Clipboard := old
}

; ═══════════════════════════════════════════════════════════════
; TYPING SHORTCUTS (text expansion)
; ═══════════════════════════════════════════════════════════════
:*:@@me::harsha@example.com
:*:@@addr::Your address here
:*:@@ty::Thank you so much!
:*:@@brb::I'll be right back
:*:@@omw::On my way!

; Date/time stamps
:*:@@date:: {
    SendInput(FormatTime(, "yyyy-MM-dd"))
}
:*:@@time:: {
    SendInput(FormatTime(, "HH:mm"))
}
:*:@@now:: {
    SendInput(FormatTime(, "yyyy-MM-dd HH:mm"))
}

; ═══════════════════════════════════════════════════════════════
; SCREEN TOOLS
; ═══════════════════════════════════════════════════════════════

; Color picker (Ctrl+Alt+K) — shows hex of pixel under cursor
^!k:: {
    MouseGetPos(&mx, &my)
    color := PixelGetColor(mx, my)
    A_Clipboard := color
    ShowToast("Color", color " (copied)", 2000)
}

; Ruler — show cursor position
^!r:: {
    MouseGetPos(&mx, &my)
    ShowToast("Position", "X:" mx " Y:" my, 2000)
}

; ═══════════════════════════════════════════════════════════════
; POWER ACTIONS (Ctrl+Shift combos)
; ═══════════════════════════════════════════════════════════════

; Empty recycle bin
^+Del:: {
    try FileRecycleEmpty()
    ShowToast("Recycle Bin", "Emptied")
}

; Kill foreground app (force)
^+Escape:: {
    pid := WinGetPID("A")
    name := WinGetProcessName("A")
    ProcessClose(pid)
    ShowToast("Killed", name)
}

; ═══════════════════════════════════════════════════════════════
; OPACITY CONTROL (Win+scroll wheel on any window)
; ═══════════════════════════════════════════════════════════════
#WheelUp:: {
    try {
        current := WinGetTransparent("A")
        if current = ""
            current := 255
        new := Min(255, current + 15)
        WinSetTransparent(new, "A")
        ShowToast("Opacity", Round(new/255*100) "%")
    }
}

#WheelDown:: {
    try {
        current := WinGetTransparent("A")
        if current = ""
            current := 255
        new := Max(50, current - 15)
        WinSetTransparent(new, "A")
        ShowToast("Opacity", Round(new/255*100) "%")
    }
}

; Reset opacity
#!0::WinSetTransparent("Off", "A")
