"""
server/app/api/utils_api.py
Routes for utils_bp
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "Core"))

from flask import jsonify, request, send_file
from app.api.Activitiy import utils_bp
import psutil, win32gui, win32process, win32con
from config_manager import PROCESS_NAME_MAP

@utils_bp.route("/process-map", methods=["GET"])
def process_map():
    return jsonify(PROCESS_NAME_MAP)

@utils_bp.route("/friendly-name/<exe>", methods=["GET"])
def friendly_name(exe: str):
    return jsonify({"exe": exe, "friendly": PROCESS_NAME_MAP.get(exe, exe)})

@utils_bp.route("/window-info", methods=["GET"])
def window_info():
    hwnd_str = request.args.get("hwnd")
    if not hwnd_str or not hwnd_str.isdigit():
        return ("?hwnd=<int> required", 400)
    hwnd = int(hwnd_str)
    info = {}
    try:
        info["class_name"] = win32gui.GetClassName(hwnd)
        info["parent_hwnd"] = win32gui.GetParent(hwnd)
        info["window_style"] = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        info["extended_style"] = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        info["is_tool_window"] = bool(info["extended_style"] & win32con.WS_EX_TOOLWINDOW)
        info["is_popup"] = bool(info["window_style"] & win32con.WS_POPUP)
        info["is_topmost"] = bool(info["extended_style"] & win32con.WS_EX_TOPMOST)
    except Exception as e:
        return (str(e), 500)
    return jsonify(info)

@utils_bp.route("/process/<int:pid>", methods=["GET"])
def process(pid: int):
    try:
        proc = psutil.Process(pid)
        return jsonify({
            "pid": proc.pid, "name": proc.name(), "exe": proc.exe(),
            "cmdline": proc.cmdline(), "create_time": proc.create_time(),
            "status": proc.status(), "friendly": PROCESS_NAME_MAP.get(proc.name(), proc.name())
        })
    except psutil.NoSuchProcess:
        return ("", 404)
    except psutil.AccessDenied:
        return ("", 403)

@utils_bp.route("/windows", methods=["GET"])
def enum_windows():
    windows = []
    def _enum(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                exe = psutil.Process(pid).name()
                windows.append({
                    "hwnd": hwnd, "title": win32gui.GetWindowText(hwnd),
                    "class_name": win32gui.GetClassName(hwnd),
                    "pid": pid, "exe": exe,
                    "friendly": PROCESS_NAME_MAP.get(exe, exe)
                })
            except Exception:
                pass
    win32gui.EnumWindows(_enum, None)
    return jsonify(windows)

@utils_bp.route("/system", methods=["GET"])
def system():
    import platform
    return jsonify({
        "platform": platform.platform(), "cpu_count": psutil.cpu_count(),
        "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "boot_time": psutil.boot_time()
    })