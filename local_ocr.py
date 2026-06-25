"""Isabella - Local OCR. Read screen text instantly using Tesseract (no API)."""
import subprocess

import pyautogui

_tesseract_available = None

def _check_tesseract():
    global _tesseract_available
    if _tesseract_available is None:
        try:
            subprocess.run(["tesseract", "--version"], capture_output=True, timeout=5)
            _tesseract_available = True
        except Exception:
            _tesseract_available = False
    return _tesseract_available

def read_screen() -> str:
    """OCR the entire screen. Returns text found."""
    if not _check_tesseract():
        return _fallback_ocr()
    try:
        import pytesseract
        img = pyautogui.screenshot()
        img = img.convert("L")  # grayscale for better OCR
        return pytesseract.image_to_string(img).strip()
    except Exception as e:
        return f"OCR failed: {e}"

def read_region(x: int, y: int, w: int, h: int) -> str:
    """OCR a specific region of the screen."""
    if not _check_tesseract():
        return _fallback_ocr(region=(x, y, w, h))
    try:
        import pytesseract
        img = pyautogui.screenshot(region=(x, y, w, h))
        img = img.convert("L")
        return pytesseract.image_to_string(img).strip()
    except Exception as e:
        return f"OCR failed: {e}"

def read_active_window() -> str:
    """OCR just the active window area."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        from ctypes import wintypes
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        x, y = rect.left, rect.top
        w, h = rect.right - rect.left, rect.bottom - rect.top
        if w > 0 and h > 0:
            return read_region(max(0, x), max(0, y), w, h)
    except Exception:
        pass
    return read_screen()

def _fallback_ocr(region=None) -> str:
    """Fallback: use Windows built-in OCR via PowerShell."""
    try:
        img = pyautogui.screenshot(region=region) if region else pyautogui.screenshot()
        import tempfile, os
        path = os.path.join(tempfile.gettempdir(), "faith_ocr.png")
        img.save(path)
        ps = f"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
$eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$file = [Windows.Storage.StorageFile]::GetFileFromPathAsync('{path}')
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{ $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'}})[0]
$fileTask = $asTask.MakeGenericMethod([Windows.Storage.StorageFile]).Invoke($null, @($file))
$fileTask.Wait()
$stream = $fileTask.Result.OpenAsync([Windows.Storage.FileAccessMode]::Read)
$streamTask = $asTask.MakeGenericMethod([Windows.Storage.Streams.IRandomAccessStream]).Invoke($null, @($stream))
$streamTask.Wait()
$decoder = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($streamTask.Result)
$decoderTask = $asTask.MakeGenericMethod([Windows.Graphics.Imaging.BitmapDecoder]).Invoke($null, @($decoder))
$decoderTask.Wait()
$bitmap = $decoderTask.Result.GetSoftwareBitmapAsync()
$bitmapTask = $asTask.MakeGenericMethod([Windows.Graphics.Imaging.SoftwareBitmap]).Invoke($null, @($bitmap))
$bitmapTask.Wait()
$ocrResult = $eng.RecognizeAsync($bitmapTask.Result)
$ocrTask = $asTask.MakeGenericMethod([Windows.Media.Ocr.OcrResult]).Invoke($null, @($ocrResult))
$ocrTask.Wait()
$ocrTask.Result.Text
"""
        result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True, timeout=15)
        os.remove(path)
        return result.stdout.strip() or "no text found"
    except Exception as e:
        return f"OCR fallback failed: {e}"
