import logging

from canopen.sdo.base import SdoBase
from canopen.sdo.constants import *
from canopen.sdo.exceptions import *


logger = logging.getLogger(__name__)


class SdoServer(SdoBase):
    """Creates an SDO server."""

    def __init__(self, rx_cobid, tx_cobid, node):
        """
        :param int rx_cobid:
            COB-ID that the server receives on (usually 0x600 + node ID)
        :param int tx_cobid:
            COB-ID that the server responds with (usually 0x580 + node ID)
        :param canopen.LocalNode od:
            Node object owning the server
        """
        SdoBase.__init__(self, rx_cobid, tx_cobid, node.object_dictionary)
        self._node = node
        self._buffer = None
        self._toggle = 0
        self._index = None
        self._subindex = None
        self.last_received_error = 0x00000000

    def on_request(self, can_id, data, timestamp):
        pass

    def init_upload(self, request):
        pass

    def segmented_upload(self, command):
        pass

    def block_upload(self, data):
        # We currently don't support BLOCK UPLOAD
        # according to CIA301 the server is allowed
        # to switch to regular upload
        pass

    def request_aborted(self, data):
        pass

    def block_download(self, data):
        # We currently don't support BLOCK DOWNLOAD
        # Unpack the index and subindex in order to send appropriate abort
        pass

    def init_download(self, request):
        # TODO: Check if writable (now would fail on end of segmented downloads)
        pass

    def segmented_download(self, command, request):
        pass

    def send_response(self, response):
        self.network.send_message(self.tx_cobid, response)

    def abort(self, abort_code=ABORT_GENERAL_ERROR):
        """Abort current transfer."""
        data = struct.pack("<BHBL", RESPONSE_ABORTED,
                           self._index, self._subindex, abort_code)
        self.send_response(data)
        # logger.error("Transfer aborted with code 0x%08X", abort_code)

    def upload(self, index: int, subindex: int) -> bytes:
        """May be called to make a read operation without an Object Dictionary.

        :param index:
            Index of object to read.
        :param subindex:
            Sub-index of object to read.

        :return: A data object.

        :raises canopen.SdoAbortedError:
            When node responds with an error.
        """
        pass

    def download(
        self,
        index: int,
        subindex: int,
        data: bytes,
        force_segment: bool = False,
    ):
        """May be called to make a write operation without an Object Dictionary.

        :param index:
            Index of object to write.
        :param subindex:
            Sub-index of object to write.
        :param data:
            Data to be written.

        :raises canopen.SdoAbortedError:
            When node responds with an error.
        """
        pass
