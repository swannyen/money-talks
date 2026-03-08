import pandas as pd
from logging import Logger
from src.models.transaction import Transaction
from src.helper import (
    create_new_transaction,
    generate_holdings,
    generate_dividends,
    generate_portfolio_dividends,
    generate_portfolio_summary,
)


class MoneyTalks:
    def __init__(
        self, excel_filepath: str = "./MultiPortfolio Investment Tracker.xlsx"
    ):
        self.transactions_sheet = "Transactions"
        self.holdings_sheet = "Holdings"
        self.dividends_sheet = "Dividends"
        self.portfolio_dividends_sheet = "Portfolio Dividends"
        self.portfolio_summary_sheet = "Portfolio Summary"
        self.excel_filepath = excel_filepath
        self.logger = Logger("MoneyTalks Pipeline")
        self.transaction_df = pd.read_excel(
            self.excel_filepath, sheet_name=self.transactions_sheet
        )
        self.holdings_df = None
        self.dividends_df = None
        self.portfolio_dividend_summary = None
        self.portfolio_summary = None

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

    def get_dividends_sheet(self):
        self.dividends_df = generate_dividends(self.transaction_df)
        self.logger.info("Dividends sheet generated successfully.")
        return self.dividends_df

    def get_portfolio_dividends(self):
        if self.dividends_df is None:
            self.get_dividends_sheet()
        self.logger.info("Portfolio Dividends sheet generated successfully.")
        self.portfolio_dividend_summary = generate_portfolio_dividends(
            self.dividends_df
        )
        return self.portfolio_dividend_summary

    def get_portfolio_summary(self):
        if self.holdings_df is None:
            self.get_holdings_sheet()
        self.logger.info("Portfolio Summary generated successfully.")
        summary = generate_portfolio_summary(self.holdings_df)
        self.portfolio_summary = summary
        return summary

    def save_sheets(self):
        with pd.ExcelWriter(self.excel_filepath) as writer:
            self.transaction_df.to_excel(writer, sheet_name=self.transactions_sheet)
            if self.holdings_df is not None:
                self.holdings_df.to_excel(writer, sheet_name=self.holdings_sheet)
            if self.dividends_df is not None:
                self.dividends_df.to_excel(writer, sheet_name=self.dividends_sheet)
            if self.portfolio_dividend_summary is not None:
                self.portfolio_dividend_summary.to_excel(
                    writer, sheet_name=self.portfolio_dividends_sheet
                )
            if self.portfolio_summary is not None:
                self.portfolio_summary.to_excel(
                    writer, sheet_name=self.portfolio_summary_sheet
                )
