from CPU import *

from Log import *
import logging
import time

class AmigaLibrary:
  
  def __init__(self, name, version, calls, struct, profile=False):
    self.name = name
    self.version = version
    self.calls = calls
    self.struct = struct
    self.profile = profile

    # get pos_size
    self.pos_size = struct.get_size()

    # calc neg_size
    last_call_bias = calls[-1][0]    
    self.neg_size = last_call_bias + 6
    self.num_jumps = self.neg_size / 6
        
    # setup jump_table: [call_tuple|None, PyFunc|None]
    self.jump_table = []
    call_id = 0
    off = 0
    for i in xrange(self.num_jumps):
      call = None
      cur_call = self.calls[call_id]
      if cur_call[0]==off:
        call = cur_call
        call_id += 1
      off += 6
      self.jump_table.append([call,None])
      
  
  def __str__(self):
    return "[Lib %s V%d num_jumps=%d pos_size=%d neg_size=%d]" % \
      (self.name, self.version, self.num_jumps, self.pos_size, self.neg_size)
  
  def setup_lib(self, mem_lib, ctx):
    # enable profiling
    if self.profile:
      self.profile_map = {}
  
  def finish_lib(self, mem_lib, ctx):
    # dump profile
    if self.profile:
      self.dump_profile()
  
  def get_num_vectors(self):
    return self.num_jumps
    
  def get_struct(self):
    return self.struct
  
  def get_name(self):
    return self.name
    
  def get_version(self):
    return self.version
  
  def get_total_size(self):
    return self.neg_size + self.pos_size
  
  def get_neg_size(self):
    return self.neg_size
    
  def get_pos_size(self):
    return self.pos_size
  
  def set_funcs(self, funcs):
    for f in funcs:
      self.set_func(*f)

  def set_func(self, key, callee):
    off = key / 6
    self.set_by_offset(off, callee)
    
  def set_by_offset(self, off, callee, name="none", param=None, ret=REG_D0):
    self.jump_table[off][1] = callee

  def log(self, text, level=logging.INFO):
    log_lib.log(level, "[%16s]  %s", self.name, text)

  def dump_profile(self):
    log_prof.info("'%s' Function Call Profile", self.name)
    funcs = sorted(self.profile_map.keys())
    sum_total = 0.0
    for f in funcs:
      entry = self.profile_map[f]
      cnt = entry[1]
      total = entry[0]
      per_call = total / cnt
      log_prof.info("  %20s: #%8d  total=%10.4f  per call=%10.4f", f, cnt, total, per_call)
      sum_total += total
    log_prof.info("sum total=%.4f",sum_total)

  def _do_profile(self, func, delta):
    if self.profile_map.has_key(func):
      entry = self.profile_map[func]
      entry[0] += delta
      entry[1] += 1
    else:
      entry = [delta, 1]
      self.profile_map[func] = entry

  def call_vector(self, off, mem_lib, ctx):
    jump_entry = self.jump_table[off]
    call = jump_entry[0]
    callee = jump_entry[1]
    callee_pc = self.get_callee_pc(ctx)
    call_name = "%4d %s( %s ) from PC=%06x" % (call[0], call[1], self.gen_arg_dump(call[2], ctx), callee_pc)
    if callee != None:
      # we have a function
      self.log("{ CALL: " + call_name)
      start_time = time.clock()
      # call the lib!
      d0 = callee(mem_lib, ctx)
      end_time = time.clock()
      delta = end_time - start_time
      # do profiling?
      if self.profile:
        self._do_profile(call[1], delta)
      # handle return value
      if d0 != None:
        self.log("} END CALL: d0=%08x (duration: %g ms)" % (d0, (delta * 1000.0)))
        ctx.cpu.w_reg(REG_D0, d0)
      else:
        self.log("} END CALL: NO RET (duration: %g ms)" % ((delta * 1000.0)))
    else:
      # function not implemented yet
      self.log("? CALL: %s -> d0=0 (default)" % call_name, level=logging.WARN)
      ctx.cpu.w_reg(REG_D0, 0)

  def call_vector_fast(self, off, mem_lib, ctx):
    """fast call does no logging"""
    jump_entry = self.jump_table[off]
    call = jump_entry[0]
    callee = jump_entry[1]
    if callee != None:
      # we have a function
      start_time = time.clock()
      # call the lib!
      d0 = callee(mem_lib, ctx)
      end_time = time.clock()
      delta = end_time - start_time
      # do profiling?
      if self.profile:
        self._do_profile(call[1], delta)
      # handle return value
      if d0 != None:
        ctx.cpu.w_reg(REG_D0, d0)
    else:
      ctx.cpu.w_reg(REG_D0, 0)
    
  def get_callee_pc(self,ctx):
    sp = ctx.cpu.r_reg(REG_A7)
    return ctx.mem.read_mem(2,sp)
    
  def gen_arg_dump(self,args,ctx):
    if args == None:
      return ""
    result = []
    for a in args:
      name = a[0]
      reg = a[1]
      reg_num = int(reg[1])
      if reg[0] == 'a':
        reg_num += 8
      val = ctx.cpu.r_reg(reg_num)
      result.append("%s[%s]=%x" % (name,reg,val))
    return ", ".join(result)
