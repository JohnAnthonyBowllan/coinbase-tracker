from coinbase.wallet.client import Client
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json


# CREDENTIALS
with open('coinbase_api.json') as creds:
    data = json.load(creds)

key = data['key']
scrt = data['secret_key']


# FIXME: until we figure out why client.get_accounts() does not return all wallets
currencies_list = ['BTC','ETH','AAVE','LTC','NMR','COMP','GRT','CGLD','NU']

def coinbase_client(api_key:str, api_secret:str):
    client = Client(api_key, api_secret)
    return client


def coinbase_transaction_fee(native_amount: float, transaction_type: str):
    if transaction_type in ('trade','send'):
        return 0
    elif transaction_type in ('buy','sell'):
        empirical_variable_percentage_fee = 0.01468
        if native_amount <= 10:
            return max(0.99,empirical_variable_percentage_fee*native_amount)
        elif native_amount > 10 and native_amount <= 25:
            return max(1.49,empirical_variable_percentage_fee*native_amount)
        elif native_amount > 25 and native_amount <= 50:
            return max(1.99,empirical_variable_percentage_fee*native_amount)
        elif native_amount >= 50:
            return max(2.99,empirical_variable_percentage_fee*native_amount)


class Wallet:

    def __init__(self, client: Client, currency: str):
        wallet_dict = client.get_account(currency)
        self.client = client
        self.currency = currency
        self.balance = float(wallet_dict['balance']['amount'])
        self.native_currency = wallet_dict['native_balance']['currency']
        self.native_balance = float(wallet_dict['native_balance']['amount'])


    def get_transactions(self):
        transactions_list = []

        for transaction_dict in self.client.get_transactions(self.currency)['data']:
            # print(transaction_dict)
            transaction_fee = coinbase_transaction_fee(float(transaction_dict['native_amount']['amount']),transaction_dict['type'])
            transaction = {
                'timestamp':transaction_dict['created_at'],
                'amount': float(transaction_dict['amount']['amount']),
                'amount_currency': transaction_dict['amount']['currency'],
                'native_amount': float(transaction_dict['native_amount']['amount']),
                'native_amount_with_fee': float(transaction_dict['native_amount']['amount']) - transaction_fee,
                'native_currency': transaction_dict['native_amount']['currency'],
                'transaction_type': transaction_dict['type']
            }
            transaction['price_per_coin']= transaction['native_amount_with_fee']/transaction['amount']
            transactions_list.append(transaction)
        transactions_list.sort(key=lambda transaction: transaction['timestamp'])
        return transactions_list


def portfolio_stats(wallets: set):

    total_USD_invested = 0
    total_USD_granted = 0
    portfolio_value = 0

    for wallet in wallets:
        wallet_transactions = wallet.get_transactions()
        portfolio_value += wallet.native_balance
        for txn in wallet_transactions:
            total_USD_invested += txn['native_amount'] if txn['transaction_type'] in ('buy','sell') else 0
            total_USD_granted += txn['native_amount'] if txn['transaction_type'] in ('send') else 0
    return {
        'balance': portfolio_value,
        'total_invested': total_USD_invested,
        'total_granted': total_USD_granted
    }

def average_coin_price_from_action(wallets: set, action: str):
    # action: buy or sell

    if action == 'buy':
        valid_txn_types = ['buy','send','trade']
        txn_amount_sign_const = 1.0
    elif action == 'sell':
        valid_txn_types = ['sell','trade']
        txn_amount_sign_const = -1.0

    wallet_to_price = {}

    for wallet in wallets:
        total = 0
        transactions_price_per_coin = []
        transactions_amount = []
        for txn in wallet.get_transactions():
            txn_type = txn['transaction_type'] 
            if txn_type in valid_txn_types and txn['amount']/txn_amount_sign_const > 0:
                total += txn['amount']
                transactions_price_per_coin.append(txn['price_per_coin'])
                transactions_amount.append(txn['amount'])

        if transactions_price_per_coin:
            txn_weights = map(lambda amount: amount/total,transactions_amount)
            avg_price = sum([price*weight for price,weight in zip(transactions_price_per_coin,txn_weights)])
            wallet_to_price[wallet.currency] = avg_price
        else:
            wallet_to_price[wallet.currency] = None

    return wallet_to_price 



client = coinbase_client(key,scrt)
wallets = set(Wallet(client,currency) for currency in currencies_list)

stats = portfolio_stats(wallets)
avg_buy_prices = average_coin_price_from_action(wallets,'buy')
avg_sell_prices = average_coin_price_from_action(wallets,'sell')

print(stats)
print(avg_buy_prices)
print(avg_sell_prices)