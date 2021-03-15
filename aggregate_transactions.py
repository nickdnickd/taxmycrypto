"""The goal of this script is to calculate the 
   proceeds from crypto transactions from 2020, given a list ot transactions.
   
   This website was helpful
   https://cryptotrader.tax/blog/the-traders-guide-to-cryptocurrency-taxes
"""

from typing import Tuple
from dataclasses import dataclass
from typing import Optional
import logging
import argparse
import pandas as pd
from enum import Enum
from datetime import date, datetime


class Strategy(Enum):
    LIFO = "LIFO"  # Last in, First out
    FIFO = "FIFO"  # First in, First out
    HIFO = "HIFO"  # Highest in, First out

    def __str__(self):
        """Required to use in argparse"""
        return self.value


class TransactionType(Enum):
    BUY = "Buy"
    SELL = "Sell"


class AssetType(Enum):
    ETH = "ETH"  # Ethereum
    BTC = "BTC"  # Bitcoin
    BCH = "BCH"  # Bitcoin Cash
    XLM = "XLM"  # Stellar Lumens
    LTC = "LTC"  # Litecoin


@dataclass
class CryptoProceeds:
    """TODO make more use of this data structure"""

    asset_name: AssetType
    received_date: date
    cost_basis_usd: float
    date_sold: date
    proceeds_usd: float

    csv_header: Tuple[str] = (
        "ASSET NAME",
        "RECEIVED DATE",
        "COST BASIS(USD)",
        "DATE SOLD",
        "PROCEEDS",
    )


@dataclass
class CoinbaseTransaction:
    """Class for keeping track of transactions."""

    timestamp: datetime
    transaction_type: TransactionType
    asset: AssetType
    quantity_transacted: float
    usd_spot_price_at_transaction: float
    usd_subtotal: float
    usd_total: float  # inclusive of fees
    usd_fees: float

    # How many of this asset did we attribute to profit
    quantity_attributed_to_profit: float = 0.0

    def cost_basis_usd(self, quantity_considered) -> float:
        """Fees included amount spend
        The reason we don't do subtotal is because part of the quantity

        NOTE ask about portion of fees. Like if I attribute a portion of my buy
        transcation, do I split up the fees for cost basis?"""

        return quantity_considered * (
            self.usd_spot_price_at_transaction
            + self.usd_fees / self.quantity_transacted
        )

    @classmethod
    def from_dict(cls, df):
        return cls(
            timestamp=df["Timestamp"],
            transaction_type=df["Transaction Type"],
            asset=df["Asset"],
            quantity_transacted=df["Quantity Transacted"],
            usd_spot_price_at_transaction=df["USD Spot Price at Transaction"],
            usd_subtotal=df["USD Subtotal"],
            usd_total=df["USD Total (inclusive of fees)"],
            usd_fees=df["USD Fees"],
        )


def read_csv(csv_path: str) -> Optional[pd.DataFrame]:
    """Return a dataframe for processing, ensure we process the correct datetime"""

    with open(csv_path) as csvfile:
        return pd.read_csv(csvfile, header=3, parse_dates=[0])


def strategy_to_sort_values(purchase_df: pd.DataFrame, strategy: Strategy):

    if strategy == Strategy.HIFO:
        return purchase_df.sort_values("USD Spot Price at Transaction", ascending=False)
    elif strategy == Strategy.LIFO:
        return purchase_df.sort_values("Timestamp", ascending=False)
    elif strategy == Strategy.FIFO:
        return purchase_df.sort_values("Timestamp", ascending=True)


def get_cost_basis_source(purchase_df: pd.DataFrame, strategy: Strategy):
    try:
        highest_row = strategy_to_sort_values(
            purchase_df[
                (
                    purchase_df["quantity_attributed_to_profit"]
                    < purchase_df["Quantity Transacted"]
                )
            ],
            strategy,
        ).head(n=1)

        index = highest_row.index.values[0]
        highest_row_dict = highest_row.to_dict(orient="records")[0]

    except IndexError:
        # This means that we couldn't find a buy transaction left
        # To attribute to this profit
        raise Exception("No transactions left that have quantity left over")

    return index, CoinbaseTransaction.from_dict(highest_row_dict)


def get_quantity_to_attribute(crypto_left, crypto_bought, crypto_used_already):

    crypto_attributable = crypto_bought - crypto_used_already
    if crypto_attributable > crypto_left:
        # If we only need part of the crypto to cover
        # just use that
        return crypto_left

    return crypto_attributable


def calculate_proceeds(
    sell_df: pd.DataFrame, buy_df: pd.DataFrame, strategy: Strategy
) -> pd.DataFrame:
    """Highest In, First Out. Show minimum profits possible.
    Mark historical transactactions so that this script can be used later."""
    output_df = pd.DataFrame(columns=CryptoProceeds.csv_header)
    buy_df.insert(0, "quantity_attributed_to_profit", 0)

    logging.debug(buy_df.to_string())

    for _, row in sell_df.iterrows():
        logging.info(
            f"taxable event: sold {row['Quantity Transacted']} crypto at {row['USD Subtotal']}"
        )

        crypto_to_cover = row["Quantity Transacted"]
        same_type_bought = buy_df.loc[buy_df["Asset"] == row["Asset"]]

        while crypto_to_cover > 0.0:

            tx_idx, highest_asset_tx = get_cost_basis_source(same_type_bought, strategy)
            # what crypto hasn't been used for profit
            crypto_to_attribute = get_quantity_to_attribute(
                crypto_to_cover,
                float(highest_asset_tx.quantity_transacted),
                float(highest_asset_tx.quantity_attributed_to_profit),
            )

            # Count this quantity of crypto towards profit

            same_type_bought.loc[tx_idx, "quantity_attributed_to_profit"] = (
                crypto_to_attribute + highest_asset_tx.quantity_attributed_to_profit
            )

            asset_name = highest_asset_tx.asset
            received_date = highest_asset_tx.timestamp.date()

            cost_basis = highest_asset_tx.cost_basis_usd(crypto_to_attribute)
            date_sold = row["Timestamp"].date()
            # NOTE use only the percentage of the current subtotal
            # that we are attributing to a purchase, is this correct?
            proceeds = (
                row["USD Subtotal"] * crypto_to_attribute / row["Quantity Transacted"]
                - cost_basis
            )
            output_df = output_df.append(
                pd.DataFrame(
                    [[asset_name, received_date, cost_basis, date_sold, proceeds]],
                    columns=CryptoProceeds.csv_header,
                ),
                ignore_index=True,
            )

            crypto_to_cover -= crypto_to_attribute
            logging.debug(f"crypto left to cover: {crypto_to_cover}")

    return output_df


def get_date_mask_for_year(tx_df: pd.DataFrame, year: int = 2020):
    date_mask = (
        tx_df["Timestamp"]
        >= pd.to_datetime(datetime(year=year, month=1, day=1), utc=True)
    ) & (
        tx_df["Timestamp"]
        < pd.to_datetime(
            datetime(year=year + 1, month=1, day=1, hour=0, minute=0), utc=True
        )
    )
    return date_mask


def summarize_total_profit_loss(proceeds_df: pd.DataFrame):
    total_profit = 0
    total_loss = 0
    for _, row in proceeds_df.iterrows():
        if row["PROCEEDS"] >= 0.0:
            total_profit += row["PROCEEDS"]
        else:
            total_loss += row["PROCEEDS"]

    logging.info(f"total profit {total_profit}")
    logging.info(f"total loss {total_loss}")


def process_file(coinbase_filepath: str):
    tx_df = read_csv(coinbase_filepath)

    # Get a copy of all sell transactions in 2020
    # TODO support all taxable events
    date_mask = get_date_mask_for_year(tx_df, 2020)
    sell_df = tx_df.loc[
        (tx_df["Transaction Type"] == TransactionType.SELL.value) & date_mask
    ]

    # Create a copy of all buy transactions (including before 2020)
    # This will form the pool of Cost basis for a sell transaction
    buy_df = tx_df.loc[(tx_df["Transaction Type"] == TransactionType.BUY.value)]

    output_df = calculate_proceeds(sell_df, buy_df, Strategy.HIFO)

    summarize_total_profit_loss(output_df)

    # TODO actually write the proceeds to a csv,
    # TODO record which input transactions were used for cost basis

    return output_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process a 2020 coinbase file for 2020 turbo tax.\n"
        "Note: this script does not yet cover conversions."
    )
    parser.add_argument("coinbase_file", help="the path to the coinbase csv file")

    # TODO make year and coin strategy parameters
    # default year idea: this year minus one

    args = parser.parse_args()

    process_file(args.coinbase_file)
