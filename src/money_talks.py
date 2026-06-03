import logging

import pandas as pd

from src.helper import (
    create_new_transaction,
    generate_dividend_recovery_sheet,
    generate_dividends,
    generate_holdings,
    generate_portfolio_dividends,
    generate_portfolio_summary,
    generate_realised_pl_sheet,
    generate_total_return_sheet,
)
from src.models.transaction import Transaction


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
        self.realised_pl_sheet = "Realised PL"
        self.total_return_sheet = "Total Return"
        self.excel_filepath = excel_filepath
        self.logger = logging.getLogger("MoneyTalks Pipeline")
        self.transaction_df = pd.read_excel(
            self.excel_filepath, sheet_name=self.transactions_sheet
        )
        self.holdings_df = None
        self.dividends_df = None
        self.portfolio_dividend_summary = None
        self.portfolio_summary = None
        self.recovery_summary = None
        self.realised_pl = None
        self.total_return = None

    def add_transaction(self, transaction: Transaction) -> None:
        try:
            new_transaction_df = create_new_transaction(transaction)
            updated_transactions = pd.concat(
                [self.transaction_df, new_transaction_df], ignore_index=True
            )
            self.transaction_df = updated_transactions
            self.logger.info("Transaction added successfully: %s", transaction)
        except ValueError as error:
            self.logger.error("Error creating transaction: %s", error)
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

    def get_realised_pl_sheet(self):
        if self.transaction_df is None:
            raise ValueError("No transaction data available.")
        realised_pl_sheet = generate_realised_pl_sheet(self.transaction_df)
        self.realised_pl = realised_pl_sheet
        self.logger.info("Realised P/L sheet generated successfully.")
        return realised_pl_sheet

    def get_total_return_sheet(self):
        if self.holdings_df is None:
            self.get_holdings_sheet()
        if self.dividends_df is None:
            self.get_dividends_sheet()
        if self.realised_pl is None:
            self.get_realised_pl_sheet()
        self.total_return = generate_total_return_sheet(
            self.holdings_df, self.realised_pl, self.dividends_df
        )
        self.logger.info("Total Return sheet generated successfully.")
        return self.total_return

    def save_sheets(self):
        sheet_df_dict = {
            self.transactions_sheet: self.transaction_df,
            self.holdings_sheet: self.holdings_df,
            self.dividends_sheet: self.dividends_df,
            self.portfolio_dividends_sheet: self.portfolio_dividend_summary,
            self.portfolio_summary_sheet: self.portfolio_summary,
            self.dividend_recovery_sheet: self.recovery_summary,
            self.realised_pl_sheet: self.realised_pl,
            self.total_return_sheet: self.total_return,
        }
        with pd.ExcelWriter(self.excel_filepath) as writer:
            for sheet_name, df in sheet_df_dict.items():
                if df is not None:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    self.logger.info("Saved %s sheet to Excel.", sheet_name)
        self.logger.info("All sheets saved successfully to %s.", self.excel_filepath)


mt = MoneyTalks()
