import logging
import struct
import threading
import time
from typing import Callable, Final, Optional, TYPE_CHECKING

import canopen.network

if TYPE_CHECKING:
    from canopen.network import PeriodicMessageTask


logger = logging.getLogger(__name__)

NMT_STATES: Final[dict[int, str]] = {
    0: 'INITIALISING',
    4: 'STOPPED',
    5: 'OPERATIONAL',
    80: 'SLEEP',
    96: 'STANDBY',
    127: 'PRE-OPERATIONAL'
}

NMT_COMMANDS: Final[dict[str, int]] = {
    'OPERATIONAL': 1,
    'STOPPED': 2,
    'SLEEP': 80,
    'STANDBY': 96,
    'PRE-OPERATIONAL': 128,
    'INITIALISING': 129,
    'RESET': 129,
    'RESET COMMUNICATION': 130
}

COMMAND_TO_STATE: Final[dict[int, int]] = {
    1: 5,
    2: 4,
    80: 80,
    96: 96,
    128: 127,
    129: 0,
    130: 0
}


class NmtBase:
    """
    Can set the state of the node it controls using NMT commands and monitor
    the current state using the heartbeat protocol.
    """

    def __init__(self, node_id: int):
        self.id = node_id
        self.network: canopen.network.Network = canopen.network._UNINITIALIZED_NETWORK
        self._state = 0

    def on_command(self, can_id, data, timestamp):
        pass

    def send_command(self, code: int):
        """Send an NMT command code to the node.

        :param code:
            NMT command code.
        """
        pass

    @property
    def state(self) -> str:
        """Attribute to get or set node's state as a string.

        Can be one of:

        - 'INITIALISING'
        - 'PRE-OPERATIONAL'
        - 'STOPPED'
        - 'OPERATIONAL'
        - 'SLEEP'
        - 'STANDBY'
        - 'RESET'
        - 'RESET COMMUNICATION'
        """
        pass

    @state.setter
    def state(self, new_state: str):
        pass


class NmtMaster(NmtBase):

    def __init__(self, node_id: int):
        super(NmtMaster, self).__init__(node_id)
        self._state_received = None
        self._node_guarding_producer: Optional[PeriodicMessageTask] = None
        #: Timestamp of last heartbeat message
        self.timestamp: Optional[float] = None
        self.state_update = threading.Condition()
        self._callbacks: list[Callable[[int], None]] = []

    def on_heartbeat(self, can_id, data, timestamp):
        pass

    def send_command(self, code: int):
        """Send an NMT command code to the node.

        :param code:
            NMT command code.
        """
        pass

    def wait_for_heartbeat(self, timeout: float = 10):
        """Wait until a heartbeat message is received."""
        pass

    def wait_for_bootup(self, timeout: float = 10) -> None:
        """Wait until a boot-up message is received."""
        pass

    def add_heartbeat_callback(self, callback: Callable[[int], None]):
        """Add function to be called on heartbeat reception.

        :param callback:
            Function that should accept an NMT state as only argument.
        """
        pass

    # Compatibility with previous typo
    add_hearbeat_callback = add_heartbeat_callback

    def start_node_guarding(self, period: float):
        """Starts the node guarding mechanism.

        :param period:
            Period (in seconds) at which the node guarding should be advertised to the slave node.
        """
        pass

    def stop_node_guarding(self):
        """Stops the node guarding mechanism."""
        pass


class NmtSlave(NmtBase):
    """
    Handles the NMT state and handles heartbeat NMT service.
    """

    def __init__(self, node_id: int, local_node):
        super(NmtSlave, self).__init__(node_id)
        self._send_task: Optional[PeriodicMessageTask] = None
        self._heartbeat_time_ms = 0
        self._local_node = local_node

    def on_command(self, can_id, data, timestamp):
        pass

    def send_command(self, code: int) -> None:
        """Send an NMT command code to the node.

        :param code:
            NMT command code.
        """
        pass

    def on_write(self, index, data, **kwargs):
        pass

    def start_heartbeat(self, heartbeat_time_ms: int):
        """Start the heartbeat service.

        :param heartbeat_time_ms
            The heartbeat time in ms. If the heartbeat time is 0
            the heartbeating will not start.
        """
        pass

    def stop_heartbeat(self):
        """Stop the heartbeat service."""
        pass

    def update_heartbeat(self):
        pass


class NmtError(Exception):
    """Some NMT operation failed."""
