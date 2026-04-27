from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import canopen.network


class SyncProducer:
    """Transmits a SYNC message periodically."""

    #: COB-ID of the SYNC message
    cob_id = 0x80

    def __init__(self, network: canopen.network.Network):
        self.network = network
        self.period: Optional[float] = None
        self._task: Optional[canopen.network.PeriodicMessageTask] = None

    def transmit(self, count: Optional[int] = None):
        """Send out a SYNC message once.

        :param count:
            Counter to add in message.
        :raises ValueError:
            If the counter value does not fit in one byte.
        """
        pass

    def start(self, period: Optional[float] = None):
        """Start periodic transmission of SYNC message in a background thread.

        :param period:
            Period of SYNC message in seconds.
        :raises RuntimeError:
            If a periodic transmission is already started.
        :raises ValueError:
            If no period is set via argument nor the instance attribute.
        """
        pass

    def stop(self):
        """Stop periodic transmission of SYNC message."""
        pass
