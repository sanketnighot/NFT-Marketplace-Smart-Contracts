import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init_type(sp.TRecord(contracts = sp.TBigMap(sp.TAddress, sp.TList(sp.TAddress))).layout("contracts"))
    self.init(contracts = {})

  @sp.entry_point
  def deploy_fa2(self, params):
    create_contract_ContractFactory_43 = sp.local("create_contract_ContractFactory_43", create contract ...)
    sp.operations().push(create_contract_ContractFactory_43.value.operation)
    sp.if self.data.contracts.contains(sp.sender):
      self.data.contracts[sp.sender].push(create_contract_ContractFactory_43.value.address)
    sp.else:
      self.data.contracts[sp.sender] = sp.list([create_contract_ContractFactory_43.value.address])
    sp.emit(sp.record(contract_address = create_contract_ContractFactory_43.value.address, deployed_by = sp.sender, event = 'CONTRACT_DEPLOYED'), tag = "CONTRACT_DEPLOYED")

  @sp.entry_point
  def mint_token(self, params):
    sp.set_type(params.contract, sp.TAddress)
    sp.set_type(params.amount, sp.TNat)
    sp.set_type(params.token_id, sp.TNat)
    sp.set_type(params.metadata, sp.TMap(sp.TString, sp.TBytes))
    sp.for addr in self.data.contracts[sp.sender]:
      sp.if addr == params.contract:
        sp.transfer(sp.record(address = sp.sender, amount = params.amount, metadata = params.metadata, token_id = params.token_id), sp.tez(0), sp.contract(sp.TRecord(address = sp.TAddress, amount = sp.TNat, metadata = sp.TMap(sp.TString, sp.TBytes), token_id = sp.TNat).layout((("address", "amount"), ("metadata", "token_id"))), params.contract, entry_point='mint').open_some())
        sp.emit(sp.record(amount = params.amount, event = 'TOKEN_MINTED', minted_by = sp.sender), tag = "TOKEN_MINTED")

sp.add_compilation_target("test", Contract())