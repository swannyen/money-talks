import pandas as pd
from logging import Logger
from src.models.transaction import Transaction
from src.helper import (
    create_new_transaction,
    generate_holdings,
    generate_dividends,
    generate_portfolio_dividends,
    generate_portfolio_summary,
    generate_dividend_recovery_sheet,
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
        self.dividend_recovery_sheet = "Dividend Recovery"
        self.excel_filepath = excel_filepath
        self.logger = Logger("MoneyTalks Pipeline")
        self.transaction_df = pd.read_excel(
            self.excel_filepath, sheet_name=self.transactions_sheet
        )
        self.holdings_df = None
        self.dividends_df = None
        self.portfolio_dividend_summary = None
        self.portfolio_summary = None
        self.recovery_summary = None

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
        summary = generate_portfolio_summary(self.holdings_df)
        self.logger.info("Portfolio Summary generated successfully.")
        self.portfolio_summary = summary
        return summary

    def get_dividend_recovery_summary(self):
        if self.holdings_df is None:
            self.get_holdings_sheet()
        if self.dividends_df is None:
            self.get_dividends_sheet()
        recovery_summary = generate_dividend_recovery_sheet(
            self.holdings_df, self.dividends_df
        )
        self.recovery_summary = recovery_summary
        self.logger.info("Dividend Recovery sheet generated successfully.")
        return recovery_summary

    def save_sheets(self):
        sheet_df_dict = {
            self.transactions_sheet: self.transaction_df,
            self.holdings_sheet: self.holdings_df,
            self.dividends_sheet: self.dividends_df,
            self.portfolio_dividends_sheet: self.portfolio_dividend_summary,
            self.portfolio_summary_sheet: self.portfolio_summary,
            self.dividend_recovery_sheet: self.recovery_summary,
        }
        with pd.ExcelWriter(self.excel_filepath) as writer:
            for sheet_name, df in sheet_df_dict.items():
                if df is not None:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        self.logger.info(f"All sheets saved successfully to {self.excel_filepath}.")
