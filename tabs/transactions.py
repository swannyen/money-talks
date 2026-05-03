import streamlit as st
import pandas as pd
from src.components.add_transaction import add_transaction_dialog
from src.db import db


def is_values_differ(dataframe_a: pd.DataFrame, dataframe_b: pd.DataFrame) -> bool:
    if pd.isna(dataframe_a) and pd.isna(dataframe_b):
        return False
    if pd.isna(dataframe_a) or pd.isna(dataframe_b):
        return True
    try:
        formatted_dataframe_a = pd.to_datetime(dataframe_a, errors="coerce")
        formatted_dataframe_b = pd.to_datetime(dataframe_b, errors="coerce")
        if not pd.isna(formatted_dataframe_a) and not pd.isna(formatted_dataframe_b):
            return (
                formatted_dataframe_a.normalize() != formatted_dataframe_b.normalize()
            )
    except (TypeError, ValueError):
        pass
    return dataframe_a != dataframe_b


def build_updates(orig_row: pd.Series, new_row: pd.Series, columns: list[str]) -> dict:
    updates = {}
    for col in columns:
        if is_values_differ(orig_row[col], new_row[col]):
            updates[col] = new_row[col]
    return updates


def render_transactions(transactions_df: pd.DataFrame):
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.header("Raw Transactions")
    with col2:
        st.write("")
        if st.button("Add Transaction", width="stretch"):
            add_transaction_dialog()

    st.caption(
        "Edit cells to change the rows, click on **Apply Changes** to save them, "
        "or remove a row to delete it."
    )

    # rowid stays in the dataframe for DB updates but is omitted from column_order so
    # it is hidden by default (users can still show it from the table column menu).
    visible_cols = [c for c in transactions_df.columns if c != "rowid"]
    edited = st.data_editor(
        transactions_df,
        width="stretch",
        hide_index=True,
        num_rows="delete",
        column_order=visible_cols,
        key="transactions_data_editor",
    )

    no_rid = edited[edited["rowid"].isna()]
    if not no_rid.empty:
        other_cols = [c for c in edited.columns if c != "rowid"]
        stray = no_rid[other_cols].notna().any(axis=1).any()
        if stray:
            st.warning(
                "Rows without a Row ID are not saved. Use **Add Transaction** for new rows, "
                "or clear extra blank rows."
            )

    if st.button("Apply changes", width="stretch", type="primary"):
        orig = transactions_df.copy()
        orig["rowid"] = pd.to_numeric(orig["rowid"], errors="coerce").astype("Int64")
        edited_work = edited.copy()
        edited_work["rowid"] = pd.to_numeric(
            edited_work["rowid"], errors="coerce"
        ).astype("Int64")

        edited_valid = edited_work.dropna(subset=["rowid"])
        orig_ids = set(orig["rowid"].dropna().astype(int))
        edited_ids = set(edited_valid["rowid"].dropna().astype(int))

        unknown = edited_ids - orig_ids
        if unknown:
            st.error(
                f"Unknown Row ID(s) in the table (not in database): {sorted(unknown)}. "
                "Reload the page and try again."
            )
            return

        deleted = orig_ids - edited_ids
        for rid in deleted:
            db.delete_transaction(int(rid))

        editable_cols = [c for c in orig.columns if c != "rowid"]
        orig_by = orig.set_index("rowid")
        new_by = edited_valid.set_index("rowid")

        updated = 0
        for rid in sorted(orig_ids & edited_ids):
            rid = int(rid)
            if rid not in new_by.index:
                continue
            updates = build_updates(
                orig_by.loc[rid, editable_cols],
                new_by.loc[rid, editable_cols],
                editable_cols,
            )
            if updates:
                db.update_transaction(rid, updates)
                updated += 1

        if deleted or updated:
            parts = []
            if deleted:
                parts.append(f"deleted {len(deleted)}")
            if updated:
                parts.append(f"updated {updated}")
            st.success("Applied: " + ", ".join(parts) + ".")
            st.cache_data.clear()
            st.rerun()
        else:
            st.info("No changes to apply.")
