import time
import threading
from PyQt6.QtCore import QThread, pyqtSignal


class StabilityMonitor(QThread):
    stability_changed = pyqtSignal(bool, list)

    POLL_MS     = 100
    STABLE_HOLD = 0.2   # seconds all params must stay stable before releasing

    def __init__(self, watched_params: list):
        super().__init__()
        self._watched      = watched_params
        self._running      = True
        self._stable_event = threading.Event()
        self._last_state   = None
        self._stable_since = None

    def wait_until_stable(self, timeout: float = 60.0) -> bool:
        return self._stable_event.wait(timeout)

    def reset(self):
        self._stable_since = None
        self._stable_event.clear()

    def stop(self):
        self._running = False

    @staticmethod
    def _param_is_stable(param) -> bool:
        if getattr(param, 'ui_type', None) == 'stability_indicator':
            return bool(param.current_value)
        return bool(getattr(param, 'stable', False))

    def run(self):
        while self._running:
            unstable   = [p for p in self._watched if not self._param_is_stable(p)]
            all_stable = len(unstable) == 0

            if all_stable:
                if self._stable_since is None:
                    self._stable_since = time.monotonic()
                elif time.monotonic() - self._stable_since >= self.STABLE_HOLD:
                    self._stable_event.set()
            else:
                self._stable_since = None
                self._stable_event.clear()

            # Emit only on state flips to avoid flooding the UI
            if all_stable != self._last_state:
                self._last_state = all_stable
                self.stability_changed.emit(all_stable, [p.name for p in unstable])

            self.msleep(self.POLL_MS)

        self._stable_event.set()


