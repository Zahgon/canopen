from __future__ import annotations

import logging
from typing import Union

import canopen.network
from canopen import objectdictionary
from canopen.emcy import EmcyProducer
from canopen.nmt import NmtSlave
from canopen.node.base import BaseNode
from canopen.objectdictionary import ObjectDictionary
from canopen.pdo import PDO, RPDO, TPDO
from canopen.sdo import SdoAbortedError, SdoServer


logger = logging.getLogger(__name__)


class LocalNode(BaseNode):

    def __init__(
        self,
        node_id: int,
        object_dictionary: Union[ObjectDictionary, str],
    ):
        super(LocalNode, self).__init__(node_id, object_dictionary)

        self.data_store: dict[int, dict[int, bytes]] = {}
        self._read_callbacks = []
        self._write_callbacks = []

        self.sdo = SdoServer(0x600 + self.id, 0x580 + self.id, self)
        self.tpdo = TPDO(self)
        self.rpdo = RPDO(self)
        self.pdo = PDO(self, self.rpdo, self.tpdo)
        self.nmt = NmtSlave(self.id, self)
        # Let self.nmt handle writes for 0x1017
        self.add_write_callback(self.nmt.on_write)
        self.emcy = EmcyProducer(0x80 + self.id)

    def associate_network(self, network: canopen.network.Network):
        pass

    def remove_network(self) -> None:
        pass

    def add_read_callback(self, callback):
        pass

    def add_write_callback(self, callback):
        pass

    def get_data(
        self, index: int, subindex: int, check_readable: bool = False
    ) -> bytes:
        pass

    def set_data(
        self,
        index: int,
        subindex: int,
        data: bytes,
        check_writable: bool = False,
    ) -> None:
        pass

    def _find_object(self, index, subindex):
        pass
