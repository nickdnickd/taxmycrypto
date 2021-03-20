# Single Crypto Tax Aggregator

This script reads the CSV file produced by Coinbase in 2020 and shows how one could calculate proceeds using past purchases as cost basis.

This is not tax or financial advice. Please seek guidance from your financial advisor.

## Setup

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

