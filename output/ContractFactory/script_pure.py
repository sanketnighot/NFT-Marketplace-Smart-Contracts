import smartpy as sp

# Import the modified FA2 contract
FA2_contract = sp.io.import_script_from_url('file:./FA2.py')

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

class Contract(sp.Contract):
    def __init__(self):
        self.init(
            contracts=sp.big_map(tkey=sp.TAddress, tvalue=sp.TList(sp.TAddress)),
        )

    # Define the entrypoint to deploy the FA2 contract
    @sp.entry_point
    def deploy_fa2(self, metadata):
        fa2_contract = sp.create_contract(
            contract = FA2_contract.FA2(config=environment_config(),
                              metadata=metadata,
                              admin=sp.self_address)
        )
        
        # Add the contract address to the bigmap
        with sp.if_(self.data.contracts.contains(sp.sender)):
            self.data.contracts[sp.sender].push(fa2_contract)
        with sp.else_():
            self.data.contracts[sp.sender] = [fa2_contract]
        sp.emit(sp.record(event="CONTRACT_DEPLOYED",deployed_by=sp.sender,contract_address=fa2_contract),tag="CONTRACT_DEPLOYED")
    
    # Define the entrypoint to deploy the FA2 contract
    @sp.entry_point
    def mint_token(self, contract, amount, token_id, metadata):
        sp.set_type(contract, sp.TAddress)
        sp.set_type(amount, sp.TNat)
        sp.set_type(token_id, sp.TNat)
        sp.set_type(metadata, sp.TMap(sp.TString, sp.TBytes))
        with sp.for_('addr', self.data.contracts[sp.sender]) as addr:
            with sp.if_(addr == contract):
                contractParams = sp.contract(sp.TRecord(address = sp.TAddress, amount = sp.TNat, metadata = sp.TMap(sp.TString, sp.TBytes), token_id = sp.TNat), contract, entry_point="mint").open_some()
                dataToBeSent = sp.record(address = sp.sender, amount = amount, metadata = metadata, token_id = token_id)
                sp.transfer(dataToBeSent,sp.mutez(0),contractParams)
                sp.emit(sp.record(event="TOKEN_MINTED",minted_by=sp.sender,amount=amount),tag="TOKEN_MINTED")

@sp.add_test(name="Contract test")
def test():
    sc = sp.test_scenario()
    sc.h1("Quilt NFT Collection Contract Factory")
    sc.table_of_contents()
    admin = sp.test_account("Admin")
    elon = sp.test_account("Elon")
    mark = sp.test_account("Mark")
    sc.show([mark, elon, admin])
    c = Contract()
    sc.h1("Code")   
    sc += c
    sc += c.deploy_fa2(sp.utils.metadata_of_url("https://example1.com")).run(sender = admin.address)
    # sc += c.deploy_fa2(sp.utils.metadata_of_url("https://example2.com")).run(sender = elon.address)
    # sc += c.deploy_fa2(sp.utils.metadata_of_url("https://example3.com")).run(sender = mark.address)
    # sc += c.mint_token(contract = sp.address("KT1TezoooozzSmartPyzzDYNAMiCzzpLu4LU"), amount = sp.nat(10), token_id = sp.nat(0), metadata = sp.map({"": sp.utils.bytes_of_string("https://ipfs.io/ipfs/bafyreias7kz2ryktu34afqwh56pltm32uxsecaxsootklwlsquw5gn3ptq/metadata.json/")})).run(sender = admin.address)
    # assert c.data.contracts[admin][0] == sp.contract(FA2_contract, c.address_of(admin)).address
