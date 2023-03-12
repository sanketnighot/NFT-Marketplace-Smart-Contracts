import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init_type(sp.TRecord(last_sum = sp.TNat, operator_support = sp.TBool).layout(("last_sum", "operator_support")))
    self.init(last_sum = 0,
              operator_support = False)

  @sp.entry_point
  def receive_balances(self, params):
    sp.set_type(params, sp.TList(sp.TRecord(balance = sp.TNat, request = sp.TRecord(owner = sp.TAddress, token_id = sp.TNat).layout(("owner", "token_id"))).layout(("request", "balance"))))
    self.data.last_sum = 0
    sp.for resp in params:
      self.data.last_sum += resp.balance

  @sp.entry_point
  def reinit(self):
    self.data.last_sum = 0

sp.add_compilation_target("test", Contract())