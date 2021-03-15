from aggregate_transactions import process_file


def test_simple_tx_history():
    filepath = "test_transaction_simple.csv"
    output_df = process_file(filepath)
    assert output_df["PROCEEDS"].item() == (700.02 - 602.02)


# TODO create WAY more tests around using differnt tokens
# Also consider testing lower level functions so that we
# can easier parametrize the data