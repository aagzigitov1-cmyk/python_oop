import os
import json
from datetime import datetime, timedelta

from src.main import Bank, Transaction, TransactionQueue, TransactionProcessor, Currency, AuditLog, RiskAnalyzer
from src.reporting import ReportBuilder


def test_audit_and_risk_and_persistence(tmp_path):
    bank = Bank(name="AuditBank")
    bank.audit_log = AuditLog()
    bank.risk_analyzer = RiskAnalyzer(bank, large_amount=500, freq_threshold=2)

    c1 = bank.add_client(full_name="User One", age=30)
    c2 = bank.add_client(full_name="User Two", age=30)

    a1 = bank.open_account(c1.client_id, account_type="bank", balance=1000, currency=Currency.RUB)
    a2 = bank.open_account(c2.client_id, account_type="bank", balance=50, currency=Currency.RUB)

    queue = TransactionQueue()
    # suspicious large
    t1 = Transaction("transfer", 600, Currency.RUB, sender_id=a1.account_id, receiver_id=a2.account_id)
    # frequent small ops
    t2 = Transaction("transfer", 10, Currency.RUB, sender_id=a1.account_id, receiver_id=a2.account_id)
    t3 = Transaction("transfer", 10, Currency.RUB, sender_id=a1.account_id, receiver_id=a2.account_id)

    queue.add(t1)
    queue.add(t2)
    queue.add(t3)

    processor = TransactionProcessor(bank)
    processed = processor.process_all(queue)

    # risk analyzer should log entries
    assert any('Risk' in e['message'] or e['level'] in ('WARN','INFO') for e in bank.audit_log.entries)

    # persistence
    state_file = tmp_path / "state.json"
    bank.save_state(str(state_file))
    assert state_file.exists()
    data = json.loads(state_file.read_text(encoding='utf-8'))
    assert 'clients' in data and 'accounts' in data

    # reports
    rb = ReportBuilder(bank)
    client_report = rb.report_client(c1.client_id)
    assert client_report['client']['full_name'] == 'User One'

    json_path = tmp_path / "report.json"
    rb.export_to_json(client_report, str(json_path))
    assert json_path.exists()

    csv_path = tmp_path / "tx.csv"
    rb.export_to_csv(client_report['transactions'], str(csv_path))
    assert csv_path.exists() or client_report['transactions'] == []