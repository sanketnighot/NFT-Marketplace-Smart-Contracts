import smartpy as sp

tstorage = sp.TRecord(contracts = sp.TBigMap(sp.TAddress, sp.TList(sp.TAddress))).layout("contracts")
tparameter = sp.TVariant(deploy_fa2 = sp.TBigMap(sp.TString, sp.TBytes), mint_token = sp.TRecord(amount = sp.TNat, contract = sp.TAddress, metadata = sp.TMap(sp.TString, sp.TBytes), token_id = sp.TNat).layout((("amount", "contract"), ("metadata", "token_id")))).layout(("deploy_fa2", "mint_token"))
tprivates = { }
tviews = { }
