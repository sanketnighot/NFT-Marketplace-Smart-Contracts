# Quilt-Smart-Contracts

## Running Files in Local Environement
1. Setup Local Smartpy Enviornent. [Check this](https://smartpy.io/docs/cli/"Check this")
2. To run Contract Factory use
`~/smartpy-cli/SmartPy.sh test ./ContractFactory.py ./output/ContractFactory --html --purge`
3. To originate Smart Contract use
`~/smartpy-cli/SmartPy.sh originate-contract --code <...contract.json FILE> --storage <...storage.json FILE> --rpc <YOUR_RPC_URL> --private-key <YOUR_PRIVATE_KEY>`
