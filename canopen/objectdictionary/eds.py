from __future__ import annotations

import copy
import logging
import re
from configparser import NoOptionError, NoSectionError, RawConfigParser
from typing import TYPE_CHECKING

from canopen.objectdictionary import (
    ODArray,
    ODRecord,
    ODVariable,
    ObjectDictionary,
    datatypes,
    objectcodes,
)
from canopen.sdo import SdoClient

if TYPE_CHECKING:
    import canopen.network


logger = logging.getLogger(__name__)

def import_eds(source, node_id):
    pass


def import_from_node(node_id: int, network: canopen.network.Network):
    """ Download the configuration from the remote node
    :param int node_id: Identifier of the node
    :param network: network object
    """
    pass


def _calc_bit_length(data_type):
    pass


def _signed_int_from_hex(hex_str, bit_length):
    pass


def _convert_variable(node_id, var_type, value):
    pass


def _revert_variable(var_type, value):
    pass


def build_variable(eds, section, node_id, index, subindex=0):
    """Creates a object dictionary entry.
    :param eds: String stream of the eds file
    :param section:
    :param node_id: Node ID
    :param index: Index of the CANOpen object
    :param subindex: Subindex of the CANOpen object (if presente, else 0)
    """
    pass


def copy_variable(eds, section, subindex, src_var):
    pass


def export_dcf(od, dest=None, fileInfo={}):
    pass


def export_eds(od, dest=None, file_info={}, device_commisioning=False):
    pass