import urllib.request
import json
import time
import hashlib
import base64
import nacl.signing

# read api key or api secret from config file
def read_api_key_from_file(file_name, field_name):
    try:
        with open(file_name, "r") as file:
            data = json.load(file)
            api_key = data.get(field_name)
            return api_key
    except Exception as e:
        print(f"Error reading API key from file: {e}")
        return None
    
def get_instructions(instruction):
    instructions = {
        "get_balances": "balanceQuery",
        "get_deposit_address": "depositAddressQuery",
        "get_deposits": "depositQueryAll",
        "get_fill_history": "fillHistoryQueryAll",
        "cancel_open_order": "orderCancel",
        "cancel_open_orders": "orderCancelAll",
        "execute_order": "orderExecute",
        "get_orders_history": "orderHistoryQueryAll",
        "get_open_order": "orderQuery",
        "get_open_orders": "orderQueryAll",
        "request_withdraw": "withdraw",
        "get_withdraws": "withdrawalQueryAll"
    }
    result = instructions.get(instruction)
    return result


def get_balance(api_key, signature, timestamp, window=5000):
    api_url = "https://api.backpack.exchange/api/v1/assets"
    params = {'timestamp': timestamp, 'window': window}  
    headers = {
        "X-API-KEY": api_key,
        "X-SIGNATURE": signature,
        "X-TIMESTAMP": str(timestamp),
        "X-WINDOW": str(window),
        "Content-Type": "application/json; charset=utf-8" 
    }
    
    try:
        encoded_params = urllib.parse.urlencode(params)
        full_url = api_url + '?' + encoded_params
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            return response_data
    except Exception as e:
        print(f"Error: {e}")
        return None

# generate order execution request
def execute_order(api_key, signature, timestamp, window, parameters):
    api_url = "https://api.backpack.exchange/api/v1/order?instruction=orderExecute"
    params = parameters
    headers = {
        "X-API-KEY": api_key,
        "X-SIGNATURE": signature,
        "X-TIMESTAMP": str(timestamp),
        "X-WINDOW": str(window),
        "Content-Type": "application/json"  # 添加Content-Type请求头
    }

    try:
        request_body = json.dumps(params).encode('utf-8')
        timestamp_and_window = {'timestamp': timestamp, 'window': window}
        encoded_params = urllib.parse.urlencode(params)
        encoded_timestamp_and_window = urllib.parse.urlencode(timestamp_and_window)
        full_url = api_url + '&' + encoded_params + '&' + encoded_timestamp_and_window
        print("full url: ", full_url)
        print("request body: ", request_body)
        req = urllib.request.Request(full_url, data=request_body, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            # 获取状态码
            status_code = response.getcode()
            # 如果状态码是 200 或者 202，打印响应的内容
            if status_code in [200, 202]:
                response_data = response.read().decode('utf-8')
                print(f"Status Code: {status_code}")
                print(f"Response Body: {response_data}")
            else:
                print(f"Unexpected Status Code: {status_code}")
            return response_data
    except urllib.error.HTTPError as e:
    # 获取错误响应的状态码和原因
        status_code = e.code
        reason = e.reason
        # 获取错误响应的内容（如果有的话）
        error_content = e.read().decode('utf-8')
        # 打印错误信息
        print(f"HTTP Error {status_code}: {reason}")
        print(f"Error Content: {error_content}")
    
# 计算签名
def calculate_signature(instruction, timestamp, window, parameters):
    data = "instruction=" + instruction + "&"
    sorted_params = dict(sorted(parameters.items()))
    print("sorted_params: ", sorted_params)
    data += urllib.parse.urlencode(sorted_params)
    data += "&timestamp=" + str(timestamp) + "&window=" + str(window)
    print("data: ", data)
    encoded_private_key = read_api_key_from_file("apikey.json", "api_secret")
    private_key = base64.b64decode(encoded_private_key)
    signing_key = nacl.signing.SigningKey(private_key)
    signed_message = signing_key.sign(data.encode())
    print("signed_message: ", signed_message)
    signature = base64.b64encode(signed_message.signature)
    print("signature: ", signature)
    return signature

# get order parameters from config file
def get_order_execution_parameters_template(file_name):
    try:
        with open(file_name, "r") as file:
            data = json.load(file)
            return data
    except Exception as e:
        print(f"Error reading order execution parameters from config file: {e}")
        return None

def modify_order_parameters(order_parameters, field_name, field_content):
    # 修改指定字段的内容
    if field_name in order_parameters:
        order_parameters[field_name] = field_content
    else:
        print(f"Error: Field '{field_name}' not found in order parameters data.")
        return
    
def read_config(filename):
    with open(filename, 'r') as file:
        config = json.load(file)
    return config

def get_current_market_price(trading_pair):
    api_url = "https://api.backpack.exchange/api/v1/depth"
    params = {"symbol" : trading_pair}
    try:
        encoded_params = urllib.parse.urlencode(params)
        full_url = api_url + '?' + encoded_params
        req = urllib.request.Request(full_url)
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            ask_price = response_data.get("asks")
            bid_price = response_data.get("bids")
            bid_price.reverse()
            return ask_price, bid_price
    except Exception as e:
        print(f"Error: {e}")
        return None

def is_order_filled(client_id, trading_pair):
    api_url = "https://api.backpack.exchange/api/v1/order?instruction=orderQuery"
    params = {"clientId": client_id, "symbol": trading_pair}
    timestamp = int(time.time() * 1000)
    window = 5000
    api_key = read_api_key_from_file("apikey.json", "api_key")
    signature = calculate_signature(get_instructions("get_open_order"), timestamp, window, params)
    headers = {
        "X-API-KEY": api_key,
        "X-SIGNATURE": signature,
        "X-TIMESTAMP": timestamp,
        "X-WINDOW": window,
        "Content-Type": "application/json"  # 添加Content-Type请求头
    }
    try:
        request_body = json.dumps(params).encode('utf-8')
        encoded_params = urllib.parse.urlencode(params)
        full_url = api_url + '&' + encoded_params
        print("full url: ", full_url)
        req = urllib.request.Request(full_url, data=request_body, headers=headers, method="GET")
        with urllib.request.urlopen(req) as response:
            # 返回200/202则说明订单没有执行完成
            return False
            
    except urllib.error.HTTPError as e:
    # 获取错误响应的状态码和原因
        status_code = e.code
        reason = e.reason
        # 获取错误响应的内容（如果有的话）
        error_content = e.read().decode('utf-8')
        # 打印错误信息
        print(f"HTTP Error {status_code}: {reason}")
        print(f"Error Content: {error_content}")
        #返回404则说明订单已经完成
        return True

def main():
    conf = read_config("config.json")
    trading_pair = conf.get("trading_pair")
    bid_quantity = conf.get("single_order_quantity")
    ask_quantity = round(0.999 * bid_quantity, 2)
    iteration_times = conf.get("iteration_time")
    timestamp = int(time.time() * 1000)
    window = 5000
    api_key = read_api_key_from_file("apikey.json", "api_key")
    if not api_key:
        exit()
    
    bid_order_parameters = get_order_execution_parameters_template("trading_parameters_template.json")
    modify_order_parameters(bid_order_parameters, "side", "Bid")
    print("bid order parameters: ", bid_order_parameters)

    ask_order_parameters = get_order_execution_parameters_template("trading_parameters_template.json")
    modify_order_parameters(ask_order_parameters, "side", "Ask")
    print("ask order parameters: ", ask_order_parameters)

    
    for i in range(iteration_times):
        bid_client_id = i
        ask_client_id = i + 1
        # 获取当前交易对的订单薄价格
        ask_price_list, bid_price_list = get_current_market_price(trading_pair)
        # 设置买入价为当前最高的卖一价
        bid_price = ask_price_list[0][0]
        modify_order_parameters(bid_order_parameters, "clientId", bid_client_id)
        modify_order_parameters(bid_order_parameters, "price", str(bid_price))
        modify_order_parameters(bid_order_parameters, "quantity", str(bid_quantity))
        timestamp = int(time.time() * 1000)
        bid_order_signature = calculate_signature(get_instructions("execute_order"), timestamp, window, bid_order_parameters)
        # 按照卖一价，买入，执行 execute_bid_order
        bid_order_response = execute_order(api_key, bid_order_signature, timestamp, window, bid_order_parameters)
        bid_order_id = str(json.loads(bid_order_response).get("id"))
        # 每间隔1s查看订单是否全部成功成交
        while True:
            if is_order_filled(bid_client_id, trading_pair) is True:
                print(f"Bid Order: {bid_order_id} executed successfully!")
                break
            else:
                print(f"Bid Order: {bid_order_id} is still pending execution.")
            time.sleep(1)
        print("execute bid order, id = ", bid_client_id, "asset pair: ", trading_pair, "bid price: ", bid_price, "quantity: ", bid_quantity)
        
        # 按照买一价，卖出，执行 execute_ask_order
        ask_price_list, bid_price_list = get_current_market_price(trading_pair)
        ask_price = bid_price_list[0][0]
        modify_order_parameters(bid_order_parameters, "clientId", ask_client_id)
        modify_order_parameters(ask_order_parameters, "price", str(ask_price))
        modify_order_parameters(ask_order_parameters, "quantity", str(ask_quantity))
        timestamp = int(time.time() * 1000)
        ask_order_signature = calculate_signature(get_instructions("execute_order"), timestamp, window, ask_order_parameters)
        ask_order_response = execute_order(api_key, ask_order_signature, timestamp, window, ask_order_parameters)
        ask_order_id = str(json.loads(ask_order_response).get("id"))

        # 每间隔1s查看订单是否全部成功成交
        while True:
            if is_order_filled(ask_client_id, trading_pair) is True:
                print(f"Ask Order: {ask_order_id} executed successfully!")
                break
            else:
                print(f"Ask Order: {ask_order_id} is still pending execution.")
            time.sleep(1)
        
        print("execute ask order, id = ", ask_client_id, "asset pair: ", trading_pair, "ask price: ", ask_price, "quantity: ", ask_quantity)        
        print(f"Iteration {i} completed.\n")

if __name__ == "__main__":
    main()