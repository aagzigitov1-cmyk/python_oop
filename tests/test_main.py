import pytest

from src.main import (
    BankAccount,
    Bank,
    Client,
    Currency,
    AccountStatus,
    ClientStatus,
    InsufficientFundsError,
    AccountFrozenError,
    InvalidOperationError,
    SavingsAccount,
    PremiumAccount,
    InvestmentAccount,
)


def test_deposit_withdraw():
    acc = BankAccount(owner="Test User", balance=100)
    acc.deposit(50)
    assert acc._balance == 150
    acc.withdraw(20)
    assert acc._balance == 130


def test_withdraw_insufficient():
    acc = BankAccount(owner="Test User", balance=50)
    with pytest.raises(InsufficientFundsError):
        acc.withdraw(100)


def test_frozen_account_operations():
    acc = BankAccount(owner="Test User", balance=100, status=AccountStatus.FROZEN)
    with pytest.raises(AccountFrozenError):
        acc.deposit(10)
    with pytest.raises(AccountFrozenError):
        acc.withdraw(10)


def test_savings_account_interest_and_min_balance():
    acc = SavingsAccount(owner="Test User", balance=1000, min_balance=100, monthly_rate=0.02)
    interest = acc.apply_monthly_interest()
    assert interest == 20
    assert acc._balance == 1020

    with pytest.raises(InsufficientFundsError):
        acc.withdraw(950)

    acc.withdraw(910)
    assert acc._balance == 110


def test_premium_account_overdraft_and_commission():
    acc = PremiumAccount(owner="Test User", balance=100, overdraft_limit=200, commission=10)
    acc.withdraw(250)
    assert acc._balance == -160

    with pytest.raises(InsufficientFundsError):
        acc.withdraw(200)

    with pytest.raises(InvalidOperationError):
        acc.withdraw(20000)


def test_investment_account_projection():
    acc = InvestmentAccount(
        owner="Test User",
        balance=500,
        portfolio={"stocks": 1000, "bonds": 500, "etf": 1500},
        annual_growth_rate=0.1
    )

    projected = acc.project_yearly_growth()
    assert projected == 300.0
    info = acc.get_account_info()
    assert info["projected_growth"] == 300.0


def test_bank_client_and_account_workflow():
    bank = Bank(name="Test Bank")
    client = bank.add_client(
        full_name="Мария Иванова",
        age=30,
        contacts={"phone": "+71234567890"},
        security_code="1234"
    )

    assert client.age == 30
    assert client.status == ClientStatus.ACTIVE

    account = bank.open_account(client.client_id, account_type="bank", balance=500)
    assert account.owner == client.full_name
    assert account.account_id in client.account_ids
    assert bank.get_total_balance() == 500

    bank.freeze_account(account.account_id)
    assert bank.accounts[account.account_id].status == AccountStatus.FROZEN

    bank.unfreeze_account(account.account_id)
    assert bank.accounts[account.account_id].status == AccountStatus.ACTIVE

    bank.close_account(account.account_id)
    assert bank.accounts[account.account_id].status == AccountStatus.CLOSED
    assert bank.get_total_balance() == 0


def test_authenticate_client_blocks_after_three_attempts():
    bank = Bank(name="Test Bank")
    client = bank.add_client(
        full_name="Иван Петров",
        age=25,
        contacts={"email": "ivan@example.com"},
        security_code="0000"
    )

    with pytest.raises(InvalidOperationError):
        bank.authenticate_client(client.client_id, "1111")
    with pytest.raises(InvalidOperationError):
        bank.authenticate_client(client.client_id, "2222")
    with pytest.raises(InvalidOperationError):
        bank.authenticate_client(client.client_id, "3333")

    assert client.status == ClientStatus.BLOCKED
    assert len(bank.suspicious_actions) >= 1


def test_bank_operations_forbidden_at_night():
    bank = Bank(name="Test Bank")
    client = bank.add_client(
        full_name="Олег Смирнов",
        age=40,
        contacts={"phone": "+79876543210"},
        security_code="2222"
    )

    with pytest.raises(InvalidOperationError):
        bank.open_account(client.client_id, account_type="bank", balance=100, hour=2)
