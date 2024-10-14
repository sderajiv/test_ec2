
'''rsi is greater than 70 and confirmation of two candles are green
    10 points jump after hiting the target, after target, sl will be the target
'''

'''in this i want when target reaches dont sell just wait for the next tpoint value if the t point value is 10 then wait to reach market 10 points more after the first 10 points if after target market goes back then sellit at the prev 10 points like if it buy at 210 then wait for 220 when 220 reaches wait for 230 if from 2340 it comes back then sell it 5 points back at 225 or if after 220 it falls back sell it at 5 points back'''

import pandas as pd
import time, datetime, pytz
import csv
import logging
# from pymongo import MongoClient
# import numpy as np
import json
import os
from dhanhq import dhanhq
import requests

# Dhan credentials

#1101219115
#1102133554

client_id = ['1106821', '12133554', '1101115']
access_token = [
    'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.', 
    'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.',
    'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.'
]

# Loop through each client_id and access_token pair and initialize dhanhq
for i in range(len(client_id)):
    # Select the current client_id and corresponding access_token
    current_client_id = client_id[i]
    current_access_token = access_token[i]

    # Initialize the dhanhq connection for the current client and access token
    dhan = dhanhq(current_client_id, current_access_token)


# Path to the CSV files
csv_file = 'merged_data_2min.csv'

# Initialize the state variable
state = 'waiting_for_yes'
yes_order_executed = False
direction_one_count = 0

# Flags to track buy and sell orders
buy_order_placed = False
sell_order_placed = False

# Variables for trailing stop-loss
buy_order_close_value = None
highest_close_since_buy = None
stop_loss_value = None
first_target_price = None  # New variable to store the first target price
points_reached = False
first_target_reached = False  # New flag to track first target achievement


def fetch_security_id():
    url = "http://15.206.82.49:8001/get_fetched_data"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            security_id = data.get('security_id')
            quantity = data.get('quantity', 'Not Provided')
            points = data.get('points', 'Points not given')
            tpoints = data.get('tpoints', 'Trailing Points not given')
            print(f"Fetched security_id: {security_id}")
            print(f"Fetched Quantity: {quantity}")
            print(f"Fetched Points: {points}")
            print(f"Fetched trailing Points: {tpoints}")
            return security_id, quantity, float(points), float(tpoints)
        else:
            print(f"Failed to fetch data, status code: {response.status_code}")
            return None, None, None, None
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return None, None, None, None

# Function to place a Buy order
def place_buy_order(security_id, quantity, close_val, current_timestamp):
    global buy_order_placed, buy_order_close_value, highest_close_since_buy, stop_loss_value, points_reached, first_target_reached
    print("Placing a Buy order...")
    order_response = dhan.place_order(
        security_id=security_id,  
        exchange_segment=dhan.NSE_FNO,
        transaction_type=dhan.BUY,
        quantity=quantity,
        order_type=dhan.MARKET,
        product_type=dhan.INTRA,
        price=0
    )
    print(order_response)
    buy_order_placed = True
    buy_order_close_value = close_val
    highest_close_since_buy = close_val
    stop_loss_value = highest_close_since_buy - tpoints
    points_reached = False  # Reset points reached flag
    first_target_reached = False  # Reset target achievement flag
    write_log_entry(current_timestamp, f"Buy order placed at {close_val}", f"Buy order placed at {close_val}. Initial Stop Loss set to: {stop_loss_value}")


def place_sell_order(security_id, quantity, close_val, current_timestamp):
    global sell_order_placed, buy_order_placed, first_target_reached
    print("Placing a Sell order...")
    order_response = dhan.place_order(
        security_id=security_id,
        exchange_segment=dhan.NSE_FNO,
        transaction_type=dhan.SELL,
        quantity=quantity,
        order_type=dhan.MARKET,
        product_type=dhan.INTRA,
        price=0
    )
    print(order_response)
    sell_order_placed = True
    buy_order_placed = False
    first_target_reached = False  # Reset target flag after sell

    write_log_entry(current_timestamp, f"Sell order placed at {close_val}", f"Sell order placed at {close_val}. Stop Loss was: {stop_loss_value}")
    write_log_entry(current_timestamp, 'INFO', f"Order Response: {order_response}")
    write_log_entry(current_timestamp, 'INFO', "Sell order placed due to stop loss or red candle")



    # else:
    #     if not buy_order_placed:
    #         reason = "Buy order has not been placed."
    #     elif sell_order_placed:
    #         reason = "Sell order has already been placed."
    #     write_log_entry(current_timestamp, 'WARNING', f"Attempted to place Sell order, but conditions were not met. Reason: {reason}")


logging.basicConfig(
    filename='trading_logs_CE_2min_10_points_jump.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# Open the log file
log_file = 'trading_logs_CE_2min_10_points_jump.csv'
csv_log_file = open(log_file, mode='a', newline='')
csv_writer = csv.writer(csv_log_file)
csv_writer.writerow(['Timestamp', 'Level', 'Message'])  # Write the header row


import pytz
from datetime import datetime

import pytz
from datetime import datetime

# Assuming csv_writer and csv_log_file are already defined
def write_log_entry(timestamp, level, message):
    india_timezone = pytz.timezone('Asia/Kolkata')
    current_time_ist = datetime.now(india_timezone)
    timestamp_str = current_time_ist.strftime('%Y-%m-%d %H:%M:%S')
    csv_writer.writerow([timestamp_str, level, message])
    csv_log_file.flush()
    logging.info(f"{timestamp_str} - {level}: {message}")

# Function to read CSV files and log the content
def read_csv_file(file_path):
    try:
        print(f"Reading CSV file: {file_path}")
        df2 = pd.read_csv(file_path)
        print(f"CSV file read successfully. Columns: {df2.columns}")
        return df2
    except pd.errors.EmptyDataError:
        print(f"Error reading {file_path}: No data")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return pd.DataFrame()

while True:
    try:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

        # Re-read the CSV files to get the latest data
        df2 = read_csv_file(csv_file)
        security_id, quantity, points, tpoints = fetch_security_id()

        if security_id is None or quantity is None or points is None or tpoints is None:
            print("Invalid data fetched. Skipping this iteration.")
            time.sleep(1)
            continue

        # Read the last rows again to ensure they are updated
        last_row2 = df2.iloc[-1]

        # Read the second last row for supertrend comparison
        if len(df2) > 1:
            prev_row3 = df2.iloc[-2]
        else:
            prev_row3 = last_row2  # Fallback to the last row if there's no previous row

        # Extract scalar values from the last row for comparison
        close_value = float(last_row2['close'])
        mark_value = str(last_row2['mark']).strip().lower()
        supertrend_value = float(last_row2['supertrend'])
        direction_value = int(last_row2['direction'])
        rsi_value = int(last_row2['rsi'])
        prev_rsi_value = int(prev_row3['rsi'])
        prev_supertrend_value = float(prev_row3['supertrend'])

        # Log the current values for debugging
        write_log_entry(timestamp, 'INFO', f"State: {state}")
        write_log_entry(timestamp, 'INFO', f"Values: close={close_value}, mark={mark_value}, supertrend={supertrend_value}, direction={direction_value}")
        write_log_entry(timestamp, 'INFO', f"Previous supertrend: {prev_supertrend_value}")

        if direction_value == 1:
            direction_one_count += 1
        else:
            direction_one_count = 0

        condition_met = (
            state == 'waiting_for_yes' and
            mark_value == 'green' and
            direction_one_count > 2 and
            (supertrend_value > prev_supertrend_value) and
            ((supertrend_value - prev_supertrend_value) > 1) and
            ((rsi_value and prev_rsi_value) >= 70 )
        )

        if condition_met and not buy_order_placed:
            write_log_entry(timestamp, 'INFO', "Condition met for placing buy order")
            place_buy_order(security_id, quantity, close_value, timestamp)
            
            state = 'waiting_for_action'
            write_log_entry(timestamp, 'INFO', "Buy order placed. Waiting for action...")
            yes_order_executed = True
        
        # State handling logic within the loop
        elif state == 'waiting_for_action' and buy_order_placed:
            write_log_entry(timestamp, 'INFO', "State: Waiting for action")
            
            # If price reaches the first target, enable trailing stop-loss
            if not first_target_reached and close_value - buy_order_close_value >= points:
                first_target_reached = True
                first_target_price = close_value  # Set first target price when the target is hit
                highest_close_since_buy = close_value
                stop_loss_value = first_target_price  # Initial stop loss is set to first target price
                write_log_entry(timestamp, 'INFO', f"First target reached at {close_value}. Stop loss set to first target price: {stop_loss_value}.")

            # If first target reached, apply trailing stop-loss
            if first_target_reached:
                # If the close price goes above the highest close since the first target was reached
                if close_value > highest_close_since_buy:
                    highest_close_since_buy = close_value
                    stop_loss_value = max(first_target_price, highest_close_since_buy - tpoints)  # Ensure stop loss doesn't go below first target price
                    write_log_entry(timestamp, 'INFO', f"New highest close at {close_value}. Stop loss updated to {stop_loss_value}.")

                # If the price falls below the trailing stop-loss, execute sell
                elif close_value <= stop_loss_value:
                    write_log_entry(timestamp, 'INFO', f"Price dropped to {close_value}, below stop loss {stop_loss_value}. Placing sell order.")
                    place_sell_order(security_id, quantity, close_value, timestamp)
                    state = 'waiting_for_red'  # Move to the next state after sell
                    write_log_entry(timestamp, 'INFO', "Sell order placed due to trailing stop loss.")

            # If the mark turns red before reaching the first target, sell immediately
            elif not first_target_reached and mark_value == 'red':
                write_log_entry(timestamp, 'INFO', "Mark is red before first target. Placing sell order immediately.")
                place_sell_order(security_id, quantity, close_value, timestamp)
                state = 'waiting_for_red'  # Switch to the next state
                write_log_entry(timestamp, 'INFO', "Sell order placed due to red mark.")

            
        elif state == 'waiting_for_red':
            write_log_entry(timestamp, 'INFO', "State: Waiting for red")
            if mark_value == 'red' and sell_order_placed:
                write_log_entry(timestamp, 'INFO', "Detected red. Changing state to waiting for yes")
                state = 'waiting_for_yes'
            else:
                write_log_entry(timestamp, 'INFO', "No red detected yet, still waiting")

        else:
            write_log_entry(timestamp, 'ERROR', f"Invalid state: {state}")
            print(f"Invalid state: {state}")

    except Exception as e:
        write_log_entry(timestamp, 'ERROR', f"An error occurred: {str(e)}")
        print(f"An error occurred: {str(e)}")

    # Sleep for a while before checking again
    time.sleep(1)
