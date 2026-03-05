import os
import csv
import time
import datetime
import itertools
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker


class DataLogger:
    def __init__(self, directory: str = "data"):
        self.directory = directory
        self._ensure_directory()
        self.filename = self._generate_filename()
        self.headers: list[str] = []
        self._file = None
        self._writer = None

    def _ensure_directory(self):
        os.makedirs(self.directory, exist_ok=True)

    def _generate_filename(self) -> str:
        i = 1
        while True:
            path = os.path.join(self.directory, f"scan__{i:03d}.csv")
            if not os.path.exists(path):
                return path
            i += 1

    def init_log(self, headers: list[str], comments: str = ""):
        self.headers = headers
        self._file = open(self.filename, 'w', newline='')
        if comments:
            self._file.write(f"# {comments}\n")
        self._writer = csv.DictWriter(self._file, fieldnames=self.headers)
        self._writer.writeheader()
        self._file.flush()

    def log(self, data: dict):
        if self._writer is None:
            return
        self._writer.writerow(data)
        self._file.flush()

    def close(self):
        if self._file:
            self._file.close()
            self._file   = None
            self._writer = None

class ScanWorker(QThread):
    data_point_ready = pyqtSignal(dict)
    scan_finished    = pyqtSignal()
    progress_update  = pyqtSignal(int, int)   # current, total
    status_update    = pyqtSignal(str)

    def __init__(self, instruments, scan_config: dict):
        super().__init__()
        self.instruments = instruments
        self.config      = scan_config

        self._running = True
        self._mutex   = QMutex()
        self._paused  = False

        self.logger: DataLogger | None = None

    def stop(self):
        with QMutexLocker(self._mutex):
            self._running = False
            self._paused  = False

    def pause(self):
        with QMutexLocker(self._mutex):
            self._paused = True

    def resume(self):
        with QMutexLocker(self._mutex):
            self._paused = False

    @property
    def is_paused(self) -> bool:
        with QMutexLocker(self._mutex):
            return self._paused

    def _is_running(self) -> bool:
        with QMutexLocker(self._mutex):
            return self._running

    def _interruptible_sleep(self, seconds: float):
        """Sleep in 50 ms slices so abort/pause are responsive."""
        end = time.time() + seconds
        while time.time() < end:
            if not self._is_running():
                return
            self.msleep(50)

    def _wait_while_paused(self):
        while True:
            with QMutexLocker(self._mutex):
                if not self._paused or not self._running:
                    return
            self.msleep(100)

    def _wait_for_stability(self, param):
        self._interruptible_sleep(1.2)
        timeout   = 60.0
        start_t   = time.time()
        while time.time() - start_t < timeout:
            if not self._is_running():
                return
            if param.stable:
                return
            self.msleep(100)
        self.status_update.emit(f"Timeout waiting for stability: {param.name}")

    def _build_axis_values(self, axis: dict, repeats: int) -> list:
        start = float(axis['start'])
        stop  = float(axis['stop'])
        steps = int(axis['steps'])

        if steps <= 1:
            base = [start]
        else:
            step_size = (stop - start) / (steps - 1)
            base = [start + i * step_size for i in range(steps)]

        if repeats <= 1:
            return base

        full = list(base)
        forward = True
        for _ in range(repeats - 1):
            if forward:
                full.extend(base[-2::-1])   # reverse, skip last overlap point
                forward = False
            else:
                full.extend(base[1:])        # forward, skip first overlap point
                forward = True
        return full

    def _snapshot(self, setpoints: dict | None = None) -> dict:
        data = {'timestamp': datetime.datetime.now().isoformat()}
        for inst in self.instruments:
            for param in inst.get_all_params():
                key = f"{inst.name}_{param.name}"
                data[key] = param.current_value
                if setpoints and key in setpoints:
                    data[f"{key}_setpoint"] = setpoints[key]
        return data

    @staticmethod
    def _build_auto_comment(axes: list, delay: float,
                            repeats: int, total_points: int) -> str:
        lines = [
            f"scan_start   : {datetime.datetime.now().isoformat()}",
            f"total_points : {total_points}",
            f"delay_s      : {delay}",
            f"repeats      : {repeats}",
            f"n_axes       : {len(axes)}",
        ]
        for i, ax in enumerate(axes):
            name = getattr(ax['param'], 'name', str(ax['param']))
            lines += [
                f"axis{i}_param : {name}",
                f"axis{i}_start : {ax['start']}",
                f"axis{i}_stop  : {ax['stop']}",
                f"axis{i}_steps : {ax['steps']}",
            ]
        return "\n# ".join(lines)


    def run(self):
        try:
            axes = self.config['axes']
            delay = float(self.config['delay'])
            repeats = int(self.config['repeats'])
            user_comment = self.config.get('comments', '').strip()

            axis_ranges = [self._build_axis_values(ax, repeats) for ax in axes]
            scan_points = list(itertools.product(*axis_ranges))
            total_points = len(scan_points)

            self.status_update.emit(f"Starting scan — {total_points} points")

            setpoint_keys = {}
            for ax in axes:
                p = ax['param']
                for inst in self.instruments:
                    if p in inst.parameters.values():
                        setpoint_keys[f"{inst.name}_{p.name}"] = None
                        break

            dummy   = self._snapshot({k: 0.0 for k in setpoint_keys})
            headers = list(dummy.keys())

            auto_comment = self._build_auto_comment(axes, delay, repeats, total_points)
            full_comment = (f"{auto_comment}\nuser_comment : {user_comment}"
                            if user_comment else auto_comment)

            self.logger = DataLogger()
            self.logger.init_log(headers, full_comment)
            self.status_update.emit(f"Saving to {self.logger.filename}")

            for idx, point in enumerate(scan_points):
                if not self._is_running():
                    break

                self._wait_while_paused()
                if not self._is_running():
                    break

                current_setpoints = {}
                for i, val in enumerate(point):
                    param = axes[i]['param']
                    if param.set_cmd:
                        param.set_cmd(val)
                    for inst in self.instruments:
                        if param in inst.parameters.values():
                            current_setpoints[f"{inst.name}_{param.name}"] = val
                            break

                if delay > 0:
                    self._interruptible_sleep(delay)
                    if not self._is_running():
                        break

                for axis in axes:
                    if axis['param'].ui_type == 'wm_freq' or axis['param'].special_channel == 'stability':
                        self.status_update.emit(
                            f"Waiting for stability: {axis['param'].name}")
                        self._wait_for_stability(axis['param'])
                        if not self._is_running():
                            break

                if not self._is_running():
                    break

                row = self._snapshot(current_setpoints)
                self.logger.log(row)
                self.data_point_ready.emit(row)
                self.progress_update.emit(idx + 1, total_points)

            self.status_update.emit("Scan finished.")

        except Exception as e:
            self.status_update.emit(f"Error: {e}")
            print(f"[ScanWorker] Error: {e}")

        finally:
            if self.logger:
                self.logger.close()
            self.scan_finished.emit()