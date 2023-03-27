import smartpy as sp

class AuctionData:
    def __init__(self):
        self.type_value = sp.TRecord(
            creator = sp.TAddress,
            token = sp.TRecord(
                address = sp.TAddress,
                token_id = sp.TNat
                ),
            start_time = sp.TTimestamp,
            end_time = sp.TTimestamp,
            price_increment = sp.TMutez,
            current_price = sp.TMutez,
            highest_bidder = sp.TAddress
        )
    
    def get_type(self): return self.type_value

    def set_type(self): return sp.big_map(l = {}, tkey = sp.TNat, tvalue = self.type_value)

    def set_value(self, _params):
        return sp.record(
            creator = _params.creator,
            token = _params.token,
            start_time = _params.start_time,
            end_time = _params.end_time,
            price_increment = _params.price_increment,
            current_price = _params.current_price,
            highest_bidder = _params.highest_bidder
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

class Auction(sp.Contract):
    def __init__(self, _mod):
        self.init(
            mods = sp.set([_mod]),
            next_auction_id = sp.nat(0),
            auctions = AuctionData().set_type(),
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
    def create_auction(self, _params):
        sp.set_type(_params, AuctionData().get_type())
        sp.verify(_params.creator == sp.sender, "INVALID_CREATOR")
        self.data.auctions[self.data.next_auction_id] = AuctionData().set_value(_params)
        self.data.next_auction_id += sp.nat(1)
        params = [
                Batch_transfer.item(from_=sp.sender,
                                       txs=[
                                           sp.record(to_=sp.self_address,
                                                     amount=1,
                                                     token_id=_params.token.token_id)
                                       ])
            ]
        self.transfer_token(_params.token.address, params)
        sp.emit(sp.record(token=_params.token.address,token_id=_params.token.token_id),tag="AUCTION_CREATED")
        
    @sp.entry_point
    def cancel_auction(self, auction_id):
        sp.set_type(auction_id, sp.TNat)
        sp.verify(self.data.auctions.contains(auction_id), "INVALID_AUCTION_ID")
        sp.verify(self.data.auctions[auction_id].creator == sp.sender, "INVALID_CREATOR")
        sp.if self.data.auctions[auction_id].current_price > sp.tez(0):
            sp.send(self.data.auctions[auction_id].highest_bidder, self.data.auctions[auction_id].current_price)
        _params = [
                Batch_transfer.item(from_=sp.self_address,
                                       txs=[
                                           sp.record(to_=self.data.auctions[auction_id].creator,
                                                     amount=1,
                                                     token_id=self.data.auctions[auction_id].token.token_id)
                                       ])
            ]
        self.transfer_token(self.data.auctions[auction_id].token.address, _params)
        del self.data.auctions[auction_id]
        sp.emit(sp.record(auction_id=auction_id,tag="AUCTION_CANCELED"))
    
    @sp.entry_point
    def bid(self, auction_id):
        sp.set_type(auction_id, sp.TNat)
        sp.verify(self.data.auctions.contains(auction_id), "INVALID_AUCTION_ID")
        sp.verify(sp.amount >= self.data.auctions[auction_id].current_price + self.data.auctions[auction_id].price_increment, "INSUFFICIENT_AMOUNT")
        sp.verify(sp.now >= self.data.auctions[auction_id].start_time, "AUCTION_NOT_STARTED")
        sp.verify(sp.now <= self.data.auctions[auction_id].end_time, "AUCTION_ENDED")
        sp.if self.data.auctions[auction_id].highest_bidder != self.data.auctions[auction_id].creator:
            sp.send(self.data.auctions[auction_id].highest_bidder, self.data.auctions[auction_id].current_price)
        self.data.auctions[auction_id].current_price = sp.amount
        self.data.auctions[auction_id].highest_bidder = sp.sender
        sp.emit(sp.record(token=self.data.auctions[auction_id].token.address,token_id=self.data.auctions[auction_id].token.token_id,bid=sp.amount,bidder=sp.sender),tag="NEW_BID")
    
    @sp.entry_point
    def settle_auction(self, auction_id):
        sp.set_type(auction_id, sp.TNat)
        sp.verify(self.data.auctions.contains(auction_id), "INVALID_AUCTION_ID")
        _params = [
                Batch_transfer.item(from_=sp.self_address,
                                       txs=[
                                           sp.record(to_=self.data.auctions[auction_id].highest_bidder,
                                                     amount=1,
                                                     token_id=self.data.auctions[auction_id].token.token_id)
                                       ])
            ]
        self.transfer_token(self.data.auctions[auction_id].token.address, _params)
        sp.send(self.data.auctions[auction_id].creator, self.data.auctions[auction_id].current_price)
        del self.data.auctions[auction_id]
        sp.emit(sp.record(auction_id=auction_id,tag="AUCTION_SETTLED"))

    @sp.entry_point
    def toggle_pause(self):
        sp.verify(self.data.mods.contains(sp.sender), "NOT_MODERATOR")
        self.data.pause = ~self.data.pause


# @sp.add_test(name="Auction")
# def test():
#     sc = sp.test_scenario()
    
#     sc.h1("Quilt NFT Collection Aucitons")
#     sc.table_of_contents()
#     admin   = sp.address("tz1ADMINoooooooooooooooooooooooooooo")
#     alice   = sp.address("tz1ALICEoooooooooooooooooooooooooooo")
#     bob     = sp.address("tz1BOBoooooooooooooooooooooooooooooo")
#     elon    = sp.address("tz1ELONooooooooooooooooooooooooooooo")
#     mark    = sp.address("tz1MARKooooooooooooooooooooooooooooo")
#     john    = sp.address("tz1JOHNooooooooooooooooooooooooooooo")
#     mike    = sp.address("tz1MIKEooooooooooooooooooooooooooooo")
#     james   = sp.address("tz1JAMESoooooooooooooooooooooooooooo")
#     joe     = sp.address("tz1JOEoooooooooooooooooooooooooooooo")
#     adam    = sp.address("tz1ADAMooooooooooooooooooooooooooooo")
#     sc.show([admin, alice, bob, mark, elon, mark, john, mike, james, joe, adam])
    
#     sc.h1("Code")
#     auc = Auction(admin)
#     sc += auc
    
#     sc.h1("Create Auction")
#     auc_data = sp.record(
#             creator = alice,
#             token = sp.record(
#                 address = sp.address("KT1TezoooozzSmartPyzzDYNAMiCzzpLu4LU"),
#                 token_id = sp.nat(0)
#                 ),
#             start_time = sp.timestamp(0),
#             end_time = sp.timestamp(10),
#             price_increment = sp.tez(1),
#             current_price = sp.tez(0),
#             highest_bidder = alice
#         )
#     sc += auc.create_auction(auc_data).run(sender = alice)
#     auc_data = sp.record(
#             creator = bob,
#             token = sp.record(
#                 address = sp.address("KT1Tezooo1zzSmartPyzzDYNAMiCzzpLu4LU"),
#                 token_id = sp.nat(1)
#                 ),
#             start_time = sp.timestamp(0),
#             end_time = sp.timestamp(10),
#             price_increment = sp.tez(1),
#             current_price = sp.tez(0),
#             highest_bidder = bob
#         )
#     sc += auc.create_auction(auc_data).run(sender = bob)
    
#     sc.h1("Bid")
#     sc += auc.bid(1).run(sender = elon, amount=sp.tez(1))
#     sc += auc.bid(0).run(sender = elon, amount=sp.tez(1))
#     sc += auc.bid(0).run(sender = bob, amount=sp.tez(2))
#     sc += auc.bid(0).run(sender = mark, amount=sp.tez(3))
#     sc += auc.bid(0).run(sender = elon, amount=sp.tez(3), valid=False)
#     sc += auc.bid(0).run(sender = admin, amount=sp.tez(5))
    
#     sc.h1("Cancel Auction")
#     sc += auc.cancel_auction(sp.nat(1)).run(sender = bob)
    
#     sc.h1("Settle Auction")
#     sc += auc.settle_auction(sp.nat(0)).run(sender = alice)
#     sc += auc.toggle_pause().run(sender = admin)