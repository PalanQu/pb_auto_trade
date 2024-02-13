# pb_auto_trade
1. put your public/private key into the apikey.json file
2. put trading pair into config.json
3. put single trade volume into config.json
4. put how many times you want trade into config.json

例子:
交易对 SOL_USDC
每次交易1SOL
交易10次, 买入+卖出算1次

{
    "trading_pair": "SOL_USDC",
    "single_order_quantity": 1.00,
    "iteration_time": 10
}