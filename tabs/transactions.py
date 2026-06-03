import streamlit as st
import pandas as pd
from src.components.add_transaction import add_transaction_dialog
from src.db import db


def _column_changed(before, after) -> bool:
    if pd.isna(before) and pd.isna(after):
        return False
    if pd.isna(before) or pd.isna(after):
        return True

    changed = before != after
    try:
        dt_before = pd.to_datetime(before, errors="coerce")
        dt_after = pd.to_datetime(after, errors="coerce")
        if not pd.isna(dt_before) and not pd.isna(dt_after):
            changed = dt_before.normalize() != dt_after.normalize()
    except (TypeError, ValueError):
        pass
    return changed


def _apply_transaction_edits(
    transactions_df: pd.DataFrame, edited: pd.DataFrame
) -> tuple[int, int] | None:
    orig = transactions_df.copy()
    orig["id"] = pd.to_numeric(orig["id"], errors="coerce").astype("Int64")
    edited_work = edited.copy()
    edited_work["id"] = pd.to_numeric(edited_work["id"], errors="coerce").astype(
        "Int64"
    )

    edited_valid = edited_work.dropna(subset=["id"])
    orig_ids = set(orig["id"].dropna().astype(int))
    edited_ids = set(edited_valid["id"].dropna().astype(int))

    unknown = edited_ids - orig_ids
    if unknown:
        st.error(
            f"Unknown transaction ID(s) in the table: {sorted(unknown)}. "
            "Reload the page and try again."
        )
        return None

    deleted_ids = orig_ids - edited_ids
    for transaction_id in deleted_ids:
        db.delete_transaction(int(transaction_id))

    editable_cols = [col for col in orig.columns if col != "id"]
    orig_by = orig.set_index("id")
    new_by = edited_valid.set_index("id")

    updated = 0
    for transaction_id in sorted(orig_ids & edited_ids):
        transaction_id = int(transaction_id)
        if transaction_id not in new_by.index:
            continue

        updates = {
            col: new_by.loc[transaction_id, col]
            for col in editable_cols
            if _column_changed(
                orig_by.loc[transaction_id, col],
                new_by.loc[transaction_id, col],
            )
        }
        if updates:
            db.update_transaction(transaction_id, updates)
            updated += 1

    return len(deleted_ids), updated


def render_transactions(transactions_df: pd.DataFrame, holdings_df: pd.DataFrame):
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.header("Raw Transactions")
    with col2:
        st.write("")
        if st.button("Add Transaction", width="stretch"):
            add_transaction_dialog(holdings_df)

    st.caption(
        "Edit cells to change the rows, click on **Apply Changes** to save them, "
        "or remove a row to delete it."
    )

    visible_cols = [c for c in transactions_df.columns if c != "id"]
    edited = st.data_editor(
        transactions_df,
        width="stretch",
        hide_index=True,
        num_rows="delete",
        column_order=visible_cols,
        key="transactions_data_editor",
    )

    no_id = edited[edited["id"].isna()]
    if not no_id.empty:
        other_cols = [c for c in edited.columns if c != "id"]
        if no_id[other_cols].notna().any(axis=1).any():
            st.warning(
                "Rows without an ID are not saved. Use **Add Transaction** for new rows, "
                "or clear extra blank rows."
            )

    if st.button("Apply changes", width="stretch", type="primary"):
        result = _apply_transaction_edits(transactions_df, edited)
        if result is None:
            return

        deleted_count, updated_count = result
        if deleted_count or updated_count:
            parts = []
            if deleted_count:
                parts.append(f"deleted {deleted_count}")
            if updated_count:
                parts.append(f"updated {updated_count}")
            st.success("Applied: " + ", ".join(parts) + ".")
            st.cache_data.clear()
            st.rerun()
        else:
            st.info("No changes to apply.")
