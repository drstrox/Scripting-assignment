from bitcoinrpc.authproxy import AuthServiceProxy
import json
from decimal import Decimal

rpc_user = "Aayush"
rpc_password = "Aayush@767"
rpc_port = 18443

try:
    rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@127.0.0.1:{rpc_port}")
    print("Connected to bitcoind successfully.")
except Exception as e:
    print(f"Error connecting to bitcoind: {e}")
    exit()

wallet_name = "MYWALLET"

try:
    wallets = rpc_connection.listwallets()
    print(f"Existing Wallets: {wallets}")

    if wallet_name in wallets:
        print(f"Wallet '{wallet_name}' is already loaded.")
    else:
        print(f"Wallet '{wallet_name}' does not exist. Creating it...")
        rpc_connection.createwallet(wallet_name)
        print(f"Wallet '{wallet_name}' created successfully.")
except Exception as e:
    print(f"Error with wallet: {e}")
    exit()

try:
    rpc_connection_wallet = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@127.0.0.1:{rpc_port}/wallet/{wallet_name}")
    print(f"Connected to wallet '{wallet_name}' successfully.")
except Exception as e:
    print(f"Error connecting to wallet '{wallet_name}': {e}")
    exit()

try:
    address_A = rpc_connection_wallet.getnewaddress("", "legacy")
    address_B = rpc_connection_wallet.getnewaddress("", "legacy")
    address_C = rpc_connection_wallet.getnewaddress("", "legacy")
    print(f"Address A: {address_A}")
    print(f"Address B: {address_B}")
    print(f"Address C: {address_C}")

    addresses = {
        "address_A": address_A,
        "address_B": address_B,
        "address_C": address_C
    }
    with open("addresses.json", "w") as f:
        json.dump(addresses, f)
    print("Addresses saved to addresses.json")
except Exception as e:
    print(f"Error generating addresses: {e}")
    exit()

try:
    addresses = rpc_connection_wallet.getaddressesbylabel("")
    print(f"Addresses in wallet: {addresses}")
    if address_A not in addresses:
        print(f"Address A ({address_A}) does not belong to the wallet. Generating a new address...")
        address_A = rpc_connection_wallet.getnewaddress()
        print(f"New Address A: {address_A}")
except Exception as e:
    print(f"Error verifying address ownership: {e}")
    exit()

try:
    print("Mining blocks to fund Address A...")
    blocks_to_mine = 201
    rpc_connection.generatetoaddress(blocks_to_mine, address_A)
    print(f"Mined {blocks_to_mine} blocks to Address A: {address_A}")
except Exception as e:
    print(f"Error mining blocks: {e}")
    exit()

try:
    unspent_A = rpc_connection_wallet.listunspent(0, 9999999, [address_A])
    if not unspent_A:
        print("No unspent transactions found for Address A.")
        exit()

    utxo_value = unspent_A[0]['amount']
    print(f"UTXO Value: {utxo_value} BTC")
except Exception as e:
    print(f"Error checking UTXOs: {e}")
    exit()

try:
    conf_target = 6
    fee_estimates = rpc_connection.estimatesmartfee(conf_target)

    if "errors" in fee_estimates or "feerate" not in fee_estimates:
        print("Error estimating fee. Using fallback fee rate.")
        fee_rate = Decimal("0.00001")
    else:
        fee_rate = Decimal(str(fee_estimates["feerate"]))

    tx_size = Decimal("200")
    fee = fee_rate * (tx_size / Decimal("1000"))

    if utxo_value <= fee:
        print(f"UTXO value ({utxo_value} BTC) is too small to cover the fee ({fee} BTC).")
        print("Mining more blocks to fund Address A...")
        rpc_connection.generatetoaddress(1, address_A)
        print("1 block mined. Address A should now have a UTXO.")
        unspent_A = rpc_connection_wallet.listunspent(0, 9999999, [address_A])
        utxo_value = unspent_A[0]['amount']
        print(f"Updated UTXO Value: {utxo_value} BTC")

    output_amount = utxo_value - fee
    print(f"Sending {output_amount} BTC to Address B (Fee: {fee} BTC)")

    raw_tx_A_to_B = rpc_connection_wallet.createrawtransaction(
        [{"txid": unspent_A[0]['txid'], "vout": unspent_A[0]['vout']}],
        {address_B: float(output_amount)}
    )
    print(f"Raw Transaction (A to B): {raw_tx_A_to_B}")

    signed_tx_A_to_B = rpc_connection_wallet.signrawtransactionwithwallet(raw_tx_A_to_B)
    print(f"Signed Transaction (A to B): {signed_tx_A_to_B}")

    txid_A_to_B = rpc_connection_wallet.sendrawtransaction(signed_tx_A_to_B['hex'])
    print(f"Transaction ID (A to B): {txid_A_to_B}")

    decoded_tx_A_to_B = rpc_connection_wallet.decoderawtransaction(raw_tx_A_to_B)
    print(f"Decoded Transaction (A to B): {decoded_tx_A_to_B}")

    scriptPubKey_B = decoded_tx_A_to_B['vout'][0]['scriptPubKey']['hex']
    print(f"ScriptPubKey for Address B: {scriptPubKey_B}")
except Exception as e:
    print(f"Error creating transaction (A to B): {e}")
    exit()