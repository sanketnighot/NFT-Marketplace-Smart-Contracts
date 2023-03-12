# Quilt-Smart-Contracts

## Running Files in Local Environment
1. Setup Local Smartpy Environment. [Check this](https://smartpy.io/docs/cli/)
2. To run Contract Factory use
`~/smartpy-cli/SmartPy.sh test ./ContractFactory.py ./output/ContractFactory --html --purge`
3. To originate Smart Contract use
`~/smartpy-cli/SmartPy.sh originate-contract --code <...contract.json FILE> --storage <...storage.json FILE> --rpc <YOUR_RPC> --private-key <YOUR_PRIVATE_KEY>`
