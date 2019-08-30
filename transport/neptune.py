import struct
import socket
from .base import PeerAbstract
from logf import logger


class Neptune(PeerAbstract):
    ProtocolMetaSize = 8
    ProtocolMagNum = 0x0001

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self._socket = self.writer.get_extra_info('socket')
        self.peername = self._socket.getpeername()
        self.buff = b''
        self.clen = 0

    async def on_connect(self):
        logger.info("connected: {}".format(self.peername))

    async def on_input(self, data):
        if data:
            self.buff += data

        msg_len = len(self.buff)
        if self.clen == 0:
            if msg_len < self.ProtocolMetaSize:
                return

            mag_num, self.clen = struct.unpack_from('!HH', self.buff, 0)
            if mag_num != self.ProtocolMagNum:
                self.quick_close()
                return

        if msg_len >= self.clen:
            await self.on_message(
                self.buff[self.ProtocolMetaSize: self.clen]
            )
            self.buff = self.buff[self.clen:]
            self.clen = 0

            # process remain data in buff
            await self.on_input(None)

    async def on_message(self, msg):
        logger.info("msg: {}".format(msg))

    async def send(self, data):
        # FIXME: message length limit
        length = len(data) + self.ProtocolMetaSize
        reserve = 0
        data = struct.pack(
            '!HHHH', self.ProtocolMagNum, length, reserve, reserve
        ) + data
        await super().send(data)

    async def on_close(self):
        logger.info("closed: {}".format(self.peername))

    def quick_close(self):
        logger.warn("Reset connection: {}".format(self.peername))
        if self._socket:
            # Reset connection
            self._socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0)
            )
        self.should_close = True
