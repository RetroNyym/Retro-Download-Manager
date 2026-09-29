import hashlib
import os
import shutil
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from download_manager import DownloadManager
from download_manager.engine import COMPLETED, PAUSED

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

ROOT = tempfile.mkdtemp(prefix="pdm_ftp_")
SERVE_DIR = os.path.join(ROOT, "serve")
DATA_DIR = os.path.join(ROOT, "data")
DL_DIR = os.path.join(ROOT, "dl")
os.makedirs(SERVE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DL_DIR, exist_ok=True)

PAYLOAD = os.urandom(5 * 1024 * 1024)
with open(os.path.join(SERVE_DIR, "ftpfile.bin"), "wb") as f:
    f.write(PAYLOAD)
EXPECTED = hashlib.sha256(PAYLOAD).hexdigest()
RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append((name, bool(condition)))
    print(f"[{'OK  ' if condition else 'FAIL'}] {name} {detail}")


def wait_for(predicate, timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.15)
    return False


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    authorizer = DummyAuthorizer()
    authorizer.add_user("tester", "secret", SERVE_DIR, perm="elradfmw")
    authorizer.add_anonymous(SERVE_DIR, perm="elr")
    handler = FTPHandler
    handler.authorizer = authorizer
    server = FTPServer(("127.0.0.1", 0), handler)
    host, port = server.socket.getsockname()[:2]
    threading.Thread(target=server.serve_forever, kwargs={"timeout": 0.5},
                     daemon=True).start()
    base = f"ftp://tester:secret@{host}:{port}/ftpfile.bin"
    print("ftp sunucu:", f"ftp://{host}:{port}")

    mgr = DownloadManager(data_dir=DATA_DIR)
    mgr.apply_settings({"download_dir": DL_DIR, "segments": 5, "auto_start": True,
                        "queue_running": True, "max_concurrent": 2, "retries": 5,
                        "ftp_user": "tester", "ftp_password": "secret"})

    task = mgr.add([base])[0]
    ok = wait_for(lambda: task.state == COMPLETED)
    check("ftp cok parcali indirme", ok, task.state)
    check("ftp boyut", task.size == len(PAYLOAD), str(task.size))
    if task.final_path and task.final_path.exists():
        check("ftp sha256", sha256(str(task.final_path)) == EXPECTED)
        check("ftp part temiz", not os.path.exists(str(task.final_path) + ".part"))
    else:
        check("ftp dosya olustu", False)

    task2 = mgr.add([base], speed_limit=400)[0]
    wait_for(lambda: task2.downloaded > 300 * 1024, timeout=60)
    task2.pause()
    wait_for(lambda: not task2.is_busy, timeout=30)
    check("ftp duraklatma", task2.state == PAUSED, task2.state)
    held = task2.downloaded
    time.sleep(1)
    check("ftp duraklatildi sayaci sabit", task2.downloaded == held)
    task2.start()
    ok2 = wait_for(lambda: task2.state == COMPLETED)
    check("ftp devam ettirme", ok2, task2.state)
    if task2.final_path and task2.final_path.exists():
        check("ftp devam sha256", sha256(str(task2.final_path)) == EXPECTED)

    task3 = mgr.add([base], speed_limit=150)[0]
    wait_for(lambda: task3.downloaded > 200 * 1024, timeout=60)
    task3.cancel(delete_files=True)
    wait_for(lambda: not task3.is_busy, timeout=30)
    time.sleep(0.5)
    check("ftp iptal", task3.state == "canceled", task3.state)
    check("ftp part silindi",
          task3.part_path is None or not task3.part_path.exists())

    mgr.shutdown()
    server.close_all()
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} ftp test gecti")
    shutil.rmtree(ROOT, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
