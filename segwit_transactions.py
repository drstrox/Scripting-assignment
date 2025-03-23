import time
from decimal import Decimal 
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

rpc_user = "Lucky"
rpc_password = "Lucky@786"
rpc_url = f"http://{rpc_user}:{rpc_password}@127.0.0.1:18443"

rpc_client = AuthServiceProxy(rpc_url)

wallet_label = "testwallet"
available_wallets = rpc_client.listwallets()

if wallet_label not in available_wallets:
    try:
        rpc_client.createwallet(wallet_label)
        print(f"Wallet '{wallet_label}' created successfully.")
    except JSONRPCException as err:
        print(f"Error creating wallet: {err}")

try:
    rpc_client.loadwallet(wallet_label)
    print(f"Wallet '{wallet_label}' loaded successfully.")
except JSONRPCException as err:
    if "-35" in str(err):  
        print(f"Wallet '{wallet_label}' is already loaded. Continuing...")
    else:
        print(f"Error loading wallet: {err}")
        exit(1)

wallet_balance = rpc_client.getbalance()
if wallet_balance == 0:
    print("Wallet balance is zero. Mining blocks to generate test BTC...")
    rpc_client.generatetoaddress(101, rpc_client.getnewaddress())
    wallet_balance = rpc_client.getbalance()

print(f"Wallet balance: {wallet_balance} BTC")

recipient_1 = rpc_client.getnewaddress("Recipient_1", "p2sh-segwit")
recipient_2 = rpc_client.getnewaddress("Recipient_2", "p2sh-segwit")
recipient_3 = rpc_client.getnewaddress("Recipient_3", "p2sh-segwit")

print(f"Generated P2SH-SegWit Addresses:\n1: {recipient_1}\n2: {recipient_2}\n3: {recipient_3}")

transfer_amount = min(5, wallet_balance)
if transfer_amount < 0.0001:
    raise Exception(f"Amount {transfer_amount} BTC is too small to send.")

transaction_id = rpc_client.sendtoaddress(recipient_1, transfer_amount)
print(f"Transaction ID for funding Recipient 1: {transaction_id}")

rpc_client.generatetoaddress(1, rpc_client.getnewaddress())

time.sleep(2)
unspent_txns = rpc_client.listunspent(1, 9999999, [recipient_1])
if not unspent_txns:
    raise Exception("No UTXOs found for Recipient 1.")

utxo_entry = unspent_txns[0]
input_txns = [{"txid": utxo_entry["txid"], "vout": utxo_entry["vout"]}]

sendable_amount = Decimal(transfer_amount) - Decimal("0.001")

if sendable_amount < Decimal("0.0001"):
    raise Exception(f"Final output amount {sendable_amount} BTC is too small.")

output_destinations = {recipient_2: str(sendable_amount)}

unsigned_txn = rpc_client.createrawtransaction(input_txns, output_destinations)
decoded_unsigned_txn = rpc_client.decoderawtransaction(unsigned_txn)
print("Decoded Raw Transaction:", decoded_unsigned_txn)

for vout in decoded_unsigned_txn["vout"]:
    print(f"scriptPubKey: {vout['scriptPubKey']['hex']}")

signed_txn = rpc_client.signrawtransactionwithwallet(unsigned_txn)
if not signed_txn["complete"]:
    raise Exception("Transaction signing failed")

broadcast_txn_id = rpc_client.sendrawtransaction(signed_txn["hex"])
print(f"Broadcasted Transaction ID: {broadcast_txn_id}")

rpc_client.generatetoaddress(1, rpc_client.getnewaddress())

print("Waiting for transaction confirmation...")
while True:
    txn_info = rpc_client.gettransaction(broadcast_txn_id)
    if txn_info["confirmations"] > 0:
        print(f"Transaction from Recipient 1 to Recipient 2 is complete. (TXID: {broadcast_txn_id})")
        break
    time.sleep(2)

decoded_signed_txn = rpc_client.decoderawtransaction(signed_txn["hex"])
for vin in decoded_signed_txn["vin"]:
    print(f"scriptSig: {vin['scriptSig']['hex']}")

time.sleep(2)
unspent_txns_2 = rpc_client.listunspent(1, 9999999, [recipient_2])

if not unspent_txns_2:
    raise Exception("No UTXOs found for Recipient 2.")

utxo_entry_2 = unspent_txns_2[0]
input_txns_2 = [{"txid": utxo_entry_2["txid"], "vout": utxo_entry_2["vout"]}]

amount_received = Decimal(utxo_entry_2["amount"])
txn_fee = Decimal("0.001")
sendable_amount_2 = amount_received - txn_fee

if sendable_amount_2 <= Decimal("0.0001"):
    raise Exception(f"Final output amount {sendable_amount_2} BTC is too small.")

output_destinations_2 = {recipient_3: str(sendable_amount_2)}

unsigned_txn_2 = rpc_client.createrawtransaction(input_txns_2, output_destinations_2)
decoded_unsigned_txn_2 = rpc_client.decoderawtransaction(unsigned_txn_2)
print("Decoded Raw Transaction (Recipient 2 -> Recipient 3):", decoded_unsigned_txn_2)

for vout in decoded_unsigned_txn_2["vout"]:
    print(f"scriptPubKey: {vout['scriptPubKey']['hex']}")

signed_txn_2 = rpc_client.signrawtransactionwithwallet(unsigned_txn_2)
if not signed_txn_2["complete"]:
    raise Exception("Transaction signing failed for Recipient 2 to Recipient 3.")

broadcast_txn_id_2 = rpc_client.sendrawtransaction(signed_txn_2["hex"])
print(f"Broadcasted Transaction ID (Recipient 2 -> Recipient 3): {broadcast_txn_id_2}")

rpc_client.generatetoaddress(1, rpc_client.getnewaddress())

print("Waiting for transaction confirmation...")
while True:
    txn_info_2 = rpc_client.gettransaction(broadcast_txn_id_2)
    if txn_info_2["confirmations"] > 0:
        print(f"Transaction from Recipient 2 to Recipient 3 is complete. (TXID: {broadcast_txn_id_2})")
        break
    time.sleep(2)

decoded_signed_txn_2 = rpc_client.decoderawtransaction(signed_txn_2["hex"])
for vin in decoded_signed_txn_2["vin"]:
    print(f"scriptSig: {vin['scriptSig']['hex']}")