from LabelStruct import LabelStruct
from AccessStruct import AccessStruct
import logging

class LabelLib(LabelStruct):
  
  op_jmp = 0x4ef9
  op_reset = 0x04e70
  op_rts = 0x4e75
  
  def __init__(self, name, addr, size, lib_base, struct):
    LabelStruct.__init__(self, name, addr, struct, size=size, offset=lib_base - addr)
    self.lib_base = lib_base
    
  def __str__(self):
    return "%s base=%06x" %(LabelStruct.__str__(self),self.lib_base)

  def trace_mem(self, mode, width, addr, val):
    # a possible trap?
    if mode == 'R' and addr < self.lib_base and width == 1:
      # is it trapped?
      if val == self.op_reset:
        delta = self.lib_base - addr
        off = delta / 6
        addon = "-%d [%d]" % (delta,off)
        self.trace_mem_int(mode, width, addr, val, text="TRAP", level=logging.INFO, addon=addon)
      # return to caller after trap
      elif val == self.op_rts:
        self.trace_mem_int(mode, width, addr, val, text="T_RTS")
      # native lib jump
      elif val == self.op_jmp:
        delta = self.lib_base - addr
        addon = "-%d" % delta
        self.trace_mem_int(mode, width, addr, val, text="JUMP", level=logging.INFO, addon=addon)
      # something strange
      else:
        self.trace_mem_int(mode, width, addr, val, text="LIB?!", level=logging.WARN)      
    else:
      # no use regular access
      LabelStruct.trace_mem(self, mode, width, addr, val)
    return True
