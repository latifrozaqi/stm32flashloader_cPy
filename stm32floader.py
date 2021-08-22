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
    def __init__(self, txpin=board.IO33, rxpin=board.IO34, baudrate=115200, verbosity=1, rst=board.IO16):
        self.uart = busio.UART(txpin,rxpin,baudrate=baudrate,parity=busio.UART.Parity.EVEN)
        self.reset_pin=digitalio.DigitalInOut(rst)
        self.reset_pin.direction=digitalio.Direction.OUTPUT
        self.reset_pin.value=True
        self._verbosity = verbosity
    def _reset_mcu(self):
        self.reset_pin.value=False
        time.sleep(0.1)
        self.reset_pin.value=True
    def _connect(self, repeat=1):
        """connect to boot-loader"""
        print("connecting to bootloader")
        self._reset_mcu()
        while repeat:
            self.uart.write(bytes([self.CMD_INIT]))
            r=self.uart.read()
            if self.check_ack(r):
                print("connected to bootloader")
                return 1
            repeat-=1
        print("Can't connect to MCU boot-loader.")
        return 0
    def check_ack(self,ack):
        if ack is not None:
            if b'\x79' in ack:
                return 1
        return 0
    def cmd_general(self,cmd):
        if isinstance(cmd, (tuple, list)):
            xor = cmd[0]
            for i in cmd[1:]:
                xor ^= i
            cmd.append(xor)
        else:
            cmd = [cmd, cmd ^ 0xff]
        self.uart.write(bytes(cmd))
        r=self.uart.read()
        return r
    def cmd_write_data(self,data):
        if isinstance(data, (tuple, list)):
            xor = data[0]
            for i in data[1:]:
                xor ^= i
            data.append(xor)
        else:
            data = [data, data ^ 0xff]
        self.uart.write(bytes(data))
        r=self.uart.read()
        return r
    def cmd_get(self):
        r=self.cmd_general(self.CMD_GET)
        if len(r):
            for i in r[3:]:
                try:
                    print(i,self.CMD[i])
                except:
                    print("error or no key: %d"%(i))
        return r
    def cmd_erase_glob(self):
        r=self.cmd_general(self.CMD_ERASE)
        if b'\x79' in r:
            print("erasing memory..")
            cmd=[255,0]
            self.uart.write(bytes(cmd))
            s=self.uart.read()
            if self.check_ack(s):
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
    ############# write flash #########
    def _cmd_write_memory(self, address, data):
        """Writes up to 256 bytes to the RAM or Flash memory
        starting from an address specified by the application"""
        #self.log("CMD_WRITE_MEMORY(%08x, %d)" % (address, len(data)), level=2)
        self.cmd_general(self.CMD_WRITE_MEMORY)
        self.cmd_write_data(self._convert_32bit(address))
        return self.cmd_write_data([len(data) - 1] + data)
    def write_memory(self, address, data):
        """write memory"""
        print("from 0x%08x (%d Bytes)" % (address, len(data)))
        _data = data[:]
        start_time=time.time()
        while _data:
            self._cmd_write_memory(address, _data[:256])
            address += 256
            _data = _data[256:]
            print("write succeed@addr: %d"%(address))
        print("done write memory in %s seconds"%(time.time()-start_time))
    def write_file(self, address, file_name):
        """Write file and or verify"""
        binfile = open(file_name, 'rb')
        mem = list(binfile.read())
        size = len(mem)
        if size % 4:
            mem += [0] * (size % 4)
            size = len(mem)
        self.write_memory(address, mem)
