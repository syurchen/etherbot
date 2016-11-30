from etherscan.accounts import Account
import json

key = '59W93VKBDTSR1V8EQTBGYDWEVZEIYIPHCV'

address = '0xb794f5ea0ba39494ce839613fffba74279579268'

api = Account(address=address, api_key=key)
balance = api.get_balance()
print(balance)

