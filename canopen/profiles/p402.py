# inspired by the NmtMaster code
import logging
import time

from canopen.node import RemoteNode
from canopen.pdo import PdoMap
from canopen.sdo import SdoCommunicationError


logger = logging.getLogger(__name__)


class State402:
    # Controlword (0x6040) commands
    CW_OPERATION_ENABLED = 0x000F
    CW_SHUTDOWN = 0x0006
    CW_SWITCH_ON = 0x0007
    CW_QUICK_STOP = 0x0002
    CW_DISABLE_VOLTAGE = 0x0000
    CW_SWITCH_ON_DISABLED = 0x0080

    CW_CODE_COMMANDS = {
        CW_SWITCH_ON_DISABLED:          'SWITCH ON DISABLED',
        CW_DISABLE_VOLTAGE:             'DISABLE VOLTAGE',
        CW_SHUTDOWN:                    'READY TO SWITCH ON',
        CW_SWITCH_ON:                   'SWITCHED ON',
        CW_OPERATION_ENABLED:           'OPERATION ENABLED',
        CW_QUICK_STOP:                  'QUICK STOP ACTIVE',
    }

    CW_COMMANDS_CODE = {
        'SWITCH ON DISABLED':           CW_SWITCH_ON_DISABLED,
        'DISABLE VOLTAGE':              CW_DISABLE_VOLTAGE,
        'READY TO SWITCH ON':           CW_SHUTDOWN,
        'SWITCHED ON':                  CW_SWITCH_ON,
        'OPERATION ENABLED':            CW_OPERATION_ENABLED,
        'QUICK STOP ACTIVE':            CW_QUICK_STOP,
    }

    # Statusword 0x6041 bitmask and values in the list in the dictionary value
    SW_MASK = {
        'NOT READY TO SWITCH ON':       (0x4F, 0x00),
        'SWITCH ON DISABLED':           (0x4F, 0x40),
        'READY TO SWITCH ON':           (0x6F, 0x21),
        'SWITCHED ON':                  (0x6F, 0x23),
        'OPERATION ENABLED':            (0x6F, 0x27),
        'FAULT':                        (0x4F, 0x08),
        'FAULT REACTION ACTIVE':        (0x4F, 0x0F),
        'QUICK STOP ACTIVE':            (0x6F, 0x07),
    }

    # Transition path to reach and state without a direct transition
    NEXTSTATE2ANY = {
        ('START'):                                                      'NOT READY TO SWITCH ON',
        ('FAULT', 'NOT READY TO SWITCH ON', 'QUICK STOP ACTIVE'):       'SWITCH ON DISABLED',
        ('SWITCH ON DISABLED'):                                         'READY TO SWITCH ON',
        ('READY TO SWITCH ON'):                                         'SWITCHED ON',
        ('SWITCHED ON'):                                                'OPERATION ENABLED',
        ('FAULT REACTION ACTIVE'):                                      'FAULT',
    }

    # Tansition table from the DS402 State Machine
    TRANSITIONTABLE = {
        # disable_voltage ---------------------------------------------------------------------
        ('READY TO SWITCH ON', 'SWITCH ON DISABLED'):     CW_DISABLE_VOLTAGE,  # transition 7
        ('OPERATION ENABLED', 'SWITCH ON DISABLED'):      CW_DISABLE_VOLTAGE,  # transition 9
        ('SWITCHED ON', 'SWITCH ON DISABLED'):            CW_DISABLE_VOLTAGE,  # transition 10
        ('QUICK STOP ACTIVE', 'SWITCH ON DISABLED'):      CW_DISABLE_VOLTAGE,  # transition 12
        # automatic ---------------------------------------------------------------------------
        ('NOT READY TO SWITCH ON', 'SWITCH ON DISABLED'): 0x00,  # transition 1
        ('START', 'NOT READY TO SWITCH ON'):              0x00,  # transition 0
        ('FAULT REACTION ACTIVE', 'FAULT'):               0x00,  # transition 14
        # shutdown ----------------------------------------------------------------------------
        ('SWITCH ON DISABLED', 'READY TO SWITCH ON'):     CW_SHUTDOWN,  # transition 2
        ('SWITCHED ON', 'READY TO SWITCH ON'):            CW_SHUTDOWN,  # transition 6
        ('OPERATION ENABLED', 'READY TO SWITCH ON'):      CW_SHUTDOWN,  # transition 8
        # switch_on ---------------------------------------------------------------------------
        ('READY TO SWITCH ON', 'SWITCHED ON'):            CW_SWITCH_ON,  # transition 3
        ('OPERATION ENABLED', 'SWITCHED ON'):             CW_SWITCH_ON,  # transition 5
        # enable_operation --------------------------------------------------------------------
        ('SWITCHED ON', 'OPERATION ENABLED'):             CW_OPERATION_ENABLED,  # transition 4
        ('QUICK STOP ACTIVE', 'OPERATION ENABLED'):       CW_OPERATION_ENABLED,  # transition 16
        # quickstop ---------------------------------------------------------------------------
        ('OPERATION ENABLED', 'QUICK STOP ACTIVE'):       CW_QUICK_STOP,  # transition 11
        # fault -------------------------------------------------------------------------------
        ('FAULT', 'SWITCH ON DISABLED'):                  CW_SWITCH_ON_DISABLED,  # transition 15
    }

    @staticmethod
    def next_state_indirect(_from):
        """Return the next state needed to reach any state indirectly.

        The chosen path always points toward the OPERATION ENABLED state, except when
        coming from QUICK STOP ACTIVE.  In that case, it will cycle through SWITCH ON
        DISABLED first, as there would have been a direct transition if the opposite was
        desired.

        :param str target: Target state.
        :return: Next target to change.
        :rtype: str
        """
        pass


class OperationMode:
    NO_MODE = 0
    PROFILED_POSITION = 1
    VELOCITY = 2
    PROFILED_VELOCITY = 3
    PROFILED_TORQUE = 4
    HOMING = 6
    INTERPOLATED_POSITION = 7
    CYCLIC_SYNCHRONOUS_POSITION = 8
    CYCLIC_SYNCHRONOUS_VELOCITY = 9
    CYCLIC_SYNCHRONOUS_TORQUE = 10
    OPEN_LOOP_SCALAR_MODE = -1
    OPEN_LOOP_VECTOR_MODE = -2

    CODE2NAME = {
        NO_MODE:                        'NO MODE',
        PROFILED_POSITION:              'PROFILED POSITION',
        VELOCITY:                       'VELOCITY',
        PROFILED_VELOCITY:              'PROFILED VELOCITY',
        PROFILED_TORQUE:                'PROFILED TORQUE',
        HOMING:                         'HOMING',
        INTERPOLATED_POSITION:          'INTERPOLATED POSITION',
        CYCLIC_SYNCHRONOUS_POSITION:    'CYCLIC SYNCHRONOUS POSITION',
        CYCLIC_SYNCHRONOUS_VELOCITY:    'CYCLIC SYNCHRONOUS VELOCITY',
        CYCLIC_SYNCHRONOUS_TORQUE:      'CYCLIC SYNCHRONOUS TORQUE',
    }

    NAME2CODE = {
        'NO MODE':                      NO_MODE,
        'PROFILED POSITION':            PROFILED_POSITION,
        'VELOCITY':                     VELOCITY,
        'PROFILED VELOCITY':            PROFILED_VELOCITY,
        'PROFILED TORQUE':              PROFILED_TORQUE,
        'HOMING':                       HOMING,
        'INTERPOLATED POSITION':        INTERPOLATED_POSITION,
        'CYCLIC SYNCHRONOUS POSITION':  CYCLIC_SYNCHRONOUS_POSITION,
        'CYCLIC SYNCHRONOUS VELOCITY':  CYCLIC_SYNCHRONOUS_VELOCITY,
        'CYCLIC SYNCHRONOUS TORQUE':    CYCLIC_SYNCHRONOUS_TORQUE,
    }

    SUPPORTED = {
        'NO MODE':                      0x0000,
        'PROFILED POSITION':            0x0001,
        'VELOCITY':                     0x0002,
        'PROFILED VELOCITY':            0x0004,
        'PROFILED TORQUE':              0x0008,
        'HOMING':                       0x0020,
        'INTERPOLATED POSITION':        0x0040,
        'CYCLIC SYNCHRONOUS POSITION':  0x0080,
        'CYCLIC SYNCHRONOUS VELOCITY':  0x0100,
        'CYCLIC SYNCHRONOUS TORQUE':    0x0200,
    }


class Homing:
    CW_START = 0x10
    CW_HALT = 0x100

    HM_ON_POSITIVE_FOLLOWING_ERROR = -8
    HM_ON_NEGATIVE_FOLLOWING_ERROR = -7
    HM_ON_POSITIVE_FOLLOWING_AND_INDEX_PULSE = -6
    HM_ON_NEGATIVE_FOLLOWING_AND_INDEX_PULSE = -5
    HM_ON_THE_POSITIVE_MECHANICAL_LIMIT = -4
    HM_ON_THE_NEGATIVE_MECHANICAL_LIMIT = -3
    HM_ON_THE_POSITIVE_MECHANICAL_LIMIT_AND_INDEX_PULSE = -2
    HM_ON_THE_NEGATIVE_MECHANICAL_LIMIT_AND_INDEX_PULSE = -1
    HM_NO_HOMING_OPERATION = 0
    HM_ON_THE_NEGATIVE_LIMIT_SWITCH_AND_INDEX_PULSE = 1
    HM_ON_THE_POSITIVE_LIMIT_SWITCH_AND_INDEX_PULSE = 2
    HM_ON_THE_POSITIVE_HOME_SWITCH_AND_INDEX_PULSE = (3, 4)
    HM_ON_THE_NEGATIVE_HOME_SWITCH_AND_INDEX_PULSE = (5, 6)
    HM_ON_THE_NEGATIVE_LIMIT_SWITCH = 17
    HM_ON_THE_POSITIVE_LIMIT_SWITCH = 18
    HM_ON_THE_POSITIVE_HOME_SWITCH = (19, 20)
    HM_ON_THE_NEGATIVE_HOME_SWITCH = (21, 22)
    HM_ON_NEGATIVE_INDEX_PULSE = 33
    HM_ON_POSITIVE_INDEX_PULSE = 34
    HM_ON_CURRENT_POSITION = 35

    STATES = {
        'IN PROGRESS':                  (0x3400, 0x0000),
        'INTERRUPTED':                  (0x3400, 0x0400),
        'ATTAINED':                     (0x3400, 0x1000),
        'TARGET REACHED':               (0x3400, 0x1400),
        'ERROR VELOCITY IS NOT ZERO':   (0x3400, 0x2000),
        'ERROR VELOCITY IS ZERO':       (0x3400, 0x2400),
    }


class BaseNode402(RemoteNode):
    """A CANopen CiA 402 profile slave node.

    :param int node_id:
        Node ID (set to None or 0 if specified by object dictionary)
    :param object_dictionary:
        Object dictionary as either a path to a file, an ``ObjectDictionary``
        or a file like object.
    :type object_dictionary: :class:`str`, :class:`canopen.ObjectDictionary`
    """

    TIMEOUT_RESET_FAULT = 0.4           # seconds
    TIMEOUT_SWITCH_OP_MODE = 0.5        # seconds
    TIMEOUT_SWITCH_STATE_FINAL = 0.8    # seconds
    TIMEOUT_SWITCH_STATE_SINGLE = 0.4   # seconds
    TIMEOUT_CHECK_TPDO = 0.2            # seconds
    TIMEOUT_HOMING_DEFAULT = 30         # seconds

    def __init__(self, node_id, object_dictionary):
        super(BaseNode402, self).__init__(node_id, object_dictionary)
        self.tpdo_values = {}  # { index: value from last received TPDO }
        self.tpdo_pointers: dict[int, PdoMap] = {}
        self.rpdo_pointers: dict[int, PdoMap] = {}

    def setup_402_state_machine(self, read_pdos=True):
        """Configure the state machine by searching for a TPDO that has the StatusWord mapped.

        :param bool read_pdos: Upload current PDO configuration from node.
        :raises ValueError:
            If the the node can't find a Statusword configured in any of the TPDOs.
        """
        pass

    def setup_pdos(self, upload=True):
        """Find the relevant PDO configuration to handle the state machine.

        :param bool upload:
            Retrieve up-to-date configuration via SDO.  If False, the node's mappings must
            already be configured in the object, matching the drive's settings.
        :raises AssertionError:
            When the node's NMT state disallows SDOs for reading the PDO configuration.
        """
        pass

    def _init_tpdo_values(self):
        pass

    def _init_rpdo_pointers(self):
        # If RPDOs have overlapping indecies, rpdo_pointers will point to
        # the first RPDO that has that index configured.
        pass

    def _check_controlword_configured(self):
        pass

    def _check_statusword_configured(self):
        pass

    def _check_op_mode_configured(self):
        pass

    def reset_from_fault(self):
        """Reset node from fault and set it to Operation Enable state."""
        pass

    def is_faulted(self):
        pass

    def _homing_status(self):
        """Interpret the current Statusword bits as homing state string."""
        pass

    def is_homed(self, restore_op_mode=False):
        """Switch to homing mode and determine its status.

        :param bool restore_op_mode: Switch back to the previous operation mode when done.
        :return: If the status indicates successful homing.
        :rtype: bool
        """
        pass

    def homing(self, timeout=None, restore_op_mode=False):
        """Execute the configured Homing method on the node.

        :param int timeout: Timeout value (default: 30, zero to disable).
        :param bool restore_op_mode:
            Switch back to the previous operation mode after homing (default: no).
        :return: If the homing was complete with success.
        :rtype: bool
        """
        pass

    @property
    def op_mode(self):
        """The node's Operation Mode stored in the object 0x6061.

        Uses SDO or PDO to access the current value.  The modes are passed as one of the
        following strings:

        - 'NO MODE'
        - 'PROFILED POSITION'
        - 'VELOCITY'
        - 'PROFILED VELOCITY'
        - 'PROFILED TORQUE'
        - 'HOMING'
        - 'INTERPOLATED POSITION'
        - 'CYCLIC SYNCHRONOUS POSITION'
        - 'CYCLIC SYNCHRONOUS VELOCITY'
        - 'CYCLIC SYNCHRONOUS TORQUE'
        - 'OPEN LOOP SCALAR MODE'
        - 'OPEN LOOP VECTOR MODE'

        :raises TypeError: When setting a mode not advertised as supported by the node.
        :raises RuntimeError: If the switch is not confirmed within the configured timeout.
        """
        pass

    @op_mode.setter
    def op_mode(self, mode):
        pass

    def _clear_target_values(self):
        # [target velocity, target position, target torque]
        pass

    def is_op_mode_supported(self, mode):
        """Check if the operation mode is supported by the node.

        The object listing the supported modes is retrieved once using SDO, then cached
        for later checks.

        :param str mode: Same format as the :attr:`op_mode` property.
        :return: If the operation mode is supported.
        :rtype: bool
        """
        pass

    def on_TPDOs_update_callback(self, mapobject: PdoMap):
        """Cache updated values from a TPDO received from this node.

        :param mapobject: The received PDO message.
        """
        pass

    @property
    def statusword(self):
        """Return the last read value of the Statusword (0x6041) from the device.

        If the object 0x6041 is not configured in any TPDO it will fall back to the SDO
        mechanism and try to get the value.
        """
        pass

    def check_statusword(self, timeout=None):
        """Report an up-to-date reading of the Statusword (0x6041) from the device.

        If the TPDO with the Statusword is configured as periodic, this method blocks
        until one was received.  Otherwise, it uses the SDO fallback of the ``statusword``
        property.

        :param timeout: Maximum time in seconds to wait for TPDO reception.
        :raises RuntimeError: Occurs when the given timeout expires without a TPDO.
        :return: Updated value of the ``statusword`` property.
        :rtype: int
        """
        pass

    @property
    def controlword(self):
        """Send a state change command using PDO or SDO.

        :param int value: Controlword value to set.
        :raises RuntimeError: Read access to the controlword is not intended.
        """
        raise RuntimeError('The Controlword is write-only.')

    @controlword.setter
    def controlword(self, value):
        pass

    @property
    def state(self):
        """Manipulate current state of the DS402 State Machine on the node.

        Uses the last received Statusword value for read access, and manipulates the
        :attr:`controlword` for changing states.  The states are passed as one of the
        following strings:

        - 'NOT READY TO SWITCH ON' (cannot be switched to deliberately)
        - 'SWITCH ON DISABLED'
        - 'READY TO SWITCH ON'
        - 'SWITCHED ON'
        - 'OPERATION ENABLED'
        - 'FAULT' (cannot be switched to deliberately)
        - 'FAULT REACTION ACTIVE' (cannot be switched to deliberately)
        - 'QUICK STOP ACTIVE'
        - 'DISABLE VOLTAGE' (only as a command when writing)

        :raises RuntimeError: If the switch is not confirmed within the configured timeout.
        :raises ValueError: Trying to execute a illegal transition in the state machine.
        """
        pass

    @state.setter
    def state(self, target_state):
        pass

    def _next_state(self, target_state):
        pass

    def _change_state(self, target_state):
        pass
