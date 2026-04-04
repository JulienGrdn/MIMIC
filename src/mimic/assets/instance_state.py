from PyQt6.QtCore import QObject, pyqtSignal

STATE_MASTER  = "master"
STATE_SLAVE   = "slave"
STATE_PENDING = "pending"


class _InstanceState(QObject):
    # Emitted whenever the state changes
    changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._state = STATE_PENDING

    @property
    def state(self) -> str:
        return self._state

    @state.setter
    def state(self, value: str):
        if value != self._state:
            self._state = value
            self.changed.emit(value)

    def is_master(self) -> bool:
        return self._state == STATE_MASTER


InstanceState = _InstanceState()
