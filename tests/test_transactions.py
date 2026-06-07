import pytest
from datetime import datetime, timedelta

from src.main import (
    Bank,
    Transaction,
    TransactionQueue,
    TransactionProcessor,
    Currency,
    PremiumAccount,
    TransactionStatus,
)


def test_transaction_queue_processing():
    bank = Bank(name="TxBank")

    # clients and accounts
    c1 = bank.add_client(full_name="A User", age=30, contacts={"phone": "1"})
    c2 = bank.add_client(full_name="B User", age=28, contacts={"phone": "2"})
    c3 = bank.add_client(full_name="P User", age=40, contacts={"phone": "3"})

    a1 = bank.open_account(c1.client_id, account_type="bank", balance=1000, currency=Currency.RUB)
    a2 = bank.open_account(c2.client_id, account_type="bank", balance=100, currency=Currency.RUB)
    a3 = bank.open_account(c3.client_id, account_type="premium", balance=0, currency=Currency.RUB, overdraft_limit=500)

    queue = TransactionQueue()

    # Create 10 transactions (mix of valid, fail, delayed, canceled)
    t1 = Transaction("transfer", 100, Currency.RUB, sender_id=a1.account_id, receiver_id=a2.account_id)
    t2 = Transaction("transfer", 50, Currency.RUB, sender_id=a2.account_id, receiver_id=a1.account_id)
    t3 = Transaction("transfer", 200, Currency.RUB, sender_id=a2.account_id, receiver_id=a1.account_id)
    t4 = Transaction("transfer", 200, Currency.RUB, sender_id=a3.account_id, receiver_id=a1.account_id)
    t5 = Transaction("transfer", 800, Currency.RUB, sender_id=a1.account_id, receiver_id=a3.account_id)
    t6 = Transaction("transfer", 10, Currency.RUB, sender_id=a1.account_id, receiver_id=a2.account_id,)
    # delayed
    t7 = Transaction("transfer", 5, Currency.RUB, sender_id=a1.account_id, receiver_id=a2.account_id)
    t8 = Transaction("transfer", 5, Currency.RUB, sender_id=a1.account_id, receiver_id=a2.account_id)
    t9 = Transaction("transfer", 50, Currency.RUB, sender_id=a1.account_id, receiver_id=a2.account_id)
    t10 = Transaction("transfer", 10, Currency.RUB, sender_id=a2.account_id, receiver_id=a1.account_id)

    # add to queue
    queue.add(t1)
    queue.add(t2)
    queue.add(t3)
    queue.add(t4)
    queue.add(t5)
    queue.add(t6)
    # delayed in future
    queue.add(t7, execute_at=datetime.now() + timedelta(days=1))
    # cancel t8
    queue.add(t8)
    queue.cancel(t8.tx_id)
    queue.add(t9)
    queue.add(t10)

    processor = TransactionProcessor(bank)
    processed = processor.process_all(queue)

    # Count completed
    completed = [t for t in processed if t.status == TransactionStatus.COMPLETED]
    failed = [t for t in processed if t.status == TransactionStatus.FAILED]

    # Expected balances computed manually for remaining processed transactions
    # (учтена комиссия 1% для внешних переводов)
    assert round(bank.accounts[a1.account_id]._balance, 2) == 290.40
    assert round(bank.accounts[a2.account_id]._balance, 2) == 199.40
    assert round(bank.accounts[a3.account_id]._balance, 2) == 598.00

    # Ensure at least expected completed transactions processed
    assert len(completed) >= 7
    # delayed transaction still in queue
    assert any(item for item in queue._items if item[2].tx_id == t7.tx_id)