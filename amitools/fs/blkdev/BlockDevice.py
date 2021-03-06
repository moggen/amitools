# a block device defines a set of blocks used by a file system

class BlockDevice:
  def __init__(self, read_only=False):
    self.read_only = read_only
  
  def _set_geometry(self, first_cyl=0, last_cyl=79, heads=2, sectors=11, block_bytes=512, reserved=2):
    self.first_cyl = first_cyl
    self.last_cyl = last_cyl
    self.heads = heads
    self.sectors = sectors
    self.block_bytes = block_bytes
    self.reserved = reserved
    # derived values
    self.num_cyl = self.last_cyl - self.first_cyl + 1
    self.num_tracks = self.num_cyl * self.heads
    self.num_blocks = self.num_tracks * self.sectors
    self.num_bytes = self.num_blocks * self.block_bytes
    self.block_longs = self.block_bytes / 4
    self.num_longs = self.num_blocks * self.block_longs
  
  def dump(self):
    print "first_cyl:  ",self.first_cyl
    print "last_cyl:   ",self.last_cyl
    print "heads:      ",self.heads
    print "sectors:    ",self.sectors
    print "block_nytes:",self.block_bytes
    print "reserved:   ",self.reserved
  
  def _blk_to_offset(self, blk_num):
    return self.block_bytes * blk_num
  
  # ----- API -----
  def create(self):
    pass
  def open(self):
    pass
  def close(self):
    pass
  def flush(self):
    pass
  def read_block(self, blk_num):
    pass
  def write_block(self, blk_num, data):
    pass
