import logging
import xml.etree.ElementTree as etree

from canopen import objectdictionary
from canopen.objectdictionary import ObjectDictionary


logger = logging.getLogger(__name__)

DATA_TYPES = {
    "BOOLEAN": objectdictionary.BOOLEAN,
    "INTEGER8": objectdictionary.INTEGER8,
    "INTEGER16": objectdictionary.INTEGER16,
    "INTEGER32": objectdictionary.INTEGER32,
    "UNSIGNED8": objectdictionary.UNSIGNED8,
    "UNSIGNED16": objectdictionary.UNSIGNED16,
    "UNSIGNED32": objectdictionary.UNSIGNED32,
    "REAL32": objectdictionary.REAL32,
    "VISIBLE_STRING": objectdictionary.VISIBLE_STRING,
    "DOMAIN": objectdictionary.DOMAIN
}


def import_epf(epf):
    """Import an EPF file.

    :param epf:
        Either a path to an EPF-file, a file-like object, or an instance of
        :class:`xml.etree.ElementTree.Element`.

    :returns:
        The Object Dictionary.
    :rtype: canopen.ObjectDictionary
    """
    pass


def build_variable(par_tree):
    pass
