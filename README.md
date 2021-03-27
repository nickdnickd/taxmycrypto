# Simple Crypto Tax Aggregator

This script reads the CSV file produced by Coinbase in 2020 and shows how one could calculate proceeds using past purchases as cost basis.

This is not tax or financial advice. Please seek guidance from your financial advisor.

### UPDATE
TurboTax has now pulled Coinbase from the list of CSV providers. In order to proceed, we have two options: 
- On the safe and reccomended side, you may manually enter the output from this csv into TurboTax
- On the not-a-great-idea side, select any provider and upload this CSV since it matches the format of the parters.
## What this does not yet support
- Multi-Exchange cost basis calculation
  - Basically if you want to minimize your taxes and you've transferred between exchanges this will raise an error
- Conversions
  - I don't yet calculate cost basis for conversions
- Multi-year cost basis
  - Almost there with saving what was used for one year's cost basis

## What this script does support
- Multiple different currencies
  - This script will separate out bitcoin, litecoin, ethereum, etc
- Different cost basis strategies
  - FIFO, LIFO and HIFO
- Producing a CSV that calculates 2020 proceeds to be submitted to TurboTax
  - Modeled off a CSV produced by Robinhood

## Setup

### Prerequisites
- Python3
- Knowledge of how to use the terminal or command prompt
- CSV file export from Coinbase

### Instructions

Create your virtual environment

`python3 -m venv venv`

Install the dependencies

`pip install -r requirements.txt`


Run the aggregator on your Coinbase 2020 transaction CSV

`python aggregate_transactions.py ./coinbase_file.csv`

You will see two files produced:

- `./coinbase_file_proceeds.csv`
  - This is the file that can be uploaded.
- `./coinbase_file_cost_basis_source.csv`
  - Keep this to know which crypto you used for cost basis.

Command help

`python aggregate_transactions.py -h`

