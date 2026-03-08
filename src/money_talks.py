import pandas as pd
from logging import Logger
from src.models.transaction import Transaction
from src.helper import create_new_transaction, generate_holdings


class MoneyTalks:
    def __init__(
        self, excel_filepath: str = "./MultiPortfolio Investment Tracker.xlsx"
    ):
        self.transactions_sheet = "Transactions"
        self.holdings_sheet = "Holdings"
        self.excel_filepath = excel_filepath
        self.logger = Logger("MoneyTalks Pipeline")
        self.transaction_df = pd.read_excel(
            self.excel_filepath, sheet_name=self.transactions_sheet
        )
        self.holdings_df = None

    def add_transaction(self, transaction: Transaction) -> None:
        try:
            new_transaction_df = create_new_transaction(transaction)
            updated_transactions = pd.concat(
                [self.transaction_df, new_transaction_df], ignore_index=True
            )
            self.transaction_df = updated_transactions
            self.logger.info(f"Transaction added successfully: {transaction}")
        except ValueError as error:
            self.logger.error(f"Error creating transaction: {error}")
            raise error

    def get_holdings_sheet(self):
        self.holdings_df = generate_holdings(self.transaction_df)
        self.logger.info("Holdings sheet generated successfully.")
        return self.holdings_df
    
    def save_sheets(self):
        with pd.ExcelWriter(self.excel_filepath) as writer:
            self.transaction_df.to_excel(writer, sheet_name=self.transactions_sheet)
            if self.holdings_df is not None:
                self.holdings_df.to_excel(writer, sheet_name=self.holdings_sheet)

    def get_portfolio_summary(self):
        holdings_df = self.get_holdings_sheet()
        summary = holdings_df.groupby("Portfolio").agg(
            {
                "Current Value (base)": "sum",
                "Unrealised P/L (base)": "sum",
            }
        )
        return summary
