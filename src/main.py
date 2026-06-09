# День 1 — Базовая модель банковских счетов (усложнённый вариант)

from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime, timedelta
import json
import csv
import logging
import random
import uuid
from src.reporting import ReportBuilder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

class AccountStatus(Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"

class AbstractAccount(ABC):

    def __init__(
        self,
        account_id,
        owner,
        balance,
        status=AccountStatus.ACTIVE
    ):
        self.account_id = account_id
        self.owner = owner
        self._balance = balance
        self.status = status

    @abstractmethod
    def deposit(self, amount: float):
        pass

    @abstractmethod
    def withdraw(self, amount: float):
        pass

    @abstractmethod
    def get_account_info(self):
        pass


class Currency(Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    KZT = "KZT"
    CNY = "CNY"


class BankAccount(AbstractAccount):

    def __init__(
        self,
        owner: str,
        balance: float = 0,
        currency: Currency = Currency.RUB,
        account_id: str | None = None,
        status: AccountStatus = AccountStatus.ACTIVE
    ):

        if not owner:
            raise ValueError("Имя владельца обязательно")
        
        if balance < 0:
            raise ValueError("Баланс не может быть отрицательным")
        
        if not isinstance(currency, Currency):
            raise ValueError("Некорректная валюта")
        
        super().__init__(
            account_id=account_id or str(uuid.uuid4())[:8],
            owner=owner,
            balance=balance,
            status=status
        )
        
        self.currency = currency
        self.creation_date = datetime.now()  # Track account creation date for risk analysis

    def _check_status(self):
        if self.status == AccountStatus.FROZEN:
            raise AccountFrozenError("Счёт заморожен")

        if self.status == AccountStatus.CLOSED:
            raise AccountClosedError("Счёт закрыт")

    def _validate_amount(self, amount):
        if not isinstance(amount, (int, float)):
            raise InvalidOperationError(
                "Сумма должна быть числом"
            )

        if amount <= 0:
            raise InvalidOperationError(
                "Сумма должна быть больше нуля"
            )

    @property
    def balance(self) -> float:
        return self._balance

    def get_account_info(self):
        return {
            "account_id": self.account_id,
            "owner": self.owner,
            "balance": self.balance,
            "currency": self.currency.value,
            "status": self.status.value
        }
        
    def deposit(self, amount):
        self._check_status()
        self._validate_amount(amount)

        self._balance += amount

    def debit(self, amount: float, fee: float = 0.0):
        self.withdraw(amount + fee)

    def withdraw(self, amount):
        self._check_status()
        self._validate_amount(amount)

        if amount > self._balance:
            raise InsufficientFundsError(
                "Недостаточно средств"
            )

        self._balance -= amount




    def __str__(self):
        return (
            f"Тип счета: {self.__class__.__name__}, "
            f"Клиент: {self.owner}, "
            f"Счет: ****{self.account_id[-4:]}, "
            f"Статус: {self.status.value}, "
            f"Баланс: {self._balance:.2f} {self.currency.value}"
        )



class AccountError(Exception):
    pass


class AccountFrozenError(AccountError):
    pass


class AccountClosedError(AccountError):
    pass


class InvalidOperationError(AccountError):
    pass


class InsufficientFundsError(AccountError):
    pass


class RiskBlockedError(AccountError):
    pass



# Тестирование
if __name__ == "__main__":

    # Активный счёт
    active_account = BankAccount(
        owner="Иван Петров",
        balance=1000,
        currency=Currency.RUB
    )

    print("Активный счет:")
    print(active_account)

    # Валидное пополнение
    active_account.deposit(500)

    # Валидное снятие
    active_account.withdraw(300)

    print("\nПосле операций:")
    print(active_account)

    # Замороженный счёт
    frozen_account = BankAccount(
        owner="Анна Смирнова",
        balance=2000,
        currency=Currency.USD,
        status=AccountStatus.FROZEN
    )

    print("\nЗамороженный счет:")
    print(frozen_account)

    # Попытка пополнения
    try:
        frozen_account.deposit(100)

    except AccountFrozenError as e:
        print(f"\nОшибка: {e}")

    # Попытка снятия
    try:
        frozen_account.withdraw(50)

    except AccountFrozenError as e:
        print(f"Ошибка: {e}")








# День 2 

class SavingsAccount(BankAccount):

    def __init__(
        self,
        owner: str,
        balance: float = 0,
        currency: Currency = Currency.RUB,
        min_balance: float = 0,
        monthly_rate: float = 0.01,
        account_id: str | None = None,
        status: AccountStatus = AccountStatus.ACTIVE
    ):
        super().__init__(
            owner=owner,
            balance=balance,
            currency=currency,
            account_id=account_id,
            status=status
        )

        if min_balance < 0:
            raise ValueError("Минимальный остаток не может быть отрицательным")

        if monthly_rate < 0:
            raise ValueError("Процентная ставка не может быть отрицательной")

        self.min_balance = min_balance
        self.monthly_rate = monthly_rate

    def apply_monthly_interest(self):
        self._check_status()

        if self._balance < self.min_balance:
            return 0.0

        interest = self._balance * self.monthly_rate
        self._balance += interest
        return interest

    def withdraw(self, amount):
        self._check_status()
        self._validate_amount(amount)

        if amount > self._balance - self.min_balance:
            raise InsufficientFundsError(
                "Сумма превышает доступный остаток с учётом минимального баланса"
            )

        self._balance -= amount

    def get_account_info(self):
        info = super().get_account_info()
        info.update({
            "min_balance": self.min_balance,
            "monthly_rate": self.monthly_rate,
        })
        return info

    def __str__(self):
        return (
            f"Тип счета: {self.__class__.__name__}, "
            f"Клиент: {self.owner}, "
            f"Баланс: {self._balance:.2f} {self.currency.value}, "
            f"Мин. остаток: {self.min_balance:.2f}, "
            f"Ставка: {self.monthly_rate * 100:.2f}%"
        )


class PremiumAccount(BankAccount):

    def __init__(
        self,
        owner: str,
        balance: float = 0,
        currency: Currency = Currency.RUB,
        overdraft_limit: float = 1000,
        withdrawal_limit: float = 10000,
        commission: float = 5,
        account_id: str | None = None,
        status: AccountStatus = AccountStatus.ACTIVE
    ):
        super().__init__(
            owner=owner,
            balance=balance,
            currency=currency,
            account_id=account_id,
            status=status
        )

        if overdraft_limit < 0:
            raise ValueError("Лимит овердрафта не может быть отрицательным")

        if withdrawal_limit <= 0:
            raise ValueError("Лимит снятия должен быть больше нуля")

        if commission < 0:
            raise ValueError("Комиссия не может быть отрицательной")

        self.overdraft_limit = overdraft_limit
        self.withdrawal_limit = withdrawal_limit
        self.commission = commission

    def debit(self, amount: float, fee: float = 0.0):
        self._check_status()
        self._validate_amount(amount)

        if amount > self.withdrawal_limit:
            raise InvalidOperationError("Превышен лимит снятия для премиум-счета")

        total_cost = amount + fee
        max_available = self._balance + self.overdraft_limit

        if total_cost > max_available:
            raise InsufficientFundsError(
                "Недостаточно средств с учетом овердрафта"
            )

        self._balance -= total_cost

    def withdraw(self, amount):
        self._check_status()
        self._validate_amount(amount)

        if amount > self.withdrawal_limit:
            raise InvalidOperationError("Превышен лимит снятия для премиум-счета")

        total_cost = amount + self.commission
        max_available = self._balance + self.overdraft_limit

        if total_cost > max_available:
            raise InsufficientFundsError(
                "Недостаточно средств с учетом овердрафта и комиссии"
            )

        self._balance -= total_cost

    def get_account_info(self):
        info = super().get_account_info()
        info.update({
            "overdraft_limit": self.overdraft_limit,
            "withdrawal_limit": self.withdrawal_limit,
            "commission": self.commission,
        })
        return info

    def __str__(self):
        return (
            f"Тип счета: {self.__class__.__name__}, "
            f"Клиент: {self.owner}, "
            f"Баланс: {self._balance:.2f} {self.currency.value}, "
            f"Овердрафт: {self.overdraft_limit:.2f}, "
            f"Комиссия: {self.commission:.2f}"
        )


class InvestmentAccount(BankAccount):

    def __init__(
        self,
        owner: str,
        balance: float = 0,
        currency: Currency = Currency.RUB,
        portfolio: dict | None = None,
        annual_growth_rate: float = 0.08,
        account_id: str | None = None,
        status: AccountStatus = AccountStatus.ACTIVE
    ):
        super().__init__(
            owner=owner,
            balance=balance,
            currency=currency,
            account_id=account_id,
            status=status
        )

        self.virtual_assets = portfolio or {
            "stocks": 0.0,
            "bonds": 0.0,
            "etf": 0.0,
        }

        if annual_growth_rate < 0:
            raise ValueError("Годовая ставка роста не может быть отрицательной")

        self.annual_growth_rate = annual_growth_rate

    def project_yearly_growth(self):
        self._check_status()
        total_assets = sum(self.virtual_assets.values())
        return total_assets * self.annual_growth_rate

    def get_account_info(self):
        info = super().get_account_info()
        info.update({
            "virtual_assets": dict(self.virtual_assets),
            "annual_growth_rate": self.annual_growth_rate,
            "projected_growth": self.project_yearly_growth(),
        })
        return info

    def withdraw(self, amount: float):
        """Withdraw from investment account with asset liquidation notification."""
        self._check_status()
        self._validate_amount(amount)

        if amount > self._balance:
            raise InsufficientFundsError("Недостаточно средств для снятия")

        # For investment accounts, withdrawal may trigger partial asset liquidation
        total_assets = sum(self.virtual_assets.values())
        if total_assets > 0:
            logger.info(f"Investment account {self.account_id}: withdrawing {amount}, liquidating assets (total: {total_assets})")

        self._balance -= amount

    def __str__(self):
        assets = ", ".join(
            f"{name}: {value:.2f}" for name, value in self.virtual_assets.items()
        )
        return (
            f"Тип счета: {self.__class__.__name__}, "
            f"Клиент: {self.owner}, "
            f"Баланс: {self._balance:.2f} {self.currency.value}, "
            f"Активы: [{assets}], "
            f"Годовой рост: {self.annual_growth_rate * 100:.2f}%"
        )




# День 3 — Система Bank 


class ClientStatus(Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"


class Client:

    def __init__(
        self,
        full_name: str,
        age: int,
        contacts: dict | None = None,
        client_id: str | None = None,
        security_code: str | None = None,
    ):
        if age < 18:
            raise ValueError("Клиент должен быть совершеннолетним")

        self.full_name = full_name
        self.age = age
        self.contacts = contacts or {}
        self.client_id = client_id or str(uuid.uuid4())[:8]
        self.status = ClientStatus.ACTIVE
        self.account_ids: list[str] = []
        self.security_code = security_code or str(uuid.uuid4())[:6]
        self.login_attempts = 0

    def add_account(self, account_id: str):
        if account_id not in self.account_ids:
            self.account_ids.append(account_id)

    def remove_account(self, account_id: str):
        if account_id in self.account_ids:
            self.account_ids.remove(account_id)

    def block(self):
        self.status = ClientStatus.BLOCKED

    def is_active(self):
        return self.status == ClientStatus.ACTIVE

    def get_info(self):
        return {
            "client_id": self.client_id,
            "full_name": self.full_name,
            "age": self.age,
            "contacts": dict(self.contacts),
            "status": self.status.value,
            "accounts": list(self.account_ids),
        }

    def __str__(self):
        return (
            f"Клиент: {self.full_name}, "
            f"ID: {self.client_id}, "
            f"Статус: {self.status.value}, "
            f"Счета: {len(self.account_ids)}"
        )


class Bank:

    ACCOUNT_TYPES = {
        "bank": BankAccount,
        "savings": SavingsAccount,
        "premium": PremiumAccount,
        "investment": InvestmentAccount,
    }

    def __init__(self, name: str = "Bank"):
        self.name = name
        self.clients: dict[str, Client] = {}
        self.accounts: dict[str, BankAccount] = {}
        self.suspicious_actions: list[dict] = []
        self.transactions: list[Transaction] = []
        self.audit_log = None
        self.risk_analyzer = None

    def add_client(
        self,
        full_name: str,
        age: int,
        contacts: dict | None = None,
        security_code: str | None = None,
    ) -> Client:
        client = Client(
            full_name=full_name,
            age=age,
            contacts=contacts,
            security_code=security_code,
        )
        self.clients[client.client_id] = client
        return client

    def _check_business_hours(self, hour: int | None = None):
        hour = datetime.now().hour if hour is None else hour
        if 0 <= hour < 5:
            raise InvalidOperationError(
                "Операции нельзя выполнять с 00:00 до 05:00"
            )

    def _get_client(self, client_id: str) -> Client:
        if client_id not in self.clients:
            raise InvalidOperationError("Клиент не найден")
        return self.clients[client_id]

    def _get_account(self, account_id: str) -> BankAccount:
        if account_id not in self.accounts:
            raise InvalidOperationError("Счёт не найден")
        return self.accounts[account_id]

    def mark_suspicious(
        self,
        action: str,
        reason: str,
        client_id: str | None = None,
        account_id: str | None = None,
    ):
        record = {
            "action": action,
            "reason": reason,
            "client_id": client_id,
            "account_id": account_id,
            "time": datetime.now().isoformat(),
        }
        self.suspicious_actions.append(record)
        # also write to audit if available
        logger.warning(
            "Suspicious action=%s reason=%s client_id=%s account_id=%s",
            action,
            reason,
            client_id,
            account_id,
        )
        if self.audit_log:
            self.audit_log.log("WARN", f"Suspicious: {action} - {reason}", context=record)

    def authenticate_client(self, client_id: str, security_code: str) -> bool:
        client = self._get_client(client_id)

        if client.status == ClientStatus.BLOCKED:
            raise InvalidOperationError("Клиент заблокирован")

        if client.security_code != security_code:
            client.login_attempts += 1
            if client.login_attempts >= 3:
                client.block()
                self.mark_suspicious(
                    action="authenticate",
                    reason="3 неверные попытки входа",
                    client_id=client_id,
                )
                raise InvalidOperationError("Клиент заблокирован после 3 неверных попыток")

            self.mark_suspicious(
                action="authenticate",
                reason=f"Неверный код ({client.login_attempts})",
                client_id=client_id,
            )
            raise InvalidOperationError("Неверный код клиента")

        client.login_attempts = 0
        return True

    def open_account(
        self,
        client_id: str,
        account_type: str = "bank",
        hour: int | None = None,
        **kwargs,
    ) -> BankAccount:
        self._check_business_hours(hour)
        client = self._get_client(client_id)

        if not client.is_active():
            raise InvalidOperationError("Клиент заблокирован")

        account_class = self.ACCOUNT_TYPES.get(account_type.lower())
        if account_class is None:
            raise InvalidOperationError("Неизвестный тип счета")

        account = account_class(owner=client.full_name, **kwargs)
        self.accounts[account.account_id] = account
        client.add_account(account.account_id)
        return account


    def save_state(self, path: str):
        import json

        data = {
            "clients": [c.get_info() for c in self.clients.values()],
            "accounts": [a.get_account_info() for a in self.accounts.values()],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_state(self, path: str):
        import json

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # naive load: recreate clients/accounts minimal info
        for c in data.get("clients", []):
            client = Client(full_name=c["full_name"], age=c.get("age", 18), contacts=c.get("contacts", {}), client_id=c.get("client_id"))
            self.clients[client.client_id] = client

        for a in data.get("accounts", []):
            owner = a.get("owner")
            balance = a.get("balance", 0)
            currency = Currency(a.get("currency", "RUB"))
            account = BankAccount(owner=owner, balance=balance, currency=currency, account_id=a.get("account_id"))
            account.status = AccountStatus(a.get("status"))
            self.accounts[account.account_id] = account

    def close_account(self, account_id: str, hour: int | None = None):
        self._check_business_hours(hour)
        account = self._get_account(account_id)
        account.status = AccountStatus.CLOSED

    def freeze_account(self, account_id: str, hour: int | None = None):
        self._check_business_hours(hour)
        account = self._get_account(account_id)
        account.status = AccountStatus.FROZEN
        self.mark_suspicious(
            action="freeze_account",
            reason="заморозка счета",
            account_id=account_id,
        )

    def unfreeze_account(self, account_id: str, hour: int | None = None):
        self._check_business_hours(hour)
        account = self._get_account(account_id)
        account.status = AccountStatus.ACTIVE

    def search_accounts(
        self,
        owner: str | None = None,
        status: AccountStatus | None = None,
        client_id: str | None = None,
    ) -> list[dict]:
        results = []
        for account in self.accounts.values():
            if owner and owner.lower() not in account.owner.lower():
                continue
            if status and account.status != status:
                continue
            if client_id:
                client = self._get_client(client_id)
                if account.account_id not in client.account_ids:
                    continue
            results.append(account.get_account_info())
        return results

    def get_total_balance(self) -> float:
        return sum(
            account.balance
            for account in self.accounts.values()
            if account.status != AccountStatus.CLOSED
        )

    def get_clients_ranking(self) -> list[dict]:
        ranking = []
        for client in self.clients.values():
            total = sum(
                self.accounts[account_id].balance
                for account_id in client.account_ids
                if account_id in self.accounts
                and self.accounts[account_id].status != AccountStatus.CLOSED
            )
            ranking.append({
                "client_id": client.client_id,
                "full_name": client.full_name,
                "total_balance": total,
            })
        ranking.sort(key=lambda item: item["total_balance"], reverse=True)
        return ranking


# День 4

class TransactionStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class Transaction:
    def __init__(
        self,
        tx_type: str,
        amount: float,
        currency: Currency,
        sender_id: str,
        receiver_id: str,
        fee: float | None = None,
        tx_id: str | None = None,
    ):
        self.tx_id = tx_id or str(uuid.uuid4())[:10]
        self.tx_type = tx_type
        self.amount = amount
        self.currency = currency
        self.fee = fee
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.status = TransactionStatus.PENDING
        self.reason: str | None = None
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.attempts = 0

    def to_dict(self):
        return {
            "tx_id": self.tx_id,
            "type": self.tx_type,
            "amount": self.amount,
            "currency": self.currency.value,
            "fee": self.fee,
            "sender": self.sender_id,
            "receiver": self.receiver_id,
            "status": self.status.value,
            "reason": self.reason,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "attempts": self.attempts,
        }


class TransactionQueue:
    def __init__(self):
        self._items: list[tuple[int, datetime, Transaction]] = []

    def add(self, tx: Transaction, priority: int = 0, execute_at: datetime | None = None):
        execute_at = execute_at or datetime.now()
        self._items.append((priority, execute_at, tx))

    def cancel(self, tx_id: str) -> bool:
        for i, (_p, _e, tx) in enumerate(self._items):
            if tx.tx_id == tx_id:
                tx.status = TransactionStatus.CANCELED
                tx.updated_at = datetime.now()
                self._items.pop(i)
                return True
        return False

    def pop_next(self) -> Transaction | None:
        now = datetime.now()
        # eligible: execute_at <= now and status pending
        eligible = [(p, e, t) for (p, e, t) in self._items if e <= now and t.status == TransactionStatus.PENDING]
        if not eligible:
            return None
        # highest priority first, then earliest execute_at
        eligible.sort(key=lambda item: (-item[0], item[1]))
        chosen = eligible[0]
        self._items.remove(chosen)
        return chosen[2]

    def __len__(self):
        return len(self._items)




class TransactionProcessor:
    def __init__(self, bank: Bank, max_retries: int = 3):
        self.bank = bank
        self.max_retries = max_retries

    def _compute_fee(self, tx: Transaction) -> float:
        sender = self.bank.accounts.get(tx.sender_id)
        receiver = self.bank.accounts.get(tx.receiver_id)
        if not sender or not receiver:
            return 0.0
        # external transfer = different owners => 1% fee
        if sender.owner != receiver.owner:
            return round(tx.amount * 0.01, 2)
        return 0.0

    def _convert_amount(self, amount: float, from_currency: Currency, to_currency: Currency) -> float:
        # simplistic conversion rates for demo (RUB base)
        rates = {"RUB": 1.0, "USD": 70.0, "EUR": 80.0, "KZT": 0.15, "CNY": 10.0}
        if from_currency == to_currency:
            return amount
        base = amount * rates[from_currency.value]
        return round(base / rates[to_currency.value], 2)

    def process_next(self, queue: TransactionQueue) -> Transaction | None:
        tx = queue.pop_next()
        if tx is None:
            return None

        tx.status = TransactionStatus.PROCESSING
        tx.updated_at = datetime.now()

        sender = self.bank.accounts.get(tx.sender_id)
        receiver = self.bank.accounts.get(tx.receiver_id)

        if sender is None or receiver is None:
            tx.status = TransactionStatus.FAILED
            tx.reason = "Account not found"
            tx.updated_at = datetime.now()
            self.bank.mark_suspicious("transaction", tx.reason, client_id=None, account_id=tx.sender_id)
            logger.warning("Transaction failed: %s", tx.reason)
            self.bank.transactions.append(tx)
            return tx

        try:
            # rule: no operations on frozen/closed accounts
            if sender.status in (AccountStatus.FROZEN, AccountStatus.CLOSED) or receiver.status in (AccountStatus.FROZEN, AccountStatus.CLOSED):
                raise InvalidOperationError("Операции с замороженным/закрытым счётом запрещены")

            fee = tx.fee if tx.fee is not None else self._compute_fee(tx)
            # Convert both amount and fee to sender's currency
            converted_amount = self._convert_amount(tx.amount, tx.currency, receiver.currency)
            fee_in_sender_currency = self._convert_amount(fee, Currency.RUB, sender.currency)
            total_debit = self._convert_amount(tx.amount, tx.currency, sender.currency) + fee_in_sender_currency

            # rule: prevent negative balances except for PremiumAccount
            sender_allows_overdraft = isinstance(sender, PremiumAccount)
            if not sender_allows_overdraft and total_debit > sender.balance:
                raise InsufficientFundsError("Недостаточно средств для перевода и комиссии")

            sender.debit(tx.amount, fee=fee)
            receiver.deposit(converted_amount)

            tx.fee = fee
            tx.status = TransactionStatus.COMPLETED
            tx.updated_at = datetime.now()
            # record transaction
            self.bank.transactions.append(tx)
            return tx

        except Exception as e:
            tx.attempts += 1
            tx.reason = str(e)
            tx.updated_at = datetime.now()
            logger.debug("Transaction %s attempt %s failed: %s", tx.tx_id, tx.attempts, tx.reason)
            if tx.attempts >= self.max_retries:
                tx.status = TransactionStatus.FAILED
                self.bank.mark_suspicious("transaction", tx.reason, client_id=sender.owner if sender else None, account_id=tx.sender_id)
                # Add failed transaction to history so it's not lost
                self.bank.transactions.append(tx)
                logger.warning("Transaction %s failed after %d attempts, marked as FAILED", tx.tx_id, tx.attempts)
                return tx
            else:
                tx.status = TransactionStatus.PENDING
                # requeue for retry shortly
                retry_at = datetime.now() + timedelta(seconds=1)
                logger.info("Transaction %s will be retried at %s", tx.tx_id, retry_at)
                return tx

    def process_all(self, queue: TransactionQueue):
        """Process all transactions in queue with guaranteed retry attempts up to max_retries."""
        processed = []
        max_iterations = len(queue) * self.max_retries + 100  # safety limit
        iterations = 0
        
        while iterations < max_iterations:
            iterations += 1
            tx = self.process_next(queue)
            if tx is None:
                # No more transactions in queue
                break
            
            # If transaction is pending (needs retry), re-queue it
            if tx.status == TransactionStatus.PENDING:
                # Re-queue with delayed execution for retry
                retry_at = datetime.now() + timedelta(seconds=0.1)
                queue.add(tx, priority=0, execute_at=retry_at)
                continue
            
            # Transaction is either COMPLETED or FAILED - add to processed
            processed.append(tx)
        
        return processed






# День 5 — Аудит и риск-анализ

class AuditLog:
    def __init__(self):
        self.entries: list[dict] = []

    def log(self, level: str, message: str, context: dict | None = None):
        entry = {
            "time": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "context": context or {},
        }
        self.entries.append(entry)
        log_method = logger.warning if level.upper() in ("WARN", "WARNING", "ERROR", "CRITICAL") else logger.info
        log_method("%s %s %s", level, message, context or {})

    def filter(self, level: str | None = None, since: datetime | None = None):
        results = self.entries
        if level:
            results = [e for e in results if e["level"] == level]
        if since:
            results = [e for e in results if datetime.fromisoformat(e["time"]) >= since]
        return results

    def save_to_file(self, path: str):
        import json

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, ensure_ascii=False, indent=2)


class RiskAnalyzer:
    def __init__(self, bank: Bank, large_amount: float = 10000.0, freq_threshold: int = 5, new_account_days: int = 7):
        self.bank = bank
        self.large_amount = large_amount
        self.freq_threshold = freq_threshold
        self.new_account_days = new_account_days

    def analyze(self, tx: Transaction) -> str:
        """Return risk: 'low'|'medium'|'high' and log to audit."""
        score = 0
        reasons = []

        # large amount
        if tx.amount >= self.large_amount:
            score += 2
            reasons.append("large_amount")

        # frequent operations: count recent transactions from sender
        recent = [t for t in self.bank.transactions if t.sender_id == tx.sender_id and datetime.fromisoformat(t.created_at.isoformat()) >= datetime.now() - timedelta(minutes=10)]
        if len(recent) >= self.freq_threshold:
            score += 2
            reasons.append("frequent_ops")

        # transfers to new accounts
        receiver_acc = self.bank.accounts.get(tx.receiver_id)
        if receiver_acc:
            # check if receiver account recently created
            if hasattr(receiver_acc, 'creation_date'):
                account_age = datetime.now() - receiver_acc.creation_date
                if account_age.days < self.new_account_days:
                    score += 1
                    reasons.append("new_receiver_account")

        # nighttime
        if tx.created_at.hour < 5:
            score += 1
            reasons.append("night_op")

        # map score to risk
        if score >= 3:
            risk = "high"
        elif score == 2:
            risk = "medium"
        else:
            risk = "low"

        # log
        if self.bank.audit_log:
            self.bank.audit_log.log("WARN" if risk != "low" else "INFO", f"Risk {risk} for tx {tx.tx_id}", context={"reasons": reasons, "tx": tx.to_dict()})

        return risk





# День 6 — Демонстрационная программа

def _print_account_summary(client, bank):
    print(f"\nСчета клиента {client.full_name} (ID={client.client_id}):")
    for account_id in client.account_ids:
        account = bank.accounts.get(account_id)
        if account:
            print(f"  - {account}")


def _print_transaction_stats(bank):
    total = len(bank.transactions)
    completed = len([t for t in bank.transactions if t.status == TransactionStatus.COMPLETED])
    failed = len([t for t in bank.transactions if t.status == TransactionStatus.FAILED])
    canceled = len([t for t in bank.transactions if t.status == TransactionStatus.CANCELED])
    print("\nСтатистика транзакций:")
    print(f"  Всего: {total}")
    print(f"  Выполнено: {completed}")
    print(f"  Отклонено: {failed}")
    print(f"  Отменено: {canceled}")


def run_demo_day6():

    print("=== Day 6 Demo: комплексная банковская система ===")
    bank = Bank(name="Demo Day6 Bank")
    bank.audit_log = AuditLog()
    bank.risk_analyzer = RiskAnalyzer(bank, large_amount=500, freq_threshold=3)

    names = [
        "Алексей Смирнов",
        "Мария Иванова",
        "Иван Петров",
        "Елена Кузнецова",
        "Сергей Николаев",
        "Ольга Соколова",
    ]
    clients = [bank.add_client(full_name=name, age=20 + i * 4, contacts={"phone": f"+700000000{i}"}) for i, name in enumerate(names)]

    account_definitions = [
        {"client": clients[0], "type": "bank", "balance": 1000},
        {"client": clients[0], "type": "premium", "balance": 200, "overdraft_limit": 300},
        {"client": clients[1], "type": "savings", "balance": 500, "min_balance": 50, "monthly_rate": 0.015},
        {"client": clients[1], "type": "investment", "balance": 200, "portfolio": {"stocks": 150, "bonds": 100, "etf": 50}},
        {"client": clients[2], "type": "bank", "balance": 300},
        {"client": clients[2], "type": "premium", "balance": 50, "overdraft_limit": 500},
        {"client": clients[3], "type": "bank", "balance": 400},
        {"client": clients[4], "type": "savings", "balance": 250, "min_balance": 20, "monthly_rate": 0.01},
        {"client": clients[4], "type": "investment", "balance": 150, "portfolio": {"stocks": 80, "bonds": 40, "etf": 30}},
        {"client": clients[5], "type": "bank", "balance": 600},
        {"client": clients[5], "type": "premium", "balance": 0, "overdraft_limit": 400},
        {"client": clients[5], "type": "savings", "balance": 150, "min_balance": 30, "monthly_rate": 0.012},
    ]

    accounts = []
    for definition in account_definitions:
        kwargs = definition.copy()
        client = kwargs.pop("client")
        acc_type = kwargs.pop("type")
        account = bank.open_account(client.client_id, account_type=acc_type, **kwargs)
        accounts.append(account)

    print("\nСозданы клиенты и счета:")
    for client in clients:
        _print_account_summary(client, bank)

    # Подготовка транзакций
    queue = TransactionQueue()

    def queue_tx(tx, priority=0, execute_at=None):
        queue.add(tx, priority=priority, execute_at=execute_at)
        print(f"Добавлена в очередь: {tx.tx_id} {tx.sender_id}->{tx.receiver_id} {tx.amount} {tx.currency.value} priority={priority} execute_at={execute_at}")

    # create a couple of suspicious / erroneous operations
    queue_tx(Transaction("transfer", 1000, Currency.RUB, sender_id=accounts[2].account_id, receiver_id=accounts[0].account_id))
    queue_tx(Transaction("transfer", 50, Currency.RUB, sender_id=accounts[4].account_id, receiver_id="invalid"))
    queue_tx(Transaction("transfer", 700, Currency.RUB, sender_id=accounts[9].account_id, receiver_id=accounts[5].account_id))
    queue_tx(Transaction("transfer", 30, Currency.RUB, sender_id=accounts[10].account_id, receiver_id=accounts[1].account_id))
    queue_tx(Transaction("transfer", 150, Currency.RUB, sender_id=accounts[0].account_id, receiver_id=accounts[3].account_id))
    queue_tx(Transaction("transfer", 200, Currency.RUB, sender_id=accounts[6].account_id, receiver_id=accounts[2].account_id))
    queue_tx(Transaction("transfer", 100, Currency.USD, sender_id=accounts[7].account_id, receiver_id=accounts[8].account_id))
    queue_tx(Transaction("transfer", 50, Currency.EUR, sender_id=accounts[9].account_id, receiver_id=accounts[4].account_id))

    # freeze one account to produce rejected operations
    frozen_target = accounts[1]
    bank.freeze_account(frozen_target.account_id)
    print(f"\nЗаморожен счёт: {frozen_target.account_id}")
    queue_tx(Transaction("transfer", 20, Currency.RUB, sender_id=frozen_target.account_id, receiver_id=accounts[0].account_id))

    # normal and suspicious transactions - ensure at least 30-50 total transactions
    tx_count = len(queue)
    target_transactions = 40  # Aim for 40 total (between 30-50)
    iterations_needed = max(40, target_transactions - tx_count)
    
    for i in range(iterations_needed):
        sender_idx = i % len(accounts)
        receiver_idx = (i + 1) % len(accounts)  # Ensure different account (no skip needed)
        sender = accounts[sender_idx]
        receiver = accounts[receiver_idx]
        
        amount = random.choice([20, 30, 50, 80, 120, 250, 600])
        tx = Transaction("transfer", amount, Currency.RUB, sender_id=sender.account_id, receiver_id=receiver.account_id)
        if i % 8 == 0:
            tx.created_at = tx.created_at.replace(hour=2)
        if i % 10 == 0:
            queue_tx(tx, priority=1)
        elif i % 7 == 0:
            queue_tx(tx, execute_at=datetime.now() + timedelta(seconds=1))
        else:
            queue_tx(tx)

    print(f"\nВсего в очереди: {len(queue)} транзакций")
    print("\nЗапуск обработки очереди транзакций...")
    processor = TransactionProcessor(bank)
    processed = processor.process_all(queue)

    for tx in processed:
        status = tx.status.value
        print(f"Транзакция {tx.tx_id}: {tx.sender_id}->{tx.receiver_id} {tx.amount} {tx.currency.value} => {status} ({tx.reason or 'OK'})")

    print("\nОсталось транзакций в очереди:", len(queue))
    print("\nПодозрительные действия:")
    for action in bank.suspicious_actions[:10]:
        print(f"  - {action['time']} {action['action']} {action['reason']}")

    print("\nТоп-3 клиентов по балансу:")
    for rank in bank.get_clients_ranking()[:3]:
        print(f"  - {rank['full_name']}: {rank['total_balance']}")

    print(f"\nОбщий баланс банка: {bank.get_total_balance():.2f}")
    _print_transaction_stats(bank)

    selected_client = clients[0]
    print(f"\nИстория клиента {selected_client.full_name}:")
    for tx in bank.transactions:
        if tx.sender_id in selected_client.account_ids or tx.receiver_id in selected_client.account_ids:
            print(f"  - {tx.tx_id} {tx.amount} {tx.currency.value} {tx.status.value}")

    report_builder = ReportBuilder(bank)
    report = report_builder.report_bank()
    print(f"\nСформирован банковский отчёт: accounts={len(report['accounts'])}, transactions={len(report['transactions'])}")

    print("\n=== Демо Day 6 завершено ===")

   

   
 


if __name__ == "__main__":
    run_demo_day6()



# День 7 - Система отчётности и визуализации


def run_demo_day7():
    print("=== Day 7 Demo: отчёты и визуализация ===")
    bank = Bank(name="Day7 Bank")
    bank.audit_log = AuditLog()
    bank.risk_analyzer = RiskAnalyzer(bank, large_amount=500, freq_threshold=3)

    client = bank.add_client(full_name="Ирина Петрова", age=30)
    account = bank.open_account(client.client_id, account_type="bank", balance=500)
    savings = bank.open_account(client.client_id, account_type="savings", balance=150, min_balance=20, monthly_rate=0.01)

    queue = TransactionQueue()
    queue.add(Transaction("transfer", 100, Currency.RUB, sender_id=account.account_id, receiver_id=savings.account_id))
    processor = TransactionProcessor(bank)
    processor.process_all(queue)

    report_builder = ReportBuilder(bank)
    client_report = report_builder.report_client(client.client_id)
    bank_report = report_builder.report_bank()
    risk_report = report_builder.report_risk()

    print(f"Клиент: {client_report['client']['full_name']}")
    print(f"Счета клиента: {len(client_report['accounts'])}")
    print(f"Транзакции клиента: {len(client_report['transactions'])}")
    print(f"Риски: {risk_report['risk_summary']['suspicious_count']} suspicious actions")

    # Export to various formats
    report_builder.export_to_json(client_report, "day7_client_report.json")
    report_builder.export_to_json(bank_report, "day7_bank_report.json")
    report_builder.export_to_json(risk_report, "day7_risk_report.json")
    report_builder.export_to_csv(client_report["transactions"], "day7_client_transactions.csv")
    
    # Export text reports
    report_builder.export_to_text(client_report, "day7_client_report.txt", report_type="client")
    report_builder.export_to_text(bank_report, "day7_bank_report.txt", report_type="bank")
    report_builder.export_to_text(risk_report, "day7_risk_report.txt", report_type="risk")
    
    # Save charts
    report_builder.save_charts(client.client_id, "day7_client")

    print("Сохранены файлы: day7_client_report.json, day7_bank_report.json, day7_risk_report.json, day7_client_transactions.csv")
    print("Сохранены текстовые отчёты: day7_client_report.txt, day7_bank_report.txt, day7_risk_report.txt")
    if plt is not None:
        print("Сохранены диаграммы: day7_client_balance_movement.png, day7_client_type_distribution.png, day7_client_status_amounts.png")




if __name__ == "__main__":
    run_demo_day7()