# Write your code here :-)
from stm32floader import stm32bl

stm32=stm32bl()
r=stm32._connect(5)
if not r:
    print("aborted: cannot connect")
else:
    stm32.cmd_get()
    stm32.cmd_erase_glob()
    #stm32.cmd_write_only('STM32UARTHS.bin')
