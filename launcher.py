"""树庭之约 · 桌面启动器

打包成 exe 后双击运行：起一个本地服务，然后自动打开浏览器。
关闭这个窗口 = 退出程序。
"""
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

APP_NAME = "树庭之约 · Tree Court Promise"
DEFAULT_PORT = 8765


def resource_root() -> Path:
    """打包后资源在 _MEIPASS；开发时就是脚本所在目录。"""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


ROOT = resource_root()
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

PORT = int(os.environ.get("TREECOURT_PORT", DEFAULT_PORT))


def open_browser_later(url: str, delay: float = 2.5) -> None:
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def manual_hint_later(url: str, delay: float = 8.0) -> None:
    """有些电脑上浏览器带管理员权限，会自动打开失败但也不报错。
    等几秒后无条件提示一句，免得人对着黑窗口干瞪眼。"""
    time.sleep(delay)
    print()
    print("  [提示] 浏览器没自动打开的话，请手动访问：")
    print(f"         {url}")
    print()


def banner(url: str) -> None:
    line = "=" * 56
    print(line)
    print(f"  {APP_NAME}")
    print(line)
    print(f"  服务地址：{url}")
    print(f"  数据目录：{ROOT / 'data' / 'runtime'}")
    print("  浏览器会自动打开。关闭这个窗口即退出。")
    print(line)
    print()


def main() -> int:
    url = f"http://127.0.0.1:{PORT}"
    banner(url)

    # 先把浏览器叫起来，别等服务完全就绪
    threading.Thread(target=open_browser_later, args=(url,), daemon=True).start()
    threading.Thread(target=manual_hint_later, args=(url,), daemon=True).start()

    try:
        import uvicorn
        from web.backend.app import app
    except Exception as exc:  # 依赖缺失或资源不完整时给出人话
        print("[启动失败] 依赖或资源不完整：", exc)
        print("请确认这是完整的发行包，而不是只有 exe 一个文件。")
        input("按回车退出…")
        return 1

    try:
        uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
    except OSError as exc:
        print(f"[启动失败] 端口 {PORT} 可能被占用：{exc}")
        print(f"可以换端口重试：set TREECOURT_PORT=8766 然后再运行")
        input("按回车退出…")
        return 1
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
