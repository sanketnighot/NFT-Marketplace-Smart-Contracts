import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init_type(sp.TRecord(administrator = sp.TAddress, all_tokens = sp.TNat, ledger = sp.TBigMap(sp.TPair(sp.TAddress, sp.TNat), sp.TRecord(balance = sp.TNat).layout("balance")), metadata = sp.TBigMap(sp.TString, sp.TBytes), operators = sp.TBigMap(sp.TRecord(operator = sp.TAddress, owner = sp.TAddress, token_id = sp.TNat).layout(("owner", ("operator", "token_id"))), sp.TUnit), paused = sp.TBool, token_metadata = sp.TBigMap(sp.TNat, sp.TRecord(token_id = sp.TNat, token_info = sp.TMap(sp.TString, sp.TBytes)).layout(("token_id", "token_info")))).layout((("administrator", ("all_tokens", "ledger")), (("metadata", "operators"), ("paused", "token_metadata")))))
    self.init(administrator = sp.address('tz1hdQscorfqMzFqYxnrApuS5i6QSTuoAp3w'),
              all_tokens = 0,
              ledger = {},
              metadata = {'' : sp.bytes('0x68747470733a2f2f6578616d706c652e636f6d')},
              operators = {},
              paused = False,
              token_metadata = {})

  @sp.entry_point
  def balance_of(self, params):
    sp.verify(~ self.data.paused, 'FA2_PAUSED')
    sp.set_type(params, sp.TRecord(callback = sp.TContract(sp.TList(sp.TRecord(balance = sp.TNat, request = sp.TRecord(owner = sp.TAddress, token_id = sp.TNat).layout(("owner", "token_id"))).layout(("request", "balance")))), requests = sp.TList(sp.TRecord(owner = sp.TAddress, token_id = sp.TNat).layout(("owner", "token_id")))).layout(("requests", "callback")))
    def f_x0(_x0):
      sp.verify(self.data.token_metadata.contains(_x0.token_id), 'FA2_TOKEN_UNDEFINED')
      sp.if self.data.ledger.contains((sp.set_type_expr(_x0.owner, sp.TAddress), sp.set_type_expr(_x0.token_id, sp.TNat))):
        sp.result(sp.record(request = sp.record(owner = sp.set_type_expr(_x0.owner, sp.TAddress), token_id = sp.set_type_expr(_x0.token_id, sp.TNat)), balance = self.data.ledger[(sp.set_type_expr(_x0.owner, sp.TAddress), sp.set_type_expr(_x0.token_id, sp.TNat))].balance))
      sp.else:
        sp.result(sp.record(request = sp.record(owner = sp.set_type_expr(_x0.owner, sp.TAddress), token_id = sp.set_type_expr(_x0.token_id, sp.TNat)), balance = 0))
    responses = sp.local("responses", params.requests.map(sp.build_lambda(f_x0)))
    sp.transfer(responses.value, sp.tez(0), sp.set_type_expr(params.callback, sp.TContract(sp.TList(sp.TRecord(balance = sp.TNat, request = sp.TRecord(owner = sp.TAddress, token_id = sp.TNat).layout(("owner", "token_id"))).layout(("request", "balance"))))))

  @sp.entry_point
  def mint(self, params):
    sp.verify(~ (params.token_id < self.data.all_tokens), 'NFT-asset: cannot mint twice same token')
    sp.if self.data.ledger.contains((sp.set_type_expr(params.address, sp.TAddress), sp.set_type_expr(params.token_id, sp.TNat))):
      self.data.ledger[(sp.set_type_expr(params.address, sp.TAddress), sp.set_type_expr(params.token_id, sp.TNat))].balance += params.amount
    sp.else:
      self.data.ledger[(sp.set_type_expr(params.address, sp.TAddress), sp.set_type_expr(params.token_id, sp.TNat))] = sp.record(balance = params.amount)
    sp.if ~ (params.token_id < self.data.all_tokens):
      sp.verify(self.data.all_tokens == params.token_id, 'Token-IDs should be consecutive')
      self.data.all_tokens = params.token_id + 1
      self.data.token_metadata[params.token_id] = sp.record(token_id = params.token_id, token_info = params.metadata)

  @sp.entry_point
  def set_administrator(self, params):
    sp.verify(sp.sender == self.data.administrator, 'FA2_NOT_ADMIN')
    self.data.administrator = params

  @sp.entry_point
  def set_metadata(self, params):
    sp.verify(sp.sender == self.data.administrator, 'FA2_NOT_ADMIN')
    self.data.metadata[params.k] = params.v

  @sp.entry_point
  def set_pause(self, params):
    sp.verify(sp.sender == self.data.administrator, 'FA2_NOT_ADMIN')
    self.data.paused = params

  @sp.entry_point
  def transfer(self, params):
    sp.verify(~ self.data.paused, 'FA2_PAUSED')
    sp.set_type(params, sp.TList(sp.TRecord(from_ = sp.TAddress, txs = sp.TList(sp.TRecord(amount = sp.TNat, to_ = sp.TAddress, token_id = sp.TNat).layout(("to_", ("token_id", "amount"))))).layout(("from_", "txs"))))
    sp.for transfer in params:
      sp.for tx in transfer.txs:
        sp.verify(((sp.sender == self.data.administrator) | (transfer.from_ == sp.sender)) | (self.data.operators.contains(sp.set_type_expr(sp.record(owner = transfer.from_, operator = sp.sender, token_id = tx.token_id), sp.TRecord(operator = sp.TAddress, owner = sp.TAddress, token_id = sp.TNat).layout(("owner", ("operator", "token_id")))))), 'FA2_NOT_OPERATOR')
        sp.verify(self.data.token_metadata.contains(tx.token_id), 'FA2_TOKEN_UNDEFINED')
        sp.if tx.amount > 0:
          sp.verify(self.data.ledger[(sp.set_type_expr(transfer.from_, sp.TAddress), sp.set_type_expr(tx.token_id, sp.TNat))].balance >= tx.amount, 'FA2_INSUFFICIENT_BALANCE')
          self.data.ledger[(sp.set_type_expr(transfer.from_, sp.TAddress), sp.set_type_expr(tx.token_id, sp.TNat))].balance = sp.as_nat(self.data.ledger[(sp.set_type_expr(transfer.from_, sp.TAddress), sp.set_type_expr(tx.token_id, sp.TNat))].balance - tx.amount)
          sp.if self.data.ledger.contains((sp.set_type_expr(tx.to_, sp.TAddress), sp.set_type_expr(tx.token_id, sp.TNat))):
            self.data.ledger[(sp.set_type_expr(tx.to_, sp.TAddress), sp.set_type_expr(tx.token_id, sp.TNat))].balance += tx.amount
          sp.else:
            self.data.ledger[(sp.set_type_expr(tx.to_, sp.TAddress), sp.set_type_expr(tx.token_id, sp.TNat))] = sp.record(balance = tx.amount)

  @sp.entry_point
  def update_operators(self, params):
    sp.set_type(params, sp.TList(sp.TVariant(add_operator = sp.TRecord(operator = sp.TAddress, owner = sp.TAddress, token_id = sp.TNat).layout(("owner", ("operator", "token_id"))), remove_operator = sp.TRecord(operator = sp.TAddress, owner = sp.TAddress, token_id = sp.TNat).layout(("owner", ("operator", "token_id")))).layout(("add_operator", "remove_operator"))))
    sp.for update in params:
      with update.match_cases() as arg:
        with arg.match('add_operator') as add_operator:
          sp.verify((add_operator.owner == sp.sender) | (sp.sender == self.data.administrator), 'FA2_NOT_ADMIN_OR_OPERATOR')
          self.data.operators[sp.set_type_expr(sp.record(owner = add_operator.owner, operator = add_operator.operator, token_id = add_operator.token_id), sp.TRecord(operator = sp.TAddress, owner = sp.TAddress, token_id = sp.TNat).layout(("owner", ("operator", "token_id"))))] = sp.unit
        with arg.match('remove_operator') as remove_operator:
          sp.verify((remove_operator.owner == sp.sender) | (sp.sender == self.data.administrator), 'FA2_NOT_ADMIN_OR_OPERATOR')
          del self.data.operators[sp.set_type_expr(sp.record(owner = remove_operator.owner, operator = remove_operator.operator, token_id = remove_operator.token_id), sp.TRecord(operator = sp.TAddress, owner = sp.TAddress, token_id = sp.TNat).layout(("owner", ("operator", "token_id"))))]


sp.add_compilation_target("test", Contract())