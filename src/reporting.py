import json
import csv
from datetime import datetime

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None


class ReportBuilder:
    def __init__(self, bank):
        self.bank = bank

    def report_client(self, client_id: str) -> dict:
        client = self.bank.clients.get(client_id)
        if not client:
            raise ValueError("Client not found")

        accounts = [self.bank.accounts[aid].get_account_info() for aid in client.account_ids if aid in self.bank.accounts]
        transactions = [t.to_dict() for t in self.bank.transactions if t.sender_id in client.account_ids or t.receiver_id in client.account_ids]

        return {
            "client": client.get_info(),
            "accounts": accounts,
            "transactions": transactions,
        }

    def report_bank(self) -> dict:
        accounts = [a.get_account_info() for a in self.bank.accounts.values()]
        transactions = [t.to_dict() for t in self.bank.transactions]
        return {"bank": {"name": self.bank.name}, "accounts": accounts, "transactions": transactions}

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
        if plt is None:
            return
        report = self.report_client(client_id)
        txs = report["transactions"]
        # simple balance over time chart
        times = [datetime.fromisoformat(t["updated_at"]) for t in txs]
        amounts = [t["amount"] for t in txs]
        if not times:
            return
        plt.figure()
        plt.plot(times, amounts)
        plt.title("Transactions over time")
        plt.savefig(f"{path_prefix}_tx_plot.png")
 