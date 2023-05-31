#!/usr/bin/python3
# -*- coding: iso-8859-1 -*
""" Python starter bot for the Crypto Trader games """
__version__ = "1.0"

import sys

def calculate_bollinger_bands(price, window, thiness):
    # moving average
    middle_band = sum(price[-window:]) / window

    # deviation
    squared_deviations = [(x - middle_band) ** 2 for x in price[-window:]]
    variance = sum(squared_deviations) / window
    std_dev = variance ** 0.5

    # upper and lower bands
    upper_band = middle_band + (thiness * std_dev)
    lower_band = middle_band - (thiness * std_dev)

    return middle_band, upper_band, lower_band

def calculate_rsi(data, window_size):
    # the price differences
    deltas = [data[i] - data[i - 1] for i in range(1, len(data))]

    # Separate positive and negative price differences
    positive_deltas = [delta for delta in deltas if delta >= 0]
    negative_deltas = [abs(delta) for delta in deltas if delta < 0]

    # the average gains and losses
    # array[:index] = array[0], array[1], ..., array[index - 1]
    avg_gain = sum(positive_deltas[:window_size]) / window_size
    avg_loss = sum(negative_deltas[:window_size]) / window_size

    # the initial RSI value
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = 100 - (100 / (1 + rs))

    # the RSI for the remaining data points
    for i in range(window_size, len(data)):
        delta = data[i] - data[i - 1]

        # Update the average gains and losses using smoothing
        if delta >= 0:
            avg_gain = ((window_size - 1) * avg_gain + delta) / window_size
            avg_loss = ((window_size - 1) * avg_loss) / window_size
        else:
            avg_gain = ((window_size - 1) * avg_gain) / window_size
            avg_loss = ((window_size - 1) * avg_loss + abs(delta)) / window_size

        # Update the RSI value
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))

    return rsi

class Bot:
    def __init__(self):
        self.botState = BotState()

    def run(self):
        while True:
            reading = input()
            if len(reading) == 0:
                continue
            self.parse(reading)

# RSI
# MACD ?

    def parse(self, info: str):
        tmp = info.split(" ")
        if tmp[0] == "settings":
            self.botState.update_settings(tmp[1], tmp[2])
        if tmp[0] == "update":
            if tmp[1] == "game":
                self.botState.update_game(tmp[2], tmp[3])
        if tmp[0] == "action":
            # This won't work every time, but it works sometimes!
            dollars = self.botState.stacks["USDT"]
            current_closing_price = self.botState.charts["USDT_BTC"].closes[-1]
            affordable = dollars / current_closing_price
            bitcoin = self.botState.stacks["BTC"]
            price = self.botState.charts["USDT_BTC"].closes


            if dollars < 10 and bitcoin < 0.0001:
                print("no_moves because we are broke", file=sys.stderr)
                print("no_moves", flush=True)

            """ implement bollinger band """
            middle_band, upper_band, lower_band = calculate_bollinger_bands(price, 20, 2)
            # print(f'My stacks are {dollars}, bitcoin = {bitcoin}. The current closing price is {current_closing_price}. So I can afford {affordable} = {0.4 * affordable}', file=sys.stderr)
            print(f'upper_band / price / lower_band = {round(lower_band)}/{price[-1]}/{round(upper_band)}', file=sys.stderr)
            if price[-1] > upper_band and bitcoin / 10 > 0.0001:
                print(f'bollinger band sell USDT_BTC {bitcoin / 10}', file=sys.stderr)
                print(f'sell USDT_BTC {bitcoin / 10}', flush=True)
                return
            elif price[-1] < lower_band and 0.2 * affordable > 0.0001:
                print(f'bollinger band buy USDT_BTC {0.2 * affordable}', file=sys.stderr)
                print(f'buy USDT_BTC {0.2 * affordable}', flush=True)
                return

            """ implement RSI """
            rsi = calculate_rsi(price, 14)
            # print(f'My stacks are {dollars}, bitcoin = {bitcoin}. The current closing price is {current_closing_price}. So I can afford {affordable} = {0.4 * affordable}', file=sys.stderr)
            print(f'rsi = {rsi}', file=sys.stderr)
            if rsi > 70 and bitcoin / 5 > 0.0001:
                print(f'RSI sell USDT_BTC {bitcoin / 5}', file=sys.stderr)
                print(f'sell USDT_BTC {bitcoin / 5}', flush=True)
                return
            elif rsi < 30 and 0.4 * affordable > 0.0001:
                print(f'RSI buy USDT_BTC {0.4 * affordable}', file=sys.stderr)
                print(f'buy USDT_BTC {0.4 * affordable}', flush=True)
                return
            print("no_moves because rsi and bollinger band are not triggered", file=sys.stderr)
            print("no_moves", flush=True)



class Candle:
    def __init__(self, format, intel):
        tmp = intel.split(",")
        for (i, key) in enumerate(format):
            value = tmp[i]
            if key == "pair":
                self.pair = value
            if key == "date":
                self.date = int(value)
            if key == "high":
                self.high = float(value)
            if key == "low":
                self.low = float(value)
            if key == "open":
                self.open = float(value)
            if key == "close":
                self.close = float(value)
            if key == "volume":
                self.volume = float(value)

    def __repr__(self):
        return str(self.pair) + str(self.date) + str(self.close) + str(self.volume)


class Chart:
    def __init__(self):
        self.dates = []
        self.opens = []
        self.highs = []
        self.lows = []
        self.closes = []
        self.volumes = []
        self.indicators = {}

    def add_candle(self, candle: Candle):
        self.dates.append(candle.date)
        self.opens.append(candle.open)
        self.highs.append(candle.high)
        self.lows.append(candle.low)
        self.closes.append(candle.close)
        self.volumes.append(candle.volume)


class BotState:
    def __init__(self):
        self.timeBank = 0
        self.maxTimeBank = 0
        self.timePerMove = 1
        self.candleInterval = 1
        self.candleFormat = []
        self.candlesTotal = 0
        self.candlesGiven = 0
        self.initialStack = 0
        self.transactionFee = 0.1
        self.date = 0
        self.stacks = dict()
        self.charts = dict()

    def update_chart(self, pair: str, new_candle_str: str):
        if not (pair in self.charts):
            self.charts[pair] = Chart()
        new_candle_obj = Candle(self.candleFormat, new_candle_str)
        self.charts[pair].add_candle(new_candle_obj)

    def update_stack(self, key: str, value: float):
        self.stacks[key] = value

    def update_settings(self, key: str, value: str):
        if key == "timebank":
            self.maxTimeBank = int(value)
            self.timeBank = int(value)
        if key == "time_per_move":
            self.timePerMove = int(value)
        if key == "candle_interval":
            self.candleInterval = int(value)
        if key == "candle_format":
            self.candleFormat = value.split(",")
        if key == "candles_total":
            self.candlesTotal = int(value)
        if key == "candles_given":
            self.candlesGiven = int(value)
        if key == "initial_stack":
            self.initialStack = int(value)
        if key == "transaction_fee_percent":
            self.transactionFee = float(value)

    def update_game(self, key: str, value: str):
        if key == "next_candles":
            new_candles = value.split(";")
            self.date = int(new_candles[0].split(",")[1])
            for candle_str in new_candles:
                candle_infos = candle_str.strip().split(",")
                self.update_chart(candle_infos[0], candle_str)
        if key == "stacks":
            new_stacks = value.split(",")
            for stack_str in new_stacks:
                stack_infos = stack_str.strip().split(":")
                self.update_stack(stack_infos[0], float(stack_infos[1]))


if __name__ == "__main__":
    mybot = Bot()
    mybot.run()
