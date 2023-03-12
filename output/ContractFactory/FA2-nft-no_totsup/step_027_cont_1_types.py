import smartpy as sp

tstorage = sp.TRecord(last_sum = sp.TNat, operator_support = sp.TBool).layout(("last_sum", "operator_support"))
tparameter = sp.TVariant(receive_balances = sp.TList(sp.TRecord(balance = sp.TNat, request = sp.TRecord(owner = sp.TAddress, token_id = sp.TNat).layout(("owner", "token_id"))).layout(("request", "balance"))), reinit = sp.TUnit).layout(("receive_balances", "reinit"))
tprivates = { }
tviews = { }
