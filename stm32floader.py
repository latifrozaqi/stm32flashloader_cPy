# Write your code here :-)
import time
import board
import busio
import digitalio

class stm32bl:
    #"""STM32 firmware loader class"""
    CMD_INIT = 0x7f
    CMD_ACK = 0x79
    CMD_NOACK = 0x1f
    CMD_GET = 0x00
    CMD_GET_VERSION = 0x01
    CMD_GET_ID = 0x02
    CMD_READ_MEMORY = 0x11
    CMD_GO = 0x21
    CMD_WRITE_MEMORY = 0x31
    CMD_ERASE = 0x43
    CMD_EXTENDED_ERASE = 0x44
    CMD_WRITE_PROTECT = 0x63
    CMD_WRITE_UNPROTECT = 0x73
    CMD_READOUT_PROTECT = 0x82
    CMD_READOUT_UNPROTECT = 0x92

    FLASH_START = 0x08000000
    CMD={0:"get command",1:"get version",2:"get id",
    17:"read memory cmd",33:"go cmd",49:"write mem cmd",
    67:"erase cmd",68:"ext erase cmd",99:"write protect cmd",
    115:"write unprotect cmd",130:"read protect cmd",
    146:"read unprotect cmd",121:"Acknowledge"}
    def __init__(self, txpin=board.IO33, rxpin=board.IO34, baudrate=9600, verbosity=1, rst=board.IO16):
        self.uart = busio.UART(txpin,rxpin,baudrate=baudrate,parity=busio.UART.Parity.EVEN)
        self.reset_pin=digitalio.DigitalInOut(rst)
        self.reset_pin.direction=digitalio.Direction.OUTPUT
        self.reset_pin.value=True
        self._verbosity = verbosity
        #self._connect(5)
        #self._gconnect(5)
        #self._allowed_commands = [self.CMD_GET, ]
        #self._boot_version = self._cmd_get()
        #print("bootver: %s\n"%(self._boot_version))
        #self._option_bytes = self._cmd_get_version()
        #print("bootver: %s\n"%(self._option_bytes))
        #self._dev_id = self._cmd_get_id()
        #print("bootver: %s\n"%(self._dev_id))
    def _reset_mcu(self):
        self.reset_pin.value=False
        time.sleep(0.1)
        self.reset_pin.value=True
    def _connect(self, repeat=1):
        """connect to boot-loader"""
        print("connecting to bootloader")
        self._reset_mcu()
        self.uart.write(bytes([self.CMD_INIT]))
        r=self.uart.read()
        if b'\x79' in r:
            print("connected to bootloader")
            return
        print("Can't connect to MCU boot-loader.")
    def cmd_general(self,cmd):
        cmd=[cmd,cmd^255]
        print(cmd)
        self.uart.write(bytes(cmd))
        r=self.uart.read()
        return r
    def write_address(self,data):
        if isinstance(data, (tuple, list)):
            xor = data[0]
            for i in data[1:]:
                xor ^= i
            data.append(xor)
        else:
            data = [data, data ^ 0xff]
        print(data)
        print("writing general data")
        self.uart.write(bytes(data))
        r=self.uart.read()
        return r
    def write_flash(self,data):
        if isinstance(data, (tuple, list)):
            xor = data[0]
            for i in data[1:]:
                xor ^= i
            data.append(xor)
        else:
            data = [data, data ^ 0xff]
        print(data)
        print("writing general data")
        self.uart.write(bytes(data))
        r=self.uart.read()
        return r
    def cmd_get(self):
        cmd=[0,255]
        self.uart.write(bytes(cmd))
        r=self.uart.read()
        if len(r):
            for i in r[3:]:
                try:
                    print(i,self.CMD[i])
                except:
                    print("error or no key: %d"%(i))
        return r
    def cmd_erase_glob(self):
        cmd=[67,188]
        self.uart.write(bytes(cmd))
        r=self.uart.read()
        if b'\x79' in r:
            print("erasing memory..")
            cmd=[255,0]
            self.uart.write(bytes(cmd))
            s=self.uart.read()
            if b'\x79' in s:
                print("erased memory")
                return
        print("erase failed")
    def _convert_32bit(self,val):
        return [
            val >> 24,
            0xff & (val >> 16),
            0xff & (val >> 8),
            0xff & val,
        ]
    def _cmd_write_memory(self, address, data):
        """Writes up to 256 bytes to the RAM or Flash memory
        starting from an address specified by the application"""
        print("CMD_WRITE_MEMORY(%08x, %d)" % (address, len(data)))
        r=self.cmd_general(self.CMD_WRITE_MEMORY)
        if r is not None:
            if not b'\x79' in r:
                print("not acknowledged - failed to write memory cmd")
                return 0
        else:
            print("transmission error - repeated")
            return 0
        print("write memory acknowledged - writing memory to address")
        r=self.write_address(self._convert_32bit(address))
        print(r)
        if not b'\x79' in r:
            print("not acknowledged - failed to write memory address")
            return
        return self.write_flash([len(data) - 1] + data)
    def write_memory(self,address,data):
        """write memory"""
        print("from 0x%08x (%d Bytes)" % (address, len(data)))
        _data = data[:]
        while _data:
            r=self._cmd_write_memory(address, _data[:256])
            if r>0:
                address += 256
                _data = _data[256:]
            else:
                pass
        print("done - write memory")
    def read_memory(self,address,mem):
        pass
    def cmd_write_bin(self,file_name,verify=False):
        """Write file and or verify"""
        try:
            binfile = open(file_name, 'rb')
        except:
            print("cannot open file!")
            return
        mem = list(binfile.read())
        size = len(mem)
        if size % 4:
            mem += [0] * (size % 4)
            size = len(mem)
        self.write_memory(self.FLASH_START, mem)
        if not verify:
            return
        addr = address
        mem_verify = self.read_memory(address, size)
        _errors = 0
        for data_a, data_b in zip(mem, mem_verify):
            if data_a != data_b:
                if _errors < 10:
                    print("error at: 0x%08x: 0x%02x != 0x%02x" % (addr, data_a, data_b))
                _errors += 1
            addr += 1
        if _errors >= 10:
            print(".. %d errors" % (_errors))
        print("writing&verify done - no errors")


