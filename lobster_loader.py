"""
lobster_loader.py

Loads LOBSTER message + orderbook files and merges them into a single
clean, time-aligned DataFrame.

LOBSTER file format (no headers in the raw CSVs):

Message file columns (6):
    0: Time      - seconds after midnight, decimal precision
    1: Type      - 1=new limit order, 2=partial cancel, 3=full delete,
                   4=visible execution, 5=hidden execution, 6=cross/halt,
                   7=trading halt
    2: OrderID   - unique order identifier
    3: Size      - number of shares
    4: Price     - price in dollars x 10000 (e.g. 5853300 = $585.33)
    5: Direction - 1 = buy order, -1 = sell order

Orderbook file columns (4 x n_levels), no header, no timestamp:
    For level i (1-indexed): AskPrice_i, AskSize_i, BidPrice_i, BidSize_i
    Row N of this file corresponds to the SAME event as row N of the
    message file (they are row-aligned, not time-joined).
"""

import pandas as pd
import numpy as np

MESSAGE_COLS = ["time", "type", "order_id", "size", "price", "direction"]

TYPE_LABELS = {
    1: "new_limit_order",
    2: "partial_cancel",
    3: "full_delete",
    4: "visible_execution",
    5: "hidden_execution",
    6: "cross_or_halt",
    7: "trading_halt",
}


def _orderbook_columns(n_levels: int) -> list[str]:
    """Build column names for the orderbook file given n_levels."""
    cols = []
    for i in range(1, n_levels + 1):
        cols += [f"ask_price_{i}", f"ask_size_{i}", f"bid_price_{i}", f"bid_size_{i}"]
    return cols


def load_lobster_day(
    message_path: str,
    orderbook_path: str,
    n_levels: int = 10,
    price_divisor: float = 10_000.0,
) -> pd.DataFrame:
    """
    Load one day of LOBSTER data and return a single merged, cleaned DataFrame.

    Parameters
    ----------
    message_path : path to the *_message_*.csv file
    orderbook_path : path to the *_orderbook_*.csv file
    n_levels : number of book levels present in the orderbook file (1, 5, or 10)
    price_divisor : LOBSTER stores prices as dollars * 10000 by default

    Returns
    -------
    DataFrame indexed by event number, with columns:
        time, type, type_label, order_id, size, price, direction,
        ask_price_1..n, ask_size_1..n, bid_price_1..n, bid_size_1..n
    All prices (message price + all book prices) are in actual dollars.
    """
    messages = pd.read_csv(message_path, header=None, names=MESSAGE_COLS)
    messages["price"] = messages["price"] / price_divisor
    messages["type_label"] = messages["type"].map(TYPE_LABELS)

    book_cols = _orderbook_columns(n_levels)
    book = pd.read_csv(orderbook_path, header=None, names=book_cols)

    price_cols = [c for c in book_cols if "price" in c]
    book[price_cols] = book[price_cols] / price_divisor

    # LOBSTER uses -9999999999 / 9999999999 as sentinel values when a level
    # doesn't exist (e.g. thin book). Replace with NaN so they don't corrupt
    # calculations downstream.
    book = book.replace([-9999999999 / price_divisor, 9999999999 / price_divisor], np.nan)

    if len(messages) != len(book):
        raise ValueError(
            f"Message file has {len(messages)} rows but orderbook file has "
            f"{len(book)} rows. They must be row-aligned — check you "
            f"downloaded matching message/orderbook files for the same day/level."
        )

    merged = pd.concat(
        [messages.reset_index(drop=True), book.reset_index(drop=True)], axis=1
    )
    merged.index.name = "event_num"
    return merged


def add_mid_price(df: pd.DataFrame) -> pd.DataFrame:
    """Add a mid_price column = (best bid + best ask) / 2."""
    df = df.copy()
    df["mid_price"] = (df["ask_price_1"] + df["bid_price_1"]) / 2
    df["spread"] = df["ask_price_1"] - df["bid_price_1"]
    return df


if __name__ == "__main__":
    # Quick smoke test — update these paths to your actual downloaded files
    msg_path = "data/AAPL_2012-06-21_34200000_57600000_message_10.csv"
    book_path = "data/AAPL_2012-06-21_34200000_57600000_orderbook_10.csv"

    df = load_lobster_day(msg_path, book_path, n_levels=10)
    df = add_mid_price(df)

    print(df.shape)
    print(df[["time", "type_label", "price", "direction",
               "ask_price_1", "bid_price_1", "mid_price", "spread"]].head(10))