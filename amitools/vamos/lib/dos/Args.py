import types
from Error import *

class Args:

  def __init__(self):
    self.targs = None
    self.in_val = None
    self.result = None

  def parse_template(self, template):
    """generate an internal representation of an AmigaDOS ReadArgs compatible arg parse template
    """
    self.targs = []
    ps = template.split(',')
    for p in ps:
      flags = p.split('/')
      keys = map(lambda x : x.lower(), flags[0].split('='))
      targ = { 'keys' : keys,
               's' : False, 'k' : False, 'n' : False, 't' : False, 
               'a' : False, 'f' : False, 'm' : False, 'n' : False }

      # get keys
      for flag in flags[1:]:
        flag = flag.lower()[0]
        if targ.has_key(flag):
          targ[flag] = True

      # n = normal switch = not s,t,k,f
      targ['n'] = not (targ['s'] or targ['t'] or targ['k'] or targ['f'])

      self.targs.append(targ)

  def prepare_input(self,mem_access,ptr):
    # read org values
    self.in_val = []
    for t in self.targs:
      raw = mem_access.read_mem(2,ptr)
      # prefill toggle
      if t['t']:
        self.in_val.append(bool(raw))
      else:
        self.in_val.append(None)
      ptr += 4

  def _find_remove_key(self, keys, in_list, extra):
    n = len(in_list)
    for key in keys:
      pos = 0
      for i in in_list:
        if i.lower() == key:
          break
        pos = pos + 1
      if pos != n:
        in_list.pop(pos)
        # extra arg?
        if extra:
          # last one? -> failed to get extra arg
          if pos == n-1:
            return None
          val = in_list[pos]
          in_list.pop(pos)
          return val
        else:
          return True
    return False

  """apply an internal template to a given argument array
  """
  def parse_string(self, in_args):
    self.error = NO_ERROR
    
    # get args and split = into args, too
    args = []
    for a in in_args:
      b = a.split('=')
      args += b
  
    # prepare result array
    result = []
    targs = self.targs
    while len(result) < len(targs):
      result.append(None)
  
    # scan through args and look for keyword named entries
    pos = 0
    for targ in targs:
      req = targ['a']
      
      # switch
      if targ['s']:
        val = self._find_remove_key(targ['keys'], args, False)
        if val:
          result[pos] = True
        else:
          result[pos] = False
          if req:
            self.error = ERROR_REQUIRED_ARG_MISSING
            return False # sensible? switch with a ??
      
      # toggle
      elif targ['t']:
        val = self._find_remove_key(targ['keys'], args, False)
        if val:
          result[pos] = not result[pos]
        elif req:
          self.error = ERROR_REQUIRED_ARG_MISSING
          return False
          
      # keyword
      elif targ['k']:
        val = self._find_remove_key(targ['keys'], args, True)
        # keyword at end of line
        if val == None:
          self.error = ERROR_REQUIRED_ARG_MISSING
          return False
        else:
          # found a real value
          if val != False:
            if targ['n']:
              val = int(val)
            result[pos] = val
          # keyword not found
          else:
            if req:
              self.error = ERROR_REQUIRED_ARG_MISSING
              return False
            
      # full line
      elif targ['f']:
        result[pos] = args
        args = []
        
      pos = pos + 1
    
    # scan for multi and non-key args
    multi_pos = None
    multi_targ = None
    pos = 0
    for targ in targs:  
      # multi 
      if targ['m']:
        multi_pos = pos
        multi_targ = targ
        result[pos] = args
        args = []
        # multi arg required
        if targ['a'] and len(result[pos])==0:
          self.error = ERROR_REQUIRED_ARG_MISSING
          return False
          
      # normal entry
      elif targ['n']:
        # take from arraay
        if len(args)>0:
          val = args[0]
          del args[0]
        # no more value in arg
        else:
          val = None
          if targ['a']: # required -> try to get from multi
            if multi_pos != None and len(result[multi_pos])>0:
              val = result[multi_pos][-1]
              result[multi_pos] = result[multi_pos][:-1]
              # oops multi is empty!
              if multi_targ['a'] and len(result[multi_pos])==0:
                self.error = ERROR_REQUIRED_ARG_MISSING
                return False
            else: # failed!
              self.error = ERROR_REQUIRED_ARG_MISSING
              return False
        result[pos] = val
        
      pos = pos + 1
  
    # something left?
    if len(args)>0:
      self.error = ERROR_TOO_MANY_ARGS
      return False
  
    self.result = result
    return True

  def calc_result_size(self):
    n = len(self.result)
    num_longs = 0
    num_chars = 0
    for i in xrange(n):
      r = self.result[i]
      if r == None: # null pointer
        pass
      elif type(r) is types.StringType: # string key 'k'
        num_chars += len(r) + 1
      elif type(r) is types.IntType: # numerical key 'kn'
        num_longs += 1
      elif type(r) is types.ListType: # string list 'm'
        num_longs += len(r) + 1
        for s in r:
          num_chars += len(s) + 1
    
    # calc total size
    size = num_longs * 4 + num_chars

    self.num_longs = num_longs
    self.num_chars = num_chars
    self.size = size
    return size

  def generate_result(self,mem_access,addr,array_ptr):
    n = len(self.result)
    char_ptr = addr + self.num_longs * 4
    long_ptr = addr
    base_ptr = array_ptr
    for i in xrange(n):
      r = self.result[i]
      if r == None: # optional value not set ('k')
        base_val = 0
      elif type(r) is types.StringType:
        # pointer to string
        base_val = char_ptr
        # append string
        mem_access.w_cstr(char_ptr, r)
        char_ptr += len(r) + 1        
      elif type(r) is types.IntType:
        # pointer to long
        base_val = long_ptr
        # write long
        mem_access.w32(long_ptr,r)
        long_ptr += 4
      elif type(r) is types.ListType:
        # pointer to array
        base_val = long_ptr
        # array with longs + strs
        for s in r:
          mem_access.w32(long_ptr,char_ptr)
          mem_access.w_cstr(char_ptr,s)
          long_ptr += 4
          char_ptr += len(s) + 1
        mem_access.w32(long_ptr,0)
        long_ptr += 4
      else:
        # direct value
        base_val = r
      
      mem_access.w32(base_ptr,base_val)
      base_ptr += 4
    