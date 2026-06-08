import json
import csv
import logging
from datetime import datetime

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

logger = logging.getLogger(__name__)


class ReportBuilder:
    def __init__(self, bank):
        self.bank = bank

    def report_client(self, client_id: str) -> dict:
        client = self.bank.clients.get(client_id)
        if not client:
            raise ValueError("Client not found")

        accounts = [
            self.bank.accounts[aid].get_account_info()
            for aid in client.account_ids
            if aid in self.bank.accounts
        ]
        transactions = [
            t.to_dict()
            for t in self.bank.transactions
            if t.sender_id in client.account_ids or t.receiver_id in client.account_ids
        ]

        return {
            "client": client.get_info(),
            "accounts": accounts,
            "transactions": transactions,
        }

    def report_bank(self) -> dict:
        accounts = [a.get_account_info() for a in self.bank.accounts.values()]
        transactions = [t.to_dict() for t in self.bank.transactions]
        return {"bank": {"name": self.bank.name}, "accounts": accounts, "transactions": transactions}

    def report_risk(self) -> dict:
        """Generate risk analysis report from audit log."""
        audit_entries = self.bank.audit_log.entries if self.bank.audit_log else []
        suspicious_actions = list(self.bank.suspicious_actions)

        level_counts: dict[str, int] = {}
        reason_counts: dict[str, int] = {}
        for entry in audit_entries:
            level = entry.get("level", "UNKNOWN")
            level_counts[level] = level_counts.get(level, 0) + 1
            context = entry.get("context", {}) or {}
            reasons = context.get("reasons")
            if isinstance(reasons, list):
                for reason in reasons:
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
            elif reasons:
                reason_counts[str(reasons)] = reason_counts.get(str(reasons), 0) + 1

        return {
            "bank": {"name": self.bank.name},
            "audit_entries": audit_entries,
            "suspicious_actions": suspicious_actions,
            "risk_summary": {
                "levels": level_counts,
                "reasons": reason_counts,
                "suspicious_count": len(suspicious_actions),
            },
        }

    def export_to_json(self, data: dict, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def export_to_csv(self, transactions: list[dict], path: str):
        if not transactions:
            return
        keys = transactions[0].keys()
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for row in transactions:
                writer.writerow(row)

    def save_charts(self, client_id: str, path_prefix: str):
        """Generate and save all charts: balance movement, transaction type pie, and status bar."""
        if plt is None:
            logger.warning("matplotlib not available, skipping charts")
            return
        report = self.report_client(client_id)
        txs = report["transactions"]
        if not txs:
            logger.info("No transactions for client %s, skipping charts", client_id)
            return

        self._save_balance_chart(report, txs, path_prefix)
        self._save_transaction_type_pie(report, txs, path_prefix)
        self._save_status_bar_chart(report, txs, path_prefix)

    def _save_balance_chart(self, report: dict, txs: list[dict], path_prefix: str):
        """Save line chart of transaction amounts over time."""
        times = [datetime.fromisoformat(t["updated_at"]) for t in txs]
        amounts = [t["amount"] for t in txs]
        plt.figure()
        plt.plot(times, amounts, marker='o')
        plt.title(f"Balance movement for {report['client']['full_name']}")
        plt.xlabel("Time")
        plt.ylabel("Amount")
        plt.grid(True, linestyle='--', alpha=0.4)
        plt.tight_layout()
        plt.savefig(f"{path_prefix}_balance_movement.png")
        plt.close()
        logger.info("Saved balance chart to %s_balance_movement.png", path_prefix)

    def _save_transaction_type_pie(self, report: dict, txs: list[dict], path_prefix: str):
        """Save pie chart of transaction types."""
        type_counts: dict[str, int] = {}
        for t in txs:
            tx_type = t.get("type") or "unknown"
            type_counts[tx_type] = type_counts.get(tx_type, 0) + 1
        labels = list(type_counts.keys())
        sizes = list(type_counts.values())
        if not labels:
            return
        plt.figure()
        plt.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140)
        plt.title(f"Transaction type distribution for {report['client']['full_name']}")
        plt.tight_layout()
        plt.savefig(f"{path_prefix}_type_distribution.png")
        plt.close()
        logger.info("Saved type distribution pie chart to %s_type_distribution.png", path_prefix)

    def _save_status_bar_chart(self, report: dict, txs: list[dict], path_prefix: str):
        """Save bar chart of transaction amounts by status."""
        status_sums: dict[str, float] = {}
        for t in txs:
            status = t.get("status") or "unknown"
            status_sums[status] = status_sums.get(status, 0.0) + float(t.get("amount", 0.0))
        labels = list(status_sums.keys())
        values = [status_sums[label] for label in labels]
        if not labels:
            return
        plt.figure()
        plt.bar(labels, values, color=["#4c72b0", "#55a868", "#c44e52", "#8172b2"][: len(labels)])
        plt.title(f"Transaction amount by status for {report['client']['full_name']}")
        plt.xlabel("Status")
        plt.ylabel("Total amount")
        plt.tight_layout()
        plt.savefig(f"{path_prefix}_status_amounts.png")
        plt.close()
        logger.info("Saved status bar chart to %s_status_amounts.png", path_prefix)
