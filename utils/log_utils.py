import logging
import logging.handlers
from datetime import date
from pathlib import Path


def setup_logger(log_dir: Path, name: str = 'main', max_logs: int = 10):
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{name}_{date.today().strftime('%Y%m%d')}.log"

    logs = sorted(log_dir.glob(f"{name}_*.log"))
    for old in logs[:-max_logs]:
        old.unlink()

    fmt = logging.Formatter('%(asctime)s | %(levelname)-7s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    memory_handler = logging.handlers.MemoryHandler(capacity=10000, flushLevel=logging.CRITICAL)
    memory_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(memory_handler)
    root.addHandler(console_handler)

    return logging.getLogger(name), log_file


def _flush_to_file(log_file: Path) -> None:
    root = logging.getLogger()
    memory_handler = next((h for h in root.handlers if isinstance(h, logging.handlers.MemoryHandler)), None)
    if memory_handler is None:
        return
    fmt = logging.Formatter('%(asctime)s | %(levelname)-7s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(fmt)
    memory_handler.setTarget(file_handler)
    memory_handler.flush()
    file_handler.close()
    memory_handler.setTarget(None)


def get_log_snippet(log_file: Path) -> str:
    if not log_file.exists():
        return '(log file not found)'
    lines = [l.rstrip() for l in log_file.read_text(encoding='utf-8').splitlines()
             if '| ERROR   |' in l or '| WARNING |' in l]
    return '<br>'.join(lines) if lines else '(no warning/error lines found)'


def notify_failure(notifier, subject: str, to: list, cc: list, log_file: Path):
    _flush_to_file(log_file)
    snippet = get_log_snippet(log_file)
    body = (
        '<BODY style="font-size:11pt;font-family:Calibri">'
        'An error occurred. Please see the log below.<br><br>'
        '<b>Log (WARNING / ERROR):</b><br>'
        f'<pre style="font-size:10pt;font-family:Consolas">{snippet}</pre>'
        '</BODY>'
    )
    notifier.send(subject=subject, body=body, to=to, cc=cc)
