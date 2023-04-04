import smartpy as sp

FA2_contract = sp.io.import_script_from_url('file:./FA2.py')
Marketplace = sp.io.import_script_from_url('file:./Marketplace.py')
Auction = sp.io.import_script_from_url('file:./Auction.py')
Addr = sp.io.import_script_from_url('file:./utils/Addresses.py')

def global_parameter(env_var, default):
    try:
        if os.environ[env_var] == "true":
            return True
        if os.environ[env_var] == "false":
            return False
        return default
    except:
        return default

def environment_config():
    return FA2_contract.FA2_config(
        debug_mode=global_parameter("debug_mode", False),
        single_asset=global_parameter("single_asset", False),
        non_fungible=global_parameter("non_fungible", True),
        add_mutez_transfer=global_parameter("add_mutez_transfer", False),
        readable=global_parameter("readable", True),
        force_layouts=global_parameter("force_layouts", True),
        support_operator=global_parameter("support_operator", True),
        assume_consecutive_token_ids=global_parameter(
            "assume_consecutive_token_ids", True),
        store_total_supply=global_parameter("store_total_supply", False),
        lazy_entry_points=global_parameter("lazy_entry_points", False),
        allow_self_transfer=global_parameter("allow_self_transfer", False),
        use_token_metadata_offchain_view=global_parameter(
            "use_token_metadata_offchain_view", True),
    )

class Batch_transfer:
    def get_transfer_type(self):
        tx_type = sp.TRecord(to_=sp.TAddress,
                             token_id=sp.TNat,
                             amount=sp.TNat)
        transfer_type = sp.TRecord(from_=sp.TAddress,
                                   txs=sp.TList(tx_type)).layout(
                                       ("from_", "txs"))
        return transfer_type

    def get_type(self):
        return sp.TList(self.get_transfer_type())

    def item(self, from_, txs):
        v = sp.record(from_=from_, txs=txs)
        return sp.set_type_expr(v, self.get_transfer_type())

class Operator_param:
    def get_type(self):
        t = sp.TRecord(
            owner=sp.TAddress,
            operator=sp.TAddress,
            token_id=sp.TNat)

    def make(self, owner, operator, token_id):
        r = sp.record(owner=owner,
                      operator=operator,
                      token_id=token_id)
        return sp.set_type_expr(r, self.get_type())

@sp.add_test(name = "Test")
def test():
    # Initializing test scenarios
    sc = sp.test_scenario()
    sc.h1("~: Quilt Marketplace Contract Tests :~")
    sc.table_of_contents()
    
    # Originating Smart Contracts in Sandbox
    metadata = sp.map({"": sp.utils.bytes_of_string("https://ipfs.io/ipfs/bafyreias7kz2ryktu34afqwh56pltm32uxsecaxsootklwlsquw5gn3ptq/metadata.json/")})
    fa2_1 = FA2_contract.FA2(config=environment_config(), metadata=metadata, admin=Addr.admin)
    fa2_2 = FA2_contract.FA2(config=environment_config(), metadata=metadata, admin=Addr.admin)
    mp = Marketplace.Marketplace(Addr.admin)
    au = Auction.Auction(Addr.admin)
    
    sc.h1("Deploying Smart Contracts")
    sc.p("✨ Smart Contracts compiled and originated in sandbox successfully ...")
    sc.p("> FA2 Contract")
    sc.register(fa2_1)
    sc.register(fa2_2)
    
    sc.p("> Marketplace Contract")
    sc.register(mp)
    
    sc.p("> Auctions Contract")
    sc.register(au)
    
    sc.h1("FA2:- Mint tokens")
    fa2_1.mint(address=Addr.alice,
                amount=1,
                metadata=sp.map({"": sp.utils.bytes_of_string(
                    "https://ipfs.io/ipfs/bafyreias7kz2ryktu34afqwh56pltm32uxsecaxsootklwlsquw5gn3ptq/metadata.json/")}),
                token_id=0).run(sender=Addr.admin)
    
    fa2_2.mint(address=Addr.bob,
                amount=15,
                metadata=sp.map({"": sp.utils.bytes_of_string(
                    "https://ipfs.io/ipfs/bafyreias7kz2ryktu34afqwh56pltm32uxsecaxsootklwlsquw5gn3ptq/metadata.json/")}),
                token_id=0).run(sender=Addr.admin)
    
    sc.h1("Part 1:- Testing Offers part in Marketplace Contract")
    sc.h2("> Elon makes offer to Alice NFT")
    offer_data = sp.record(
        creator = Addr.elon,
        token = sp.record(
            address = fa2_1.address,
            token_id = sp.nat(0)
        ),
        amount = sp.tez(5),
        expiry_time = sp.none
    )
    sc += mp.offer(offer_data).run(sender = Addr.elon, amount = sp.tez(5))
    
    sc.h2("> Alice accepts Elons offer")
    sc.h3(">> FA2 Call: Alice adds Marketplace Contract as operator of NFT")
    sc += fa2_1.update_operators([
                sp.variant("add_operator", Operator_param().make(
                    owner= Addr.alice,
                    operator=mp.address,
                    token_id=0))]).run(sender= Addr.alice)
    sc.h3(">> Marketplace Call: Alice accepts offer of Elon")
    sc += mp.fulfill_offer(sp.nat(0)).run(sender = Addr.alice)
    
    sc.h3(">> Tests: Verify data and check storage")
    sc.show(mp.data)
    sc.p("Current ꜩ Balance")
    sc.show(mp.balance)
    
    sc.h2("> Elon makes another offer to Alice NFT")
    offer_data = sp.record(
        creator = Addr.elon,
        token = sp.record(
            address = fa2_1.address,
            token_id = sp.nat(0)
        ),
        amount = sp.tez(5),
        expiry_time = sp.none
    )
    sc += mp.offer(offer_data).run(sender = Addr.elon, amount = sp.tez(5))
    
    sc.h2("> Alice accepts Elons offer")
    sc.h3(">> FA2 Call: Alice adds Marketplace Contract as operator of NFT")
    sc += fa2_1.update_operators([
                sp.variant("add_operator", Operator_param().make(
                    owner= Addr.alice,
                    operator=mp.address,
                    token_id=0))]).run(sender= Addr.alice)
    sc.h3(">> Marketplace Call: Alice accepts offer of Elon")
    sc += mp.fulfill_offer(sp.nat(1)).run(sender = Addr.alice, valid = False)

    sc.h3(">> Tests: Verify data and check storage")
    sc.verify((mp.data.offers).contains(1))     # Checks if storage contains the offer data
    sc.show(mp.data)
    sc.p("Current ꜩ Balance")
    sc.show(mp.balance)


    sc.h2("> Elon retracts the offer")
    sc += mp.retract_offer(sp.nat(1)).run(sender = Addr.elon)
    
    sc.verify(~(mp.data.offers).contains(1))       # Checks if storage has deleted the offer data
    sc.show(mp.data)
    sc.p("Current ꜩ Balance")
    sc.show(mp.balance)
    
    sc.h1("Part 2:- Testing Asks part in Marketplace Contract")
    sc.h2("> Bob places ask for his NFT")
    sc.h3(">> FA2 Call: Bob adds Marketplace Contract as operator of NFT")
    sc += fa2_2.update_operators([
                sp.variant("add_operator", Operator_param().make(
                    owner=Addr.bob,
                    operator=mp.address,
                    token_id=0))]).run(sender=Addr.bob)
    
    sc.h3(">> Marketplace Call: Bob places Ask on Marketplace")
    ask_data = sp.record(
        creator = Addr.bob,
        token = sp.record(
            address = fa2_2.address,
            token_id = sp.nat(0)
        ),
        amount = sp.tez(12),
        editions = sp.nat(5),
        expiry_time = sp.none
    )
    sc += mp.ask(ask_data).run(sender = Addr.bob)
    
    sc.h2("> Mark Accepts Bobs Ask")
    sc += mp.fulfill_ask(sp.nat(0)).run(sender = Addr.mark, amount = sp.tez(12))
    
    sc.h3(">> Tests: Verify data and check storage")
    sc.show(mp.data)
    sc.p("Current ꜩ Balance")
    sc.show(mp.balance)
    
    
    sc.h1("Part 3:- Testing Auctions Smart Contract")
    sc.h2("> Bob creates an Auction")
    auc_data = sp.record(
            creator = Addr.bob,
            token = sp.record(
                address = fa2_2.address,
                token_id = sp.nat(0)
                ),
            start_time = sp.timestamp(0),
            end_time = sp.timestamp(10),
            price_increment = sp.tez(1),
            current_price = sp.tez(0),
            highest_bidder = Addr.bob
        )
    
    sc.h3(">> FA2 Call: Bob makes Auction contract an Operator")
    sc += fa2_2.update_operators([
                sp.variant("add_operator", Operator_param().make(
                    owner=Addr.bob,
                    operator=au.address,
                    token_id=0))]).run(sender=Addr.bob)
    sc.h3(">> Auction Call: Bob Creates Auction")
    sc += au.create_auction(auc_data).run(sender = Addr.bob)
    
    sc.h2(">Bids get submitted")
    sc += au.bid(0).run(sender = Addr.elon, amount=sp.tez(1))
    sc += au.bid(0).run(sender = Addr.bob, amount=sp.tez(2))
    sc += au.bid(0).run(sender = Addr.mark, amount=sp.tez(3))
    sc += au.bid(0).run(sender = Addr.elon, amount=sp.tez(3), valid=False)
    sc += au.bid(0).run(sender = Addr.admin, amount=sp.tez(5))
    
    sc.h2("> Bob ends Auction")
    sc += au.settle_auction(sp.nat(0)).run(sender = Addr.bob)


@sp.add_test(name="Mutation1")
def test():
    s = sp.test_scenario()
    with s.mutation_test() as mt:
        mt.add_scenario("Test", contract_id=2)