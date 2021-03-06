import struct
import ctypes
from ..TimeStamp import TimeStamp

class Block:
  
  # block types
  T_SHORT = 2
  T_DATA = 8
  T_LIST = 16
  # block sub types
  ST_ROOT = 1
  ST_USERDIR = 2
  ST_FILE = -3 & 0xffffffff
  
  def __init__(self, blkdev, blk_num, is_type=0, is_sub_type=0, chk_loc=5):
    self.valid = False
    self.blkdev = blkdev
    self.blk_num = blk_num
    self.block_longs = blkdev.block_longs
    self.type = 0
    self.sub_type = 0
    self.data = None
    self.is_type = is_type
    self.is_sub_type = is_sub_type
    self.chk_loc = chk_loc
  
  def create(self):
    self.type = self.is_type
    self.sub_type = self.is_sub_type
  
  def read(self):
    self._read_data()
    self._get_types()
    self._get_chksum()
    self.valid = self.valid_types and self.valid_chksum
    
  def write(self):
    if self.data == None:
      self._create_data()
    self._put_types()
    self._put_chksum()
    self._write_data()
  
  def _set_data(self, data):
    self.data = data
  
  def _read_data(self):
    data = self.blkdev.read_block(self.blk_num)
    if len(data) != self.blkdev.block_bytes:
      raise ValueError("Invalid Block Data: size=%d but expected %d" % (len(data), self.blkdev.block_bytes))
    self._create_data()
    self.data[:] = data
  
  def _write_data(self):
    if self.data != None:
      self.blkdev.write_block(self.blk_num, self.data)
  
  def _free_data(self):
    self.data = None
  
  def _create_data(self):
    num_bytes = self.blkdev.block_bytes
    self.data = ctypes.create_string_buffer(num_bytes)
  
  def _put_long(self, num, val):
    if num < 0:
      num = self.block_longs + num
    struct.pack_into(">I",self.data,num*4,val)
  
  def _get_long(self, num):
    if num < 0:
      num = self.block_longs + num
    return struct.unpack_from(">I",self.data,num*4)[0]

  def _get_types(self):
    self.type = self._get_long(0)
    self.sub_type = self._get_long(-1)
    self.valid_types = True
    if self.is_type != 0:
      if self.type != self.is_type:
        self.valid_types = False
    if self.is_sub_type != 0:
      if self.sub_type != self.is_sub_type:
        self.valid_types = False
  
  def _put_types(self):
    if self.is_type != 0:
      self._put_long(0, self.is_type)
    if self.is_sub_type != 0:
      self._put_long(-1, self.is_sub_type)
  
  def _get_chksum(self):
    self.got_chksum = self._get_long(self.chk_loc)
    self.calc_chksum = self._calc_chksum()
    self.valid_chksum = self.got_chksum == self.calc_chksum
  
  def _put_chksum(self):
    self.calc_chksum = self._calc_chksum()
    self.got_chksum = self.calc_chksum
    self.valid_chksum = True
    self._put_long(self.chk_loc, self.calc_chksum)
  
  def _calc_chksum(self):
    chksum = 0
    for i in xrange(self.block_longs):
      if i != self.chk_loc:
        chksum += self._get_long(i)
    return (-chksum) & 0xffffffff
  
  def _get_timestamp(self, loc):
    days = self._get_long(loc)
    mins = self._get_long(loc+1)
    ticks = self._get_long(loc+2)
    return TimeStamp(days, mins, ticks)
  
  def _put_timestamp(self, loc, ts):
    self._put_long(loc, ts.days)
    self._put_long(loc+1, ts.mins)
    self._put_long(loc+2, ts.ticks)
  
  def _get_bstr(self, loc, max_size):
    if loc < 0:
      loc = self.block_longs + loc
    loc = loc * 4
    size = ord(self.data[loc])
    if size > max_size:
      return None
    if size == 0:
      return ""
    name = self.data[loc+1:loc+1+size]
    return name
  
  def _put_bstr(self, loc, max_size, bstr):
    if bstr == None:
      bstr = ""
    n = len(bstr)
    if n > max_size:
      bstr = bstr[:max_size]
    if loc < 0:
      loc = self.block_longs + loc
    loc = loc * 4
    self.data[loc] = chr(len(bstr))
    if len(bstr) > 0:
      self.data[loc+1:loc+1+len(bstr)] = bstr
  
  def dump(self, name):
    print "%sBlock(%d):" % (name, self.blk_num)
    print " types:     %x/%x (valid: %x/%x)" % (self.type, self.sub_type, self.is_type, self.is_sub_type)
    print " chksum:    0x%08x (got) 0x%08x (calc)" % (self.got_chksum, self.calc_chksum)
    print " valid:     %s" % self.valid
    