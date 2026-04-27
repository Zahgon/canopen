from __future__ import annotations

import binascii
import contextlib
import logging
import math
import threading
from collections.abc import Iterator, Mapping
from typing import Callable, Optional, TYPE_CHECKING, Union

import canopen.network
from canopen import objectdictionary
from canopen import variable
from canopen.sdo import SdoAbortedError

if TYPE_CHECKING:
    from canopen import LocalNode, RemoteNode
    from canopen.pdo import RPDO, TPDO
    from canopen.sdo import SdoRecord


PDO_NOT_VALID = 1 << 31
RTR_NOT_ALLOWED = 1 << 30

logger = logging.getLogger(__name__)


class PdoBase(Mapping):
    """Represents the base implementation for the PDO object.

    :param object node:
        Parent object associated with this PDO instance
    """

    def __init__(self, node: Union[LocalNode, RemoteNode]):
        self.network: canopen.network.Network = canopen.network._UNINITIALIZED_NETWORK
        self.map: PdoMaps  # must initialize in derived classes
        self.node: Union[LocalNode, RemoteNode] = node

    def __iter__(self):
        return iter(self.map)

    def __getitem__(self, key: Union[int, str]):
        if isinstance(key, int):
            if key == 0:
                raise KeyError("PDO index zero requested for 1-based sequence")
            if (
                0 < key <= 512  # By PDO Index
                or 0x1400 <= key <= 0x1BFF  # By RPDO / TPDO mapping or communication record
            ):
                return self.map[key]
        for pdo_map in self.map.values():
            try:
                return pdo_map[key]
            except KeyError:
                # ignore if one specific PDO does not have the key and try the next one
                continue
        raise KeyError(f"PDO: {key} was not found in any map")

    def __len__(self):
        return len(self.map)

    def read(self, from_od=False):
        """Read PDO configuration from node using SDO."""
        pass

    def save(self):
        """Save PDO configuration to node using SDO."""
        pass

    def subscribe(self):
        """Register the node's PDOs for reception on the network.

        This normally happens when the PDO configuration is read from
        or saved to the node.  Use this method to avoid the SDO flood
        associated with read() or save(), if the local PDO setup is
        known to match what's stored on the node.
        """
        pass

    def export(self, filename):
        """Export current configuration to a database file.

        .. note::
           This API requires the ``db_export`` feature to be installed::

              python3 -m pip install 'canopen[db_export]'

        :param str filename:
            Filename to save to (e.g. DBC, DBF, ARXML, KCD etc)
        :raises NotImplementedError:
            When the ``canopen[db_export]`` feature is not installed.

        :return: The CanMatrix object created
        :rtype: canmatrix.canmatrix.CanMatrix
        """
        pass

    def stop(self):
        """Stop all running tasks."""
        pass


class PdoMaps(Mapping[int, 'PdoMap']):
    """A collection of transmit or receive maps."""

    def __init__(self, com_offset: int, map_offset: int, pdo_node: PdoBase, cob_base=None):
        """
        :param com_offset:
        :param map_offset:
        :param pdo_node:
        :param cob_base:
        """
        self.maps: dict[int, PdoMap] = {}
        self.com_offset = com_offset
        self.map_offset = map_offset
        if not com_offset and not map_offset:
            # Skip generating entries without parameter index offsets
            return
        for map_no in range(512):
            if com_offset + map_no in pdo_node.node.object_dictionary:
                new_map = PdoMap(
                    pdo_node,
                    pdo_node.node.sdo[com_offset + map_no],
                    pdo_node.node.sdo[map_offset + map_no])
                # Generate default COB-IDs for predefined connection set
                if cob_base is not None and map_no < 4:
                    new_map.predefined_cob_id = cob_base + map_no * 0x100 + pdo_node.node.id
                self.maps[map_no + 1] = new_map

    def __getitem__(self, key: int) -> PdoMap:
        try:
            return self.maps[key]
        except KeyError:
            if self.map_offset:
                with contextlib.suppress(KeyError):
                    return self.maps[key + 1 - self.map_offset]
            if self.com_offset:
                with contextlib.suppress(KeyError):
                    return self.maps[key + 1 - self.com_offset]
            raise

    def __iter__(self) -> Iterator[int]:
        return iter(self.maps)

    def __len__(self) -> int:
        return len(self.maps)


class PdoMap:
    """One message which can have up to 8 bytes of variables mapped."""

    def __init__(self, pdo_node, com_record, map_array):
        self.pdo_node: Union[TPDO, RPDO] = pdo_node
        self.com_record: SdoRecord = com_record
        self.map_array: SdoRecord = map_array
        #: If this map is valid
        self.enabled: bool = False
        #: COB-ID for this PDO
        self.cob_id: Optional[int] = None
        #: Default COB-ID if this PDO is part of the pre-defined connection set
        self.predefined_cob_id: Optional[int] = None
        #: Is the remote transmit request (RTR) allowed for this PDO
        self.rtr_allowed: bool = True
        #: Transmission type (0-255)
        self.trans_type: Optional[int] = None
        #: Inhibit Time (optional) (in 100us)
        self.inhibit_time: Optional[int] = None
        #: Event timer (optional) (in ms)
        self.event_timer: Optional[int] = None
        #: Ignores SYNC objects up to this SYNC counter value (optional)
        self.sync_start_value: Optional[int] = None
        #: List of variables mapped to this PDO
        self.map: list[PdoVariable] = []
        self.length: int = 0
        #: Current message data
        self.data = bytearray()
        #: Timestamp of last received message
        self.timestamp: Optional[float] = None
        #: Period of receive message transmission in seconds.
        #: Set explicitly or using the :meth:`start()` method.
        self.period: Optional[float] = None
        self.callbacks = []
        self.receive_condition = threading.Condition()
        self.is_received: bool = False
        self._task = None

    def __repr__(self) -> str:
        cob = f"0x{self.cob_id:X}" if self.cob_id else "Unassigned"
        return f"<{type(self).__qualname__} {self.name!r} at COB-ID {cob}>"

    def __getitem_by_index(self, value):
        pass

    def __getitem_by_name(self, value):
        pass

    def __getitem__(self, key: Union[int, str]) -> PdoVariable:
        if isinstance(key, int):
            # there is a maximum available of 8 slots per PDO map
            if key in range(0, 8):
                var = self.map[key]
            else:
                var = self.__getitem_by_index(key)
        else:
            try:
                var = self.__getitem_by_index(int(key, 16))
            except ValueError:
                var = self.__getitem_by_name(key)
        return var

    def __iter__(self) -> Iterator[PdoVariable]:
        return iter(self.map)

    def __len__(self) -> int:
        return len(self.map)

    def _get_variable(self, index, subindex):
        pass

    def _fill_map(self, needed):
        """Fill up mapping array to required length."""
        pass

    def _update_data_size(self):
        pass

    @property
    def name(self) -> str:
        """A descriptive name of the PDO.

        Examples:
         * TxPDO1_node4
         * RxPDO4_node1
         * Unknown
        """
        pass

    @property
    def is_periodic(self) -> bool:
        """Indicate whether PDO updates will be transferred regularly.

        If some external mechanism is used to transmit the PDO regularly, its cycle time
        should be written to the :attr:`period` member for this property to work.
        """
        pass

    def on_message(self, can_id, data, timestamp):
        pass

    def add_callback(self, callback: Callable[[PdoMap], None]) -> None:
        """Add a callback which will be called on receive.

        :param callback:
            The function to call which must take one argument of a
            :class:`~canopen.pdo.PdoMap`.
        """
        pass

    def read(self, from_od=False) -> None:
        """Read PDO configuration for this map.
        
        :param from_od:
            Read using SDO if False, read from object dictionary if True.
            When reading from object dictionary, if DCF populated a value, the
            DCF value will be used, otherwise the EDS default will be used instead.
        """
        pass

    def save(self) -> None:
        """Save PDO configuration for this map using SDO."""
        pass

    def subscribe(self) -> None:
        """Register the PDO for reception on the network.

        This normally happens when the PDO configuration is read from
        or saved to the node.  Use this method to avoid the SDO flood
        associated with read() or save(), if the local PDO setup is
        known to match what's stored on the node.
        """
        pass

    def clear(self) -> None:
        """Clear all variables from this map."""
        pass

    def add_variable(
        self,
        index: Union[str, int],
        subindex: Union[str, int] = 0,
        length: Optional[int] = None,
    ) -> PdoVariable:
        """Add a variable from object dictionary as the next entry.

        :param index: Index of variable as name or number
        :param subindex: Sub-index of variable as name or number
        :param length: Size of data in number of bits
        :return: PdoVariable that was added
        """
        pass

    def transmit(self) -> None:
        """Transmit the message once.

        :raises ValueError: When no COB-ID was assigned.
        """
        pass

    def start(self, period: Optional[float] = None) -> None:
        """Start periodic transmission of message in a background thread.

        :param period:
            Transmission period in seconds.  Can be omitted if :attr:`period` has been set
            on the object before.

        :raises ValueError:
            When neither the argument nor the :attr:`period` is given, or no COB-ID assigned.
        """
        pass

    def stop(self) -> None:
        """Stop transmission."""
        pass

    def update(self) -> None:
        """Update periodic message with new data."""
        pass

    def remote_request(self) -> None:
        """Send a remote request for the transmit PDO.
        Silently ignore if not allowed.
        """
        pass

    def wait_for_reception(self, timeout: float = 10) -> float:
        """Wait for the next transmit PDO.

        :param float timeout: Max time to wait in seconds.
        :return: Timestamp of message received or None if timeout.
        """
        pass


class PdoVariable(variable.Variable):
    """One object dictionary variable mapped to a PDO."""

    def __init__(self, od: objectdictionary.ODVariable):
        #: PDO object that is associated with this ODVariable Object
        self.pdo_parent: Optional[PdoMap] = None
        #: Location of variable in the message in bits
        self.offset = None
        self.length = len(od)
        variable.Variable.__init__(self, od)

    def get_data(self) -> bytes:
        """Reads the PDO variable from the last received message.

        :return: PdoVariable value as :class:`bytes`.
        """
        pass

    def set_data(self, data: bytes):
        """Set for the given variable the PDO data.

        :param data: Value for the PDO variable in the PDO message.
        """
        pass


# For compatibility
Variable = PdoVariable
Maps = PdoMaps
Map = PdoMap
