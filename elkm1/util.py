"""Utility functions"""

import logging
import ssl
from .message import add_message_handler, sd_encode


LOG = logging.getLogger(__name__)

# pylint: disable=invalid-name
get_descriptions_in_progress = {}
sync_handlers = []

def add_sync_handler(sync_handler):
    """Register a fn that synchronizes part of the panel."""
    sync_handlers.append(sync_handler)

def call_sync_handlers():
    """Invoke the synchronization handlers."""
    LOG.debug("Synchronizing panel...")
    for sync_handler in sync_handlers:
        sync_handler()

def get_descriptions(elk, desc, callback):
    """
    Gets the descriptions for specified type
    When complete the callback is called with a list of descriptions
    """
    desc_type = desc[0]
    max_units = desc[1]
    results = [None] * max_units
    get_descriptions_in_progress[desc_type] = (max_units, callback, results, elk)
    add_message_handler('SD', sd_handler)
    elk.send(sd_encode(desc_type=desc_type, unit=0))

# pylint: disable=unused-argument
def sd_handler(desc_type, unit, desc, show_on_keypad):
    """Text description"""
    if desc_type not in get_descriptions_in_progress:
        LOG.debug("Text description response ignored")
        return

    max_units = get_descriptions_in_progress[desc_type][0]
    results = get_descriptions_in_progress[desc_type][2]
    if unit < 0 or unit >= max_units:
        callback = get_descriptions_in_progress[desc_type][1]
        callback(results)
        del get_descriptions_in_progress[desc_type]
        return

    elk = get_descriptions_in_progress[desc_type][3]
    results[unit] = desc
    elk.send(sd_encode(desc_type=desc_type, unit=unit+1))

def url_scheme_is_secure(url):
    """Check if the URL is one that requires SSL/TLS."""
    scheme, _dest = url.split('://')
    return scheme == 'elks'

def parse_url(url):
    """Parse a Elk connection string """
    scheme, dest = url.split('://')
    if scheme == 'serial':
        # No easy way to test, so not implemented; should use serial.async
        raise NotImplementedError("Elk serial connection not implemented")

    host = None
    ssl_context = None
    if scheme == 'elk':
        host, port = dest.split(':') if ':' in dest else (dest, 2101)
    elif scheme == 'elks':
        host, port = dest.split(':') if ':' in dest else (dest, 2601)
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        ssl_context.verify_mode = ssl.CERT_NONE
    else:
        raise ValueError("Invalid scheme '%s'" % scheme)
    return (scheme, host, int(port), ssl_context)
