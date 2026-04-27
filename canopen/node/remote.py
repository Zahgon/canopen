from __future__ import annotations

import logging
from typing import TextIO, Union

import canopen.network
from canopen.emcy import EmcyConsumer
from canopen.nmt import NmtMaster
from canopen.node.base import BaseNode
from canopen.objectdictionary import ODArray, ODRecord, ODVariable, ObjectDictionary
from canopen.pdo import PDO, RPDO, TPDO
from canopen.sdo import SdoAbortedError, SdoClient, SdoCommunicationError


logger = logging.getLogger(__name__)


class RemoteNode(BaseNode):
    """A CANopen remote node.

    :param node_id:
        Node ID (set to None or 0 if specified by object dictionary)
    :param object_dictionary:
        Object dictionary as either a path to a file, an ``ObjectDictionary``
        or a file like object.
    :param load_od:
        Enable the Object Dictionary to be sent through SDO's to the remote
        node at startup.
    """

    def __init__(
        self,
        node_id: int,
        object_dictionary: Union[ObjectDictionary, str, TextIO],
        load_od: bool = False,
    ):
        super(RemoteNode, self).__init__(node_id, object_dictionary)

        #: Enable WORKAROUND for reversed PDO mapping entries
        self.curtis_hack = False

        self.sdo_channels = []
        self.sdo = self.add_sdo(0x600 + self.id, 0x580 + self.id)
        self.tpdo = TPDO(self)
        self.rpdo = RPDO(self)
        self.pdo = PDO(self, self.rpdo, self.tpdo)
        self.nmt = NmtMaster(self.id)
        self.emcy = EmcyConsumer()

        if load_od:
            self.load_configuration()

    def associate_network(self, network: canopen.network.Network):
        pass

    def remove_network(self) -> None:
        pass

    def add_sdo(self, rx_cobid, tx_cobid):
        """Add an additional SDO channel.

        The SDO client will be added to :attr:`sdo_channels`.

        :param int rx_cobid:
            COB-ID that the server receives on
        :param int tx_cobid:
            COB-ID that the server responds with

        :return: The SDO client created
        :rtype: canopen.sdo.SdoClient
        """
        pass

    def store(self, subindex=1):
        """Store parameters in non-volatile memory.

        :param int subindex:
            1 = All parameters\n
            2 = Communication related parameters\n
            3 = Application related parameters\n
            4 - 127 = Manufacturer specific
        """
        pass

    def restore(self, subindex=1):
        """Restore default parameters.

        :param int subindex:
            1 = All parameters\n
            2 = Communication related parameters\n
            3 = Application related parameters\n
            4 - 127 = Manufacturer specific
        """
        pass

    def __load_configuration_helper(self, index, subindex, name, value):
        """Helper function to send SDOs to the remote node
        :param index: Object index
        :param subindex: Object sub-index (if it does not exist e should be None)
        :param name: Object name
        :param value: Value to set in the object
        """
        pass

    def load_configuration(self) -> None:
        """Load the configuration of the node from the Object Dictionary.

        Iterate through all objects in the Object Dictionary and download the
        values to the remote node via SDO.
        To avoid PDO mapping conflicts, PDO-related objects are handled through
        the methods :meth:`canopen.pdo.PdoBase.read` and
        :meth:`canopen.pdo.PdoBase.save`.

        """
        pass
