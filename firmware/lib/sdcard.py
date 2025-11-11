# Save this file on your ESP32 as sdcard.py

"""
MicroPython driver for SD cards using SPI bus.

This is a port of the Arduino SD library for MicroPython.
(https://github.com/arduino-libraries/SD)
"""

import time
from micropython import const

_CMD_TIMEOUT = const(100)

_R1_IDLE_STATE = const(1 << 0)
_R1_ERASE_RESET = const(1 << 1)
_R1_ILLEGAL_COMMAND = const(1 << 2)
_R1_COM_CRC_ERROR = const(1 << 3)
_R1_ERASE_SEQUENCE_ERROR = const(1 << 4)
_R1_ADDRESS_ERROR = const(1 << 5)
_R1_PARAMETER_ERROR = const(1 << 6)

# R7 (SPI)
_R7_IDLE_STATE = const(1 << 0)
_R7_ERASE_RESET = const(1 << 1)
_R7_ILLEGAL_COMMAND = const(1 << 2)
_R7_COM_CRC_ERROR = const(1 << 3)
_R7_ERASE_SEQUENCE_ERROR = const(1 << 4)
_R7_ADDRESS_ERROR = const(1 << 5)
_R7_PARAMETER_ERROR = const(1 << 6)
_R7_VOLTAGE_ACCEPTED = const(0xF)  # Mask
_R7_VOLTAGE_2V7_3V6 = const(1 << 8)
_R7_ECHO_BACK = const(0xAA)  # Echo back pattern

# Command definitions
_CMD0 = const(0)  # GO_IDLE_STATE
_CMD1 = const(1)  # SEND_OP_COND
_CMD8 = const(8)  # SEND_IF_COND
_CMD9 = const(9)  # SEND_CSD
_CMD10 = const(10)  # SEND_CID
_CMD12 = const(12)  # STOP_TRANSMISSION
_CMD13 = const(13)  # SEND_STATUS
_CMD16 = const(16)  # SET_BLOCKLEN
_CMD17 = const(17)  # READ_SINGLE_BLOCK
_CMD18 = const(18)  # READ_MULTIPLE_BLOCK
_CMD24 = const(24)  # WRITE_BLOCK
_CMD25 = const(25)  # WRITE_MULTIPLE_BLOCK
_CMD32 = const(32)  # ERASE_WR_BLK_START_ADDR
_CMD33 = const(33)  # ERASE_WR_BLK_END_ADDR
_CMD38 = const(38)  # ERASE
_CMD55 = const(55)  # APP_CMD
_CMD58 = const(58)  # READ_OCR
_ACMD41 = const(41)  # SD_SEND_OP_COND (application-specific)

# Card types
_CARD_TYPE_SD1 = const(1)
_CARD_TYPE_SD2 = const(2)
_CARD_TYPE_SDHC = const(3)


class SDCard:
    def __init__(self, spi, cs):
        self.spi = spi
        self.cs = cs

        self.cmdbuf = bytearray(6)
        self.tokenbuf = bytearray(1)
        self.buf = bytearray(512)

        self.cs.init(self.cs.OUT, value=1)

        self.card_type = None
        self.csd = None
        self.cid = None
        self.ocr = None
        self.init_card()

    def init_card(self):
        # init CS pin
        self.cs.value(1)

        # Set SPI clock to a low speed (e.g., 250kHz) for initialization
        # The main SPI bus frequency is often too high for an uninitialized card.
        try:
            self.spi.init(baudrate=250000)
        except TypeError:
            # Some ports might not support re-init with baudrate
            self.spi.init()  # Use default slow speed if re-init fails
            # If your port's default is high, you may need to pass baudrate in SPI constructor

        # 80 dummy clock cycles
        for _ in range(10):
            self.spi.write(b"\xff")

        # Select card
        self.cs.value(0)

        # Send CMD0 (GO_IDLE_STATE)
        if self._cmd(_CMD0, 0, 0x95) != _R1_IDLE_STATE:
            raise OSError("SD card: No response to CMD0")

        # Send CMD8 (SEND_IF_COND)
        r7 = self._cmd_r7(_CMD8, 0x1AA, 0x87)
        if r7 == _R1_IDLE_STATE:
            self.card_type = _CARD_TYPE_SD2
        elif r7 == (_R1_IDLE_STATE | _R1_ILLEGAL_COMMAND):
            self.card_type = _CARD_TYPE_SD1
        else:
            raise OSError("SD card: Invalid response to CMD8")

        # Send ACMD41 (SD_SEND_OP_COND)
        if self.card_type == _CARD_TYPE_SD2:
            arg = 0x40000000  # Host supports SDHC
        else:
            arg = 0

        # Poll until card is ready
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 1000:
            if self._cmd(_CMD55, 0) == _R1_IDLE_STATE:
                if self._cmd(_ACMD41, arg) == 0:
                    break
            time.sleep_ms(50)
        else:
            raise OSError("SD card: Timeout on ACMD41")

        # Check for SDHC card
        if self.card_type == _CARD_TYPE_SD2:
            if self._cmd_r7(_CMD58, 0) != 0:
                raise OSError("SD card: Error on CMD58")
            if self.tokenbuf[0] & 0x40:
                self.card_type = _CARD_TYPE_SDHC

        # Set block size to 512 bytes
        if self._cmd(_CMD16, 512) != 0:
            raise OSError("SD card: Error on CMD16 (set blocklen)")

        # Set SPI to full speed
        # Note: 10MHz is a safe speed. Some cards support 20MHz+.
        self.spi.init(baudrate=10000000)

        # Deselect card
        self.cs.value(1)
        self.spi.write(b"\xff")  # Dummy clock

        # Read CSD
        self.csd = bytearray(16)
        if self._readinto(_CMD9, self.csd) != 0:
            raise OSError("SD card: Error reading CSD")

        # Read CID
        self.cid = bytearray(16)
        if self._readinto(_CMD10, self.cid) != 0:
            raise OSError("SD card: Error reading CID")

        # Read OCR
        self.ocr = bytearray(4)
        if self._cmd_r7(_CMD58, 0) != 0:
            raise OSError("SD card: Error reading OCR")
        self.ocr[:] = self.tokenbuf[0:4]

    def _cmd(self, cmd, arg, crc=0):
        self.cmdbuf[0] = 0x40 | cmd
        self.cmdbuf[1] = (arg >> 24) & 0xFF
        self.cmdbuf[2] = (arg >> 16) & 0xFF
        self.cmdbuf[3] = (arg >> 8) & 0xFF
        self.cmdbuf[4] = arg & 0xFF
        self.cmdbuf[5] = crc

        self.cs.value(0)
        self.spi.write(self.cmdbuf)

        # Wait for response
        for _ in range(_CMD_TIMEOUT):
            self.spi.readinto(self.tokenbuf, 0xFF)
            if not (self.tokenbuf[0] & 0x80):
                self.cs.value(1)
                self.spi.write(b"\xff")  # Dummy clock
                return self.tokenbuf[0]

        # Timeout
        self.cs.value(1)
        self.spi.write(b"\xff")  # Dummy clock
        return -1  # Error

    def _cmd_r7(self, cmd, arg, crc=0):
        self.cmdbuf[0] = 0x40 | cmd
        self.cmdbuf[1] = (arg >> 24) & 0xFF
        self.cmdbuf[2] = (arg >> 16) & 0xFF
        self.cmdbuf[3] = (arg >> 8) & 0xFF
        self.cmdbuf[4] = arg & 0xFF
        self.cmdbuf[5] = crc

        self.cs.value(0)
        self.spi.write(self.cmdbuf)

        # Wait for response
        for _ in range(_CMD_TIMEOUT):
            self.spi.readinto(self.tokenbuf, 0xFF)
            if not (self.tokenbuf[0] & 0x80):
                # Read remaining 4 bytes of R7 response
                self.spi.readinto(self.tokenbuf, 0xFF)
                self.spi.readinto(self.tokenbuf, 0xFF)
                self.spi.readinto(self.tokenbuf, 0xFF)
                self.spi.readinto(self.tokenbuf, 0xFF)
                self.cs.value(1)
                self.spi.write(b"\xff")  # Dummy clock
                return 0  # Success (R1 part of R7 is 0)

        # Timeout
        self.cs.value(1)
        self.spi.write(b"\xff")  # Dummy clock
        return -1  # Error

    def _wait_ready(self):
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 500:
            self.spi.readinto(self.tokenbuf, 0xFF)
            if self.tokenbuf[0] == 0xFF:
                return 0
            time.sleep_ms(1)
        return -1  # Timeout

    def _readinto(self, cmd, buf, arg=0):
        if self._cmd(cmd, arg) != 0:
            return -1

        self.cs.value(0)

        # Wait for data token
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 200:
            self.spi.readinto(self.tokenbuf, 0xFF)
            if self.tokenbuf[0] == 0xFE:  # Start block token
                break
            time.sleep_ms(1)
        else:
            self.cs.value(1)
            self.spi.write(b"\xff")
            return -1  # Timeout

        # Read data block
        self.spi.readinto(buf, 0xFF)

        # Read 2-byte CRC
        self.spi.write(b"\xff")
        self.spi.write(b"\xff")

        self.cs.value(1)
        self.spi.write(b"\xff")  # Dummy clock
        return 0

    def _write(self, cmd, buf, token=0xFE, arg=0):
        if self._cmd(cmd, arg) != 0:
            return -1

        self.cs.value(0)

        # Send data packet
        self.spi.write(bytearray([token]))  # Start block token
        self.spi.write(buf)  # Data
        self.spi.write(b"\xff\xff")  # Dummy CRC

        # Wait for response token
        for _ in range(_CMD_TIMEOUT):
            self.spi.readinto(self.tokenbuf, 0xFF)
            if self.tokenbuf[0] & 0x10 == 0:  # Check for data response token
                break

        if (self.tokenbuf[0] & 0x0F) != 0x05:  # Check if data accepted
            self.cs.value(1)
            self.spi.write(b"\xff")
            return -1  # Data rejected

        # Wait for card to finish writing
        if self._wait_ready() != 0:
            self.cs.value(1)
            self.spi.write(b"\xff")
            return -1  # Timeout

        self.cs.value(1)
        self.spi.write(b"\xff")  # Dummy clock
        return 0

    # --- Block Device API ---
    def readblocks(self, block_num, buf, num_blocks=1):
        n = len(buf)
        if n % 512 != 0:
            raise ValueError("Buffer size must be a multiple of 512")

        offset = 0
        for i in range(num_blocks):
            addr = block_num + i
            if self.card_type != _CARD_TYPE_SDHC:
                addr *= 512  # Convert to byte address for SDv1/v2

            if self._readinto(_CMD17, self.buf, addr) != 0:
                return -1  # Error

            buf[offset:offset + 512] = self.buf
            offset += 512

        return 0

    def writeblocks(self, block_num, buf, num_blocks=1):
        n = len(buf)
        if n % 512 != 0:
            raise ValueError("Buffer size must be a multiple of 512")

        offset = 0
        for i in range(num_blocks):
            addr = block_num + i
            if self.card_type != _CARD_TYPE_SDHC:
                addr *= 512  # Convert to byte address for SDv1/v2

            self.buf[:] = buf[offset:offset + 512]

            if self._write(_CMD24, self.buf, 0xFE, addr) != 0:
                return -1  # Error

            offset += 512

        return 0

    def ioctl(self, op, arg):
        if op == 4:  # Get number of blocks
            if self.csd is None:
                return -1

            c_size = ((self.csd[6] & 0x03) << 10) | (self.csd[7] << 2) | ((self.csd[8] & 0xC0) >> 6)

            if self.card_type == _CARD_TYPE_SDHC:
                # SDHC CSD v2.0 - size is in 512K blocks
                return (c_size + 1) * 1024
            else:
                # SDv1/v2 CSD v1.0 - size is in blocks
                c_size_mult = ((self.csd[9] & 0x03) << 1) | ((self.csd[10] & 0x80) >> 7)
                read_bl_len = self.csd[5] & 0x0F
                capacity = (c_size + 1) * (2 ** (c_size_mult + 2)) * (2 ** read_bl_len)
                return capacity // 512  # Return number of 512-byte blocks

        if op == 5:  # Get block size
            return 512

        return -1
