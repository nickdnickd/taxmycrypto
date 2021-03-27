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

    return buy_tx.to_df_row()


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

    return sell_tx.to_df_row()


@pytest.fixture
def multi_asset_sell_df(simple_sell_df):
    """Create a mixed df of assets"""
    new_sell_df = simple_sell_df.copy()
    new_sell_df.at[0, "Asset"] = "ETH"
    return pd.concat([simple_sell_df, new_sell_df], ignore_index=True)


@pytest.fixture
def multi_asset_buy_df(simple_buy_df):
    """Create a mixed df of assets"""
    new_buy_df = simple_buy_df.copy()
    new_buy_df.at[0, "Asset"] = "ETH"
    return pd.concat([simple_buy_df, new_buy_df], ignore_index=True)


def test_simple_tx_history():
    filepath = "test_transaction_simple.csv"
    output_df = process_file(filepath)
    assert output_df["PROCEEDS"].item() == (700.02 - 602.02)


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
        simple_sell_df, simple_buy_df, strategy=Strategy.HIFO
    )

    print(output_df.to_string())
    assert output_df["PROCEEDS"][0] == -1.0
    assert simple_buy_df["quantity_attributed_to_profit"][0] == 1.0


def test_only_sell(simple_buy_df, simple_sell_df):
    """In this scenario, we don't have enough buy
    to attribute to the sale.
    Say for example that somebody had some old ethereum
    on a hardware wallet, transfers it to an exchagne and sells it.
    In this scenario, the exchange is not aware of any asset to
    cover the cost and therefore.
    """
    simple_buy_df = simple_buy_df.drop(0)
    print("simple buy df:\n")
    print(simple_buy_df.to_string())

    with pytest.raises(Exception):
        calculate_proceeds(simple_sell_df, simple_buy_df, strategy=Strategy.HIFO)


def test_multi_asset_type(multi_asset_buy_df, multi_asset_sell_df):

    print("multi asset sell and buy dfs:\n")
    print(multi_asset_sell_df.to_string())
    print(multi_asset_buy_df.to_string())

    output_df = calculate_proceeds(
        multi_asset_buy_df, multi_asset_sell_df, strategy=Strategy.HIFO
    )

    print("multi output df:\n")
    print(output_df.to_string())
    assert all(output_df[output_df["ASSET NAME"] == "BTC"].PROCEEDS == -1.0)

    assert all(output_df[output_df["ASSET NAME"] == "ETH"].PROCEEDS == -1.0)


def test_multi_currency(simple_buy_df, simple_sell_df):
    """In this scenario, we don't have enough buy
    to attribute to the sale.
    Say for example that somebody had some old ethereum
    on a hardware wallet, transfers it to an exchagne and sells it.
    In this scenario, the exchange is not aware of any asset to
    cover the cost and therefore.
    """
    simple_buy_df = simple_buy_df.drop(0)
    print("simple buy df:\n")
    print(simple_buy_df.to_string())

    with pytest.raises(Exception):
        calculate_proceeds(simple_sell_df, simple_buy_df, strategy=Strategy.HIFO)
