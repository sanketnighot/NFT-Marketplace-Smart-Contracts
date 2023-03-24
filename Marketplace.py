import smartpy as sp


class Ask:
    type_value = sp.TRecord(
        creator = sp.TAddress,
        token = sp.TRecord(
            address = sp.TAddress,
            token_id = sp.TNat
        ),
        amount = sp.TMutez,
        editions = sp.TNat,
        expiry_time = sp.TOption(sp.TTimestamp)
    )

    def set_type(): return sp.big_map(l = {}, tkey = sp.TNat, tvalue = Ask.type_value)
    
    def set_value(_params):
        return sp.record(
            creator = _params.creator,
            token = _params.token,
            amount = _params.amount,
            editions = _params.editions,
            expiry_time = _params.expiry_time
        )
    
class Offer:
    type_value = sp.TRecord(
        creator = sp.TAddress,
        token = sp.TRecord(
            address = sp.TAddress,
            token_id = sp.TNat
        ),
        amount = sp.TMutez,
        expiry_time = sp.TOption(sp.TTimestamp)
    )
    
    def set_type(): return sp.big_map(l = {}, tkey = sp.TNat, tvalue = Offer.type_value)

    def set_value(_params):
        return sp.record(
            creator = _params.creator,
            token = _params.token,
            amount = _params.amount,
            expiry_time = _params.expiry_time
        )

class Batch_transfer:
    def get_transfer_type():
        tx_type = sp.TRecord(to_=sp.TAddress,
                             token_id=sp.TNat,
                             amount=sp.TNat)
        transfer_type = sp.TRecord(from_=sp.TAddress,
                                   txs=sp.TList(tx_type)).layout(
                                       ("from_", "txs"))
        return transfer_type

    def get_type():
        return sp.TList(Batch_transfer.get_transfer_type())

    def item(from_, txs):
        v = sp.record(from_=from_, txs=txs)
        return sp.set_type_expr(v, Batch_transfer.get_transfer_type())
    
class Marketplace(sp.Contract):
    def __init__(self, _mod):
        self.init(
            # metadata = metadata,
            mods = sp.set([_mod]),
            next_ask_id = sp.nat(0),
            asks = Ask.set_type(),
            next_offer_id = sp.nat(0),
            offers = Offer.set_type(),
            pause = sp.bool(False)
        )

    def transfer_token(self, contract, params_):
        sp.set_type(contract, sp.TAddress)
        sp.set_type(params_, sp.TList(
                sp.TRecord(
                    from_ = sp.TAddress, 
                    txs = sp.TList(
                        sp.TRecord(
                            amount = sp.TNat, 
                            to_ = sp.TAddress, 
                            token_id = sp.TNat
                        ).layout(("to_", ("token_id", "amount")))
                    )
                )
            .layout(("from_", "txs"))))
        contractParams = sp.contract(sp.TList(
                sp.TRecord(
                    from_ = sp.TAddress, 
                    txs = sp.TList(
                        sp.TRecord(
                            amount = sp.TNat, 
                            to_ = sp.TAddress, 
                            token_id = sp.TNat
                        ).layout(("to_", ("token_id", "amount")))
                    )
                )
            .layout(("from_", "txs"))), contract, entry_point="transfer").open_some()
        sp.transfer(params_, sp.mutez(0), contractParams)
        sp.emit(sp.record(event="TOKEN_TRANSFERED",transfered_by=sp.sender),tag="TOKEN_TRANSFERED")
    
    @sp.entry_point
    def add_moderator(self, _moderator):
        sp.set_type(_moderator, sp.TAddress)
        sp.verify(self.data.mods.contains(sp.sender), "NOT_MODERATOR")
        self.data.mods.add(_moderator)
        sp.emit(sp.record(moderator=_moderator),tag="MODERATOR_ADDED")
        
    @sp.entry_point
    def remove_moderator(self, _moderator):
        sp.set_type(_moderator, sp.TAddress)
        sp.verify(self.data.mods.contains(sp.sender), "NOT_MODERATOR")
        sp.verify(self.data.mods.contains(_moderator), "ADDRESS_NAT_MODERATOR")
        self.data.mods.remove(_moderator)
        sp.emit(sp.record(moderator=_moderator),tag="MODERATOR_REMOVED")
        
    @sp.entry_point
    def offer(self, params):
        sp.set_type(params, Offer.type_value)
        sp.verify(sp.amount == params.amount, "INVALID_AMOUNT")
        self.data.offers[self.data.next_offer_id] = Offer.set_value(params)
        self.data.next_offer_id += 1
        sp.emit(sp.record(creator=params.creator,token=params.token),tag="OFFER_CREATED")
    
    @sp.entry_point
    def fulfill_offer(self, offer_id):
        sp.set_type(offer_id, sp.TNat)
        sp.verify(self.data.offers.contains(offer_id), "INVALID_OFFER_ID")
        sp.send(sp.sender, self.data.offers[offer_id].amount)
        _params = [
                Batch_transfer.item(from_=sp.sender,
                                       txs=[
                                           sp.record(to_=self.data.offers[offer_id].creator,
                                                     amount=1,
                                                     token_id=self.data.offers[offer_id].token.token_id)
                                       ])
            ]
        self.transfer_token(self.data.offers[offer_id].token.address, _params)
        del self.data.offers[offer_id]
        sp.emit(sp.record(offer_id=offer_id),tag="OFFER_FULFILLED")

    @sp.entry_point
    def retract_offer(self, offer_id):
        sp.set_type(offer_id, sp.TNat)
        sp.verify(self.data.offers.contains(offer_id), "INVALID_OFFER_ID")
        sp.verify(self.data.offers[offer_id].creator == sp.sender, "INVALID_CREATOR")
        sp.send(sp.sender, self.data.offers[offer_id].amount)
        del self.data.offers[offer_id]
        sp.emit(sp.record(offer_id=offer_id),tag="OFFER_RETRACTED")

    @sp.entry_point
    def ask(self, params):
        sp.set_type(params, Ask.type_value)
        #TODO: Verify if the sender is owner of nft
        self.data.asks[self.data.next_ask_id] = Ask.set_value(params)
        self.data.next_ask_id += 1
        sp.emit(sp.record(creator=params.creator,token=params.token),tag="ASK_CREATED")

    @sp.entry_point
    def fulfill_ask(self, ask_id):
        sp.set_type(ask_id, sp.TNat)
        sp.verify(self.data.asks.contains(ask_id), "INVALID_ASK_ID")
        sp.verify(sp.amount == self.data.asks[ask_id].amount, "INVALID_AMOUNT")
        sp.send(self.data.asks[ask_id].creator, sp.amount)
        _params = [
                Batch_transfer.item(from_=self.data.asks[ask_id].creator,
                                       txs=[
                                           sp.record(to_=sp.sender,
                                                     amount=1,
                                                     token_id=self.data.asks[ask_id].token.token_id)
                                       ])
            ]
        self.transfer_token(self.data.asks[ask_id].token.address, _params)
        del self.data.asks[ask_id]
        sp.emit(sp.record(ask_id=ask_id),tag="ASK_FULFILLED")

    @sp.entry_point
    def retract_ask(self, ask_id):
        sp.set_type(ask_id, sp.TNat)
        sp.verify(self.data.asks.contains(ask_id), "INVALID_ASK_ID")
        sp.verify(self.data.asks[ask_id].creator == sp.sender, "INVALID_CREATOR")
        del self.data.asks[ask_id]
        sp.emit(sp.record(ask_id=ask_id),tag="ASK_RETRACTED")
    
    @sp.entry_point
    def toggle_pause(self):
        sp.verify(self.data.mods.contains(sp.sender), "NOT_MODERATOR")
        self.data.pause = ~self.data.pause



@sp.add_test(name="Marketplace")
def test():
    sc = sp.test_scenario()
    sc.h1("Quilt NFT Collection Marketplace")
    sc.table_of_contents()
    admin = sp.test_account("Admin")
    alice = sp.test_account("Alice")
    bob = sp.test_account("Bob")
    elon = sp.test_account("Elon")
    mark = sp.test_account("Mark")
    sc.show([admin, alice, bob, mark, elon, ])
    mp = Marketplace(admin.address)
    
    sc.h1("Code")
    sc += mp
    sc.h1("Add/Remove Moderator")
    sc += mp.add_moderator(alice.address).run(sender = admin.address)
    sc += mp.remove_moderator(alice.address).run(sender = admin.address)
    
    sc.h1("Create Offer")
    offer_data = sp.record(
        creator = alice.address,
        token = sp.record(
            address = sp.address("KT1TezoooozzSmartPyzzDYNAMiCzzpLu4LU"),
            token_id = sp.nat(0)
        ),
        amount = sp.tez(1),
        expiry_time = sp.some(sp.timestamp(5))
    )
    sc += mp.offer(offer_data).run(sender = alice.address, amount = sp.tez(1))
    offer_data = sp.record(
        creator = bob.address,
        token = sp.record(
            address = sp.address("KT1Tezooo1zzSmartPyzzDYNAMiCzzpLu4LU"),
            token_id = sp.nat(0)
        ),
        amount = sp.tez(5),
        expiry_time = sp.some(sp.timestamp(10))
    )
    sc += mp.offer(offer_data).run(sender = bob.address, amount = sp.tez(5))

    sc.h1("Fulfill offer")
    sc += mp.fulfill_offer(sp.nat(0)).run(sender = admin.address)

    sc.h1("Retract Offer")
    sc += mp.retract_offer(sp.nat(1)).run(sender = bob.address)
    
    sc.h1("Create Ask")
    ask_data = sp.record(
        creator = alice.address,
        token = sp.record(
            address = sp.address("KT1TezoooozzSmartPyzzDYNAMiCzzpLu4LU"),
            token_id = sp.nat(0)
        ),
        amount = sp.tez(1),
        editions = sp.nat(2),
        expiry_time = sp.some(sp.timestamp(5))
    )
    sc += mp.ask(ask_data).run(sender = alice.address, amount = sp.tez(1))
    ask_data = sp.record(
        creator = bob.address,
        token = sp.record(
            address = sp.address("KT1Tezooo1zzSmartPyzzDYNAMiCzzpLu4LU"),
            token_id = sp.nat(0)
        ),
        amount = sp.tez(5),
        editions = sp.nat(5),
        expiry_time = sp.some(sp.timestamp(10))
    )
    sc += mp.ask(ask_data).run(sender = bob.address)

    sc.h1("Fulfill Ask")
    sc += mp.fulfill_ask(sp.nat(0)).run(sender = admin.address, amount = sp.tez(1))

    sc.h1("Retract Ask")
    sc += mp.retract_ask(sp.nat(1)).run(sender = bob.address)
