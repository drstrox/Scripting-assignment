
from bitcoinrpc.authproxy import AuthServiceProxy
import json
from decimal import Decimal
import subprocess

rpc_user = "Aayush"
rpc_password = "Aayush@767"
rpc_port = 18443

try:
    rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@127.0.0.1:{rpc_port}")
    print("Connected to bitcoind successfully.")
except Exception as e:
    print(f"Error connecting to bitcoind: {e}")
    exit()

try:
    with open("addresses.json", "r") as f:
        addresses = json.load(f)
    address_B = addresses["address_B"]
    address_C = addresses["address_C"]
    print(f"Address B: {address_B}")
    print(f"Address C: {address_C}")
except Exception as e:
    print(f"Error loading addresses: {e}")
    exit()

try:
    unspent_B = rpc_connection.listunspent(0, 9999999, [address_B])
    if not unspent_B:
        print("No unspent transactions found for Address B. Funding Address B...")
        rpc_connection.generatetoaddress(101, address_B)
        print("101 blocks mined. Address B should now have a UTXO.")
        unspent_B = rpc_connection.listunspent(0, 9999999, [address_B])
        print("Updated UTXOs for Address B:", unspent_B)

    utxo_value_B = unspent_B[0]['amount']
    print(f"UTXO Value (B): {utxo_value_B} BTC")

    conf_target = 6
    fee_estimates = rpc_connection.estimatesmartfee(conf_target)

    if "errors" in fee_estimates or "feerate" not in fee_estimates:
        print("Error estimating fee. Using fallback fee rate.")
        fee_rate = Decimal("0.0002")
    else:
        fee_rate = Decimal(str(fee_estimates["feerate"]))

    tx_size = Decimal("200")
    fee = fee_rate * (tx_size / Decimal("1000"))
    output_amount_B_to_C = utxo_value_B - fee
    print(f"Sending {output_amount_B_to_C} BTC to Address C (Fee: {fee} BTC)")

    raw_tx_B_to_C = rpc_connection.createrawtransaction(
        [{"txid": unspent_B[0]['txid'], "vout": unspent_B[0]['vout']}],
        {address_C: float(output_amount_B_to_C)}
    )
    print(f"Raw Transaction (B to C): {raw_tx_B_to_C}")

    signed_tx_B_to_C = rpc_connection.signrawtransactionwithwallet(raw_tx_B_to_C)
    print(f"Signed Transaction (B to C): {signed_tx_B_to_C}")

    txid_B_to_C = rpc_connection.sendrawtransaction(signed_tx_B_to_C['hex'])
    print(f"Transaction ID (B to C): {txid_B_to_C}")

    decoded_tx_B_to_C = rpc_connection.decoderawtransaction(raw_tx_B_to_C)
    print(f"Decoded Transaction (B to C): {decoded_tx_B_to_C}")

    scriptSig = decoded_tx_B_to_C['vin'][0]['scriptSig']['hex']
    scriptPubKey_C = decoded_tx_B_to_C['vout'][0]['scriptPubKey']['hex']
    print(f"ScriptSig: {scriptSig}")
    print(f"ScriptPubKey for Address C: {scriptPubKey_C}")

    txid_A_to_B = unspent_B[0]['txid']
    try:
        decoded_tx_A_to_B = rpc_connection.getrawtransaction(txid_A_to_B, True)
    except Exception as e:
        print(f"Error getting raw transaction: {e}. Trying gettransaction...")
        decoded_tx_A_to_B = rpc_connection.gettransaction(txid_A_to_B)

    scriptPubKey_B = decoded_tx_A_to_B['vout'][unspent_B[0]['vout']]['scriptPubKey']['hex']
    print(f"ScriptPubKey from previous transaction (A to B): {scriptPubKey_B}")

    print("\nValidating ScriptSig against ScriptPubKey using bitcoin-cli...")
    try:
        result = subprocess.run(
            [
                "bitcoin-cli",
                "-regtest",
                "verifyscript",
                scriptSig,
                scriptPubKey_B,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("Script validation successful! The ScriptSig satisfies the ScriptPubKey.")
        else:
            print(f"Script validation failed: {result.stderr}")
    except Exception as e:
        print(f"Error validating script: {e}")
except Exception as e:
    print(f"Error creating transaction (B to C): {e}")
    exit()
