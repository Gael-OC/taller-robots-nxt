"""Parche macOS para nxt-python: evita Errno 19.

El backend USB hace dev.reset() antes de set_configuration().
En macOS + libusb eso invalida el handle y falla con
"No such device (it may have been disconnected)".

Este parche replica connect() sin el reset. Importalo antes de find():
  import nxt_usb_patch  # noqa: F401
  import nxt.locator
  b = nxt.locator.find()
"""
import nxt.backend.usb as _usb_backend
import nxt.brick as _brick


def _connect_sin_reset(self):
    self._dev.set_configuration()
    intf = self._dev.get_active_configuration()[(0, 0)]
    self._epout, self._epin = intf
    return _brick.Brick(self)


_usb_backend.USBSock.connect = _connect_sin_reset
