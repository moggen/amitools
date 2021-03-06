from ProtectFlags import *
from TimeStamp import *

class MetaInfo:
  def __init__(self, protect=None, mod_ts=None, comment=None):
    self.set_protect(protect)
    self.set_mod_ts(mod_ts)
    self.set_comment(comment)
  
  def __str__(self):
    res = []
    res.append(self.get_protect_str())
    res.append(self.get_time_str())
    res.append(self.get_comment_str())
    return "  ".join(res)
    
  def get_time_str(self):
    if self.mod_ts != None:
      return str(self.mod_ts)
    else:
      return ts_empty_string
      
  def get_protect_str(self):
    if self.protect_flags != None:
      return str(self.protect_flags)
    else:
      return ProtectFlags.empty_string
      
  def get_comment_str(self):
    if self.comment != None:
      return self.comment
    else:
      return ""
  
  def set_protect(self, protect):
    self.protect = protect
    if self.protect != None:
      self.protect_flags = ProtectFlags(protect)
    else:
      self.protect_flags = None
  
  def set_default_protect(self):
    self.protect = 0
    self.protect_flags = ProtectFlags(self.protect)
  
  def set_current_time(self):
    mod_time = time.mktime(time.localtime())
    self.set_mod_time(mod_time)
    
  def set_mod_time(self, mod_time):
    self.mod_time = mod_time
    if self.mod_time != None:
      self.mod_ts = TimeStamp()
      self.mod_ts.from_secs(mod_time)
    else:
      self.mod_ts = None
  
  def set_mod_ts(self, mod_ts):
    self.mod_ts = mod_ts
    if self.mod_ts != None:
      self.mod_time = self.mod_ts.get_secsf()
    else:
      self.mod_time = None
  
  def set_comment(self, comment):
    self.comment = comment
  
  def get_protect(self):
    return self.protect
  
  def get_protect_flags(self):
    return self.protect_flags
  
  def get_mod_time(self):
    return self.mod_time

  def get_mod_ts(self):
    return self.mod_ts
  
  def get_comment(self):
    return self.comment

