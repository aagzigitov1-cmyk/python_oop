# День 1 — Базовая модель банковских счетов (усложнённый вариант)

from abc import ABC, abstractmethod
from enum import Enum
import uuid

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

    def get_account_info(self):
        return {
            "account_id": self.account_id,
            "owner": self.owner,
            "balance": self._balance,
            "currency": self.currency.value,
            "status": self.status.value
        }
        
    def deposit(self, amount):
        self._check_status()
        self._validate_amount(amount)

        self._balance += amount

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