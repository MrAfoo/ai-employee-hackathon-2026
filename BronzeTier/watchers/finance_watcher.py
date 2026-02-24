"""
finance_watcher.py – Finance Watcher.

Monitors a folder for bank CSV exports and appends new transactions
to /Accounting/Current_Month.md in the Obsidian vault.

How to use:
  1. Export your bank statement as CSV (most banks support this).
  2. Drop the CSV into the folder specified by FINANCE_DROP_FOLDER in .env.
  3. This watcher detects it, parses transactions, and logs them.

CSV format expected (common bank export):
  Date, Description, Amount, Balance
  2026-01-07, "Coffee Shop", -4.50, 1234.56

Set FINANCE_DROP_FOLDER in .env to the folder you drop CSVs into.
"""
import csv
import logging
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

try:
    from base_watcher import BaseWatcher
except ImportError:
    from watchers.base_watcher import BaseWatcher

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [FinanceWatcher] %(levelname)s %(message)s',
)

APPROVAL_THRESHOLD = float(os.getenv('APPROVAL_THRESHOLD', '500.0'))


class FinanceWatcher(BaseWatcher):
    """
    Watches a drop folder for bank CSV files.
    Parses each CSV and appends transactions to /Accounting/Current_Month.md.
    Flags transactions over APPROVAL_THRESHOLD to /Needs_Action.
    """

    def __init__(self, vault_path: str, drop_folder: str | None = None):
        super().__init__(vault_path, check_interval=60)
        self.drop_folder = Path(
            drop_folder or os.getenv('FINANCE_DROP_FOLDER', './finance_drops')
        )
        self.drop_folder.mkdir(parents=True, exist_ok=True)
        self.accounting_dir = self.vault_path / 'Accounting'
        self.accounting_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir = self.drop_folder / 'processed'
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def check_for_updates(self) -> list:
        """Return list of unprocessed CSV files in the drop folder."""
        csvs = list(self.drop_folder.glob('*.csv'))
        self.logger.info(f'Found {len(csvs)} CSV file(s) to process.')
        return csvs

    def create_action_file(self, item: Path) -> Path:
        """Parse CSV and append to Current_Month.md. Flag large transactions."""
        transactions = self._parse_csv(item)
        if not transactions:
            self.logger.warning(f'No transactions found in {item.name}')
            self._archive_csv(item)
            return item

        # Append to /Accounting/Current_Month.md
        month_file = self.accounting_dir / f'Current_Month_{datetime.now().strftime("%Y-%m")}.md'
        self._append_to_monthly_log(month_file, transactions, item.name)

        # Flag large transactions to /Needs_Action (skip empty/invalid amounts)
        def _safe_amount(t):
            try:
                return abs(float(t.get('amount', '0').replace(',', '').replace('$', '') or '0'))
            except (ValueError, AttributeError):
                return 0.0
        large = [t for t in transactions if _safe_amount(t) >= APPROVAL_THRESHOLD]
        for txn in large:
            self._flag_large_transaction(txn)

        # Archive processed CSV
        self._archive_csv(item)
        self.logger.info(
            f'Processed {len(transactions)} transactions from {item.name}. '
            f'{len(large)} flagged for approval.'
        )
        return month_file

    def _parse_csv(self, filepath: Path) -> list[dict]:
        """Parse bank CSV into list of transaction dicts."""
        transactions = []
        try:
            with filepath.open(encoding='utf-8-sig') as f:
                # Try to sniff dialect
                sample = f.read(1024)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                except csv.Error:
                    dialect = csv.excel

                reader = csv.DictReader(f, dialect=dialect)
                for row in reader:
                    # Normalise common column name variations
                    txn = {
                        'date':        self._get_field(row, ['Date', 'date', 'DATE', 'Transaction Date']),
                        'description': self._get_field(row, ['Description', 'description', 'Narrative', 'Details']),
                        'amount':      self._get_field(row, ['Amount', 'amount', 'Debit', 'Credit', 'Value']),
                        'balance':     self._get_field(row, ['Balance', 'balance', 'Running Balance']),
                    }
                    if txn['date'] or txn['description']:
                        transactions.append(txn)
        except Exception as e:
            self.logger.error(f'Failed to parse CSV {filepath.name}: {e}')
        return transactions

    def _get_field(self, row: dict, keys: list[str]) -> str:
        """Try multiple possible column names and return first match."""
        for key in keys:
            if key in row and row[key].strip():
                return row[key].strip()
        return ''

    def _append_to_monthly_log(self, month_file: Path, transactions: list[dict], source_file: str):
        """Append transactions to the monthly accounting log."""
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        header = f'\n\n## Import: {source_file} ({now})\n\n'
        header += '| Date | Description | Amount | Balance |\n'
        header += '|------|-------------|--------|--------|\n'

        rows = ''
        for t in transactions:
            amount = t.get('amount', '')
            # Colour-code: negative = expense (red emoji), positive = income (green)
            try:
                amt_clean = (amount or '').replace(',', '').replace('$', '').strip()
                amt_float = float(amt_clean) if amt_clean else 0.0
                icon = '🔴' if amt_float < 0 else ('🟢' if amt_float > 0 else '⚪')
            except (ValueError, AttributeError):
                icon = '⚪'
            rows += f"| {t.get('date','')} | {t.get('description','')} | {icon} {amount} | {t.get('balance','')} |\n"

        # Create file with header if it doesn't exist
        if not month_file.exists():
            month_file.write_text(
                f'# Accounting – {datetime.now().strftime("%B %Y")}\n\n'
                f'> Auto-generated by Finance Watcher. Do not edit the import sections.\n',
                encoding='utf-8',
            )

        with month_file.open('a', encoding='utf-8') as f:
            f.write(header + rows)

    def _flag_large_transaction(self, txn: dict):
        """Write a Needs_Action note for transactions over the approval threshold."""
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_desc = ''.join(c if c.isalnum() else '_' for c in txn.get('description', 'unknown'))[:40]
        filename = f'FINANCE_{ts}_{safe_desc}.md'
        filepath = self.needs_action / filename
        content = f"""---
type: payment
action: payment
amount: {txn.get('amount', 'unknown')}
recipient: {txn.get('description', 'unknown')}
date: {txn.get('date', '')}
status: pending
priority: high
---

# ⚠️ Large Transaction Flagged

**Amount:** {txn.get('amount', 'unknown')}
**Description:** {txn.get('description', 'unknown')}
**Date:** {txn.get('date', '')}
**Balance After:** {txn.get('balance', 'unknown')}

> This transaction exceeds the approval threshold of ${APPROVAL_THRESHOLD:.2f}.

## Actions Required
- [ ] Verify this transaction is expected
- [ ] Move to `/Approved` if OK, `/Rejected` if suspicious
- [ ] Contact bank if unrecognised

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder.
"""
        filepath.write_text(content, encoding='utf-8')
        self.logger.warning(f'Large transaction flagged: {txn.get("amount")} – {txn.get("description")}')

    def _archive_csv(self, filepath: Path):
        """Move processed CSV to /processed subfolder."""
        dest = self.processed_dir / filepath.name
        shutil.move(str(filepath), dest)
        self.logger.info(f'CSV archived: {filepath.name} → processed/')


if __name__ == '__main__':
    vault = os.getenv('VAULT_PATH', './BronzeTier')
    watcher = FinanceWatcher(vault_path=vault)
    watcher.run()
