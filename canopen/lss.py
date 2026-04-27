import logging
import queue
import struct
import time

import canopen.network


logger = logging.getLogger(__name__)

# Command Specifier (CS)
CS_SWITCH_STATE_GLOBAL = 0x04
CS_CONFIGURE_NODE_ID = 0x11
CS_CONFIGURE_BIT_TIMING = 0x13
CS_ACTIVATE_BIT_TIMING = 0x15
CS_STORE_CONFIGURATION = 0x17
CS_SWITCH_STATE_SELECTIVE_VENDOR_ID = 0x40
CS_SWITCH_STATE_SELECTIVE_PRODUCT_CODE = 0x41
CS_SWITCH_STATE_SELECTIVE_REVISION_NUMBER = 0x42
CS_SWITCH_STATE_SELECTIVE_SERIAL_NUMBER = 0x43
CS_SWITCH_STATE_SELECTIVE_RESPONSE = 0x44
CS_IDENTIFY_REMOTE_SLAVE_VENDOR_ID = 0x46               # m -> s
CS_IDENTIFY_REMOTE_SLAVE_PRODUCT_CODE = 0x47            # m -> s
CS_IDENTIFY_REMOTE_SLAVE_REVISION_NUMBER_LOW = 0x48     # m -> s
CS_IDENTIFY_REMOTE_SLAVE_REVISION_NUMBER_HIGH = 0x49    # m -> s
CS_IDENTIFY_REMOTE_SLAVE_SERIAL_NUMBER_LOW = 0x4A       # m -> s
CS_IDENTIFY_REMOTE_SLAVE_SERIAL_NUMBER_HIGH = 0x4B      # m -> s
CS_IDENTIFY_NON_CONFIGURED_REMOTE_SLAVE = 0x4C          # m -> s
CS_IDENTIFY_SLAVE = 0x4F                                # s -> m
CS_IDENTIFY_NON_CONFIGURED_SLAVE = 0x50                 # s -> m
CS_FAST_SCAN = 0x51                                     # m -> s
CS_INQUIRE_VENDOR_ID = 0x5A
CS_INQUIRE_PRODUCT_CODE = 0x5B
CS_INQUIRE_REVISION_NUMBER = 0x5C
CS_INQUIRE_SERIAL_NUMBER = 0x5D
CS_INQUIRE_NODE_ID = 0x5E

# obsolete
SWITCH_MODE_GLOBAL = 0x04
CONFIGURE_NODE_ID = 0x11
CONFIGURE_BIT_TIMING = 0x13
STORE_CONFIGURATION = 0x17
INQUIRE_NODE_ID = 0x5E

ERROR_NONE = 0
ERROR_INADMISSIBLE = 1

ERROR_STORE_NONE = 0
ERROR_STORE_NOT_SUPPORTED = 1
ERROR_STORE_ACCESS_PROBLEM = 2

ERROR_VENDOR_SPECIFIC = 0xff

ListMessageNeedResponse = [
    CS_CONFIGURE_NODE_ID,
    CS_CONFIGURE_BIT_TIMING,
    CS_STORE_CONFIGURATION,
    CS_SWITCH_STATE_SELECTIVE_SERIAL_NUMBER,
    CS_FAST_SCAN,
    CS_INQUIRE_VENDOR_ID,
    CS_INQUIRE_PRODUCT_CODE,
    CS_INQUIRE_REVISION_NUMBER,
    CS_INQUIRE_SERIAL_NUMBER,
    CS_INQUIRE_NODE_ID,
]


class LssMaster:
    """The Master of Layer Setting Services"""

    LSS_TX_COBID = 0x7E5
    LSS_RX_COBID = 0x7E4

    WAITING_STATE = 0x00
    CONFIGURATION_STATE = 0x01

    # obsolete
    NORMAL_MODE = 0x00
    CONFIGURATION_MODE = 0x01

    #: Max time in seconds to wait for response from server
    RESPONSE_TIMEOUT = 0.5

    def __init__(self) -> None:
        self.network: canopen.network.Network = canopen.network._UNINITIALIZED_NETWORK
        self._node_id = 0
        self._data = None
        self.responses = queue.Queue()

    def send_switch_state_global(self, mode):
        """switch mode to CONFIGURATION_STATE or WAITING_STATE
        in the all slaves on CAN bus.
        There is no reply for this request

        :param int mode:
            CONFIGURATION_STATE or WAITING_STATE
        """
        pass

    def send_switch_mode_global(self, mode):
        """obsolete"""
        pass

    def send_switch_state_selective(self,
                                    vendorId, productCode, revisionNumber, serialNumber):
        """switch mode from WAITING_STATE to CONFIGURATION_STATE
        only if 128bits LSS address matches with the arguments.
        It sends 4 messages for each argument.
        Then wait the response from the slave.
        There will be no response if there is no matching slave

        :param int vendorId:
            object index 0x1018 subindex 1
        :param int productCode:
            object index 0x1018 subindex 2
        :param int revisionNumber:
            object index 0x1018 subindex 3
        :param int serialNumber:
            object index 0x1018 subindex 4

        :return:
            True if any slave responds.
            False if there is no response.
        :rtype: bool
        """
        pass

    def inquire_node_id(self):
        """Read the node id.
        CANopen node id must be within the range from 1 to 127.

        :return:
            node id. 0 means it is not read by LSS protocol
        :rtype: int
        """
        pass

    def inquire_lss_address(self, req_cs):
        """Read the part of LSS address.
            VENDOR_ID, PRODUCT_CODE, REVISION_NUMBER, or SERIAL_NUMBER

        :param int req_cs:
            command specifier for request

        :return:
            part of LSS address
        :rtype: int
        """
        pass

    def configure_node_id(self, new_node_id):
        """Set the node id

        :param int new_node_id:
            new node id to set
        """
        pass

    def configure_bit_timing(self, new_bit_timing):
        """Set the bit timing.

        :param int new_bit_timing:
            bit timing index.
            0: 1 MBit/sec, 1: 800 kBit/sec,
            2: 500 kBit/sec, 3: 250 kBit/sec,
            4: 125 kBit/sec  5: 100 kBit/sec,
            6: 50 kBit/sec, 7: 20 kBit/sec,
            8: 10 kBit/sec
        """
        pass

    def activate_bit_timing(self, switch_delay_ms):
        """Activate the bit timing.

        :param uint16_t switch_delay_ms:
            The slave that receives this message waits for switch delay,
            then activate the bit timing. But it shouldn't send any message
            until another switch delay is elapsed.
        """
        pass

    def store_configuration(self):
        """Store node id and baud rate.
        """
        pass

    def send_identify_remote_slave(self,
                                   vendorId, productCode,
                                   revisionNumberLow, revisionNumberHigh,
                                   serialNumberLow, serialNumberHigh):

        """This command sends the range of LSS address to find the slave nodes
        in the specified range

        :param int vendorId:
        :param int productCode:
        :param int revisionNumberLow:
        :param int revisionNumberHigh:
        :param int serialNumberLow:
        :param int serialNumberHigh:

        :return:
            True if any slave responds.
            False if there is no response.
        :rtype: bool
        """
        pass

    def send_identify_non_configured_remote_slave(self):
        # TODO it should handle the multiple respones from slaves
        pass

    def fast_scan(self):
        """This command sends a series of fastscan message
        to find unconfigured slave with lowest number of LSS idenities

        :return:
            True if a slave is found.
            False if there is no candidate.
            list is the LSS identities [vendor_id, product_code, revision_number, serial_number]
        :rtype: bool, list
        """
        pass

    def __send_fast_scan_message(self, id_number, bit_checker, lss_sub, lss_next):
        pass

    def __send_lss_address(self, req_cs, number):
        pass

    def __send_inquire_node_id(self):
        """
        :return:
            Current node id
        :rtype: int
        """
        pass

    def __send_inquire_lss_address(self, req_cs):
        """
        :return:
            part of address. e.g., vendor ID or product code,  ..
        :rtype: int
        """
        pass

    def __send_configure(self, req_cs, value1=0, value2=0):
        """Send a message to set a key with values"""
        pass

    def __send_command(self, message):
        """Send a LSS operation code to the network

        :param bytearray message:
            LSS request message.

        :return:
            response
            None if there is no response
        :rtype: bytes
        """
        pass

    def on_message_received(self, can_id, data, timestamp):
        pass


class LssError(Exception):
    """Some LSS operation failed."""
