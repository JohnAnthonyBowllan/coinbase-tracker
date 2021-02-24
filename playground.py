from coinbase.wallet.client import Client
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# CREDENTIALS
key = 'INSERT API KEY'
scrt = 'INSERT API SECRET KEY'


# FIXME: until we figure out why client.get_accounts() does not return all wallets
currencies_list = ['BTC','ETH','AAVE','LTC','NMR','COMP','GRT','CGLD','NU']

def coinbase_client(api_key:str, api_secret:str):
    client = Client(api_key, api_secret)
    return client


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
            transaction = {
                'timestamp':transaction_dict['created_at'],
                'amount': float(transaction_dict['amount']['amount']),
                'amount_currency': transaction_dict['amount']['currency'],
                'native_amount': float(transaction_dict['native_amount']['amount']),
                'native_currency': transaction_dict['native_amount']['currency'],
                'transaction_type': transaction_dict['type']
            }
            transactions_list.append(transaction)
        transactions_list.sort(key=lambda transaction: transaction['timestamp'])
        return transactions_list

    def get_average_price_per_coin(self):
        # TODO
        return 


def portfolio_stats(wallets: set):

    total_USD_invested = 0
    portfolio_value = 0

    for wallet in wallets:
        wallet_transactions = wallet.get_transactions()
        portfolio_value += wallet.native_balance
        for txn in wallet_transactions:
            total_USD_invested += txn['native_amount'] if txn['transaction_type'] == 'buy' else 0
    return {
        'balance': portfolio_value,
        'total_invested': total_USD_invested,

    }


client = coinbase_client(key,scrt)
wallets = set(Wallet(client,currency) for currency in currencies_list)
