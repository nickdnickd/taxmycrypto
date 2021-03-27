import pytest
import pandas as pd
import datetime
from aggregate_transactions import (
    Strategy,
    process_file,
    calculate_proceeds,
    CoinbaseTransaction,
    TransactionType,
)


@pytest.fixture(scope="session")
def test_start_time():
    return datetime.datetime.now()


@pytest.fixture
def simple_buy_df(test_start_time):
    buy_time = test_start_time - datetime.timedelta(days=30)
    buy_tx = CoinbaseTransaction(
        timestamp=buy_time,
        transaction_type=TransactionType.BUY,
        asset="BTC",
        usd_fees=1.00,
        quantity_transacted=1.0,
        usd_spot_price_at_transaction=10.00,
        usd_subtotal=10.00,
        usd_total=11.00,
    )
    # Create the dataframe and set the columns
    buy_df = pd.DataFrame([buy_tx])

    buy_df.columns = [
        CoinbaseTransaction.TO_COINBASE_COLS.get(column, column)
        for column in buy_df.columns
    ]

    return buy_df


@pytest.fixture
def simple_sell_df(test_start_time):
    sell_time = test_start_time - datetime.timedelta(days=15)
    sell_tx = CoinbaseTransaction(
        timestamp=sell_time,
        transaction_type=TransactionType.SELL,
        asset="BTC",
        usd_fees=1.00,
        quantity_transacted=1.0,
        usd_spot_price_at_transaction=10.00,
        usd_subtotal=10.00,
        usd_total=11.00,
    )

    sell_df = pd.DataFrame([sell_tx])
    sell_df.columns = [
        CoinbaseTransaction.TO_COINBASE_COLS.get(column, column)
        for column in sell_df.columns
    ]
    return sell_df


def test_simple_tx_history():
    filepath = "test_transaction_simple.csv"
    output_df = process_file(filepath)
    assert output_df["PROCEEDS"].item() == (700.02 - 602.02)


# TODO create WAY more tests around using differnt tokens
# Also consider testing lower level functions so that we
# can easier parametrize the data
# Also test "next year" usability


def test_simple_buy_sell(simple_buy_df, simple_sell_df):
    """Given one simple buy transaction and sell
    transaction at the same price with the same qantity,
    the proceeds would equate to just the fees on the buy
    transaction"""

    print("simple buy df:\n")
    print(simple_buy_df.to_string())
    print("simple sell df:\n")
    print(simple_sell_df.to_string())

    output_df = calculate_proceeds(
        simple_buy_df, simple_sell_df, strategy=Strategy.HIFO
    )

    print(output_df.to_string())
    assert output_df["PROCEEDS"][0] == -1.0
