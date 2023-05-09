import uuid
from typing import Optional
from pydantic import BaseModel


class LoanCreationRequest(BaseModel):
    user_id: str
    amount: float
    annual_interest_rate: float
    loan_term: int


class Loan:
    def __init__(self, loan_id: uuid.UUID, user_id: uuid.UUID, amount: float, annual_interest_rate: float,
                 loan_term: int):
        self.loan_id = loan_id
        self.user_id = user_id
        self.amount = amount
        self.annual_interest_rate = annual_interest_rate
        self.loan_term = loan_term
        self.loan_schedule = []

    def get_loan_metadata(self) -> dict:
        return {
            "loan_id": self.loan_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "annual_interest_rate": self.annual_interest_rate,
            "loan_term": self.loan_term,
        }

    @staticmethod
    def make_payment(principal_remaining, mpr, monthly_payment) -> dict:

        current_interest_payment = principal_remaining * mpr
        current_principal_payment = monthly_payment - current_interest_payment

        principal_remaining -= current_principal_payment

        return {
            "principal_remaining": round(principal_remaining, 2),
            "current_principal_payment": round(current_principal_payment, 2),
            "current_interest_payment": round(current_interest_payment, 2),
        }

    def get_loan_schedule(self) -> list:
        if self.loan_schedule:
            return self.loan_schedule

        apr = self.annual_interest_rate / 100
        mpr = apr / 12
        principal_remaining = self.amount
        term_remaining = self.loan_term

        monthly_payment = (principal_remaining * mpr) / (1 - (1 + mpr) ** -self.loan_term)

        total_interest_paid = 0
        payments = []

        while principal_remaining > 0 and term_remaining > 0:
            cur_payment = self.make_payment(principal_remaining, mpr, monthly_payment)
            principal_remaining = cur_payment['principal_remaining']
            term_remaining -= 1
            total_interest_paid += cur_payment['current_interest_payment']
            payments.append({
                "month": self.loan_term - term_remaining,
                "remaining_balance": principal_remaining,
                "monthly_payment": cur_payment['current_principal_payment'] + cur_payment['current_interest_payment'],
                "aggregate_principal_paid": self.amount - principal_remaining,
                "aggregate_interest_paid": total_interest_paid,
            })

        self.loan_schedule = payments
        return self.loan_schedule

    def get_loan_summary_for_month(self, month: int) -> Optional[dict]:
        """
        Get the loan summary for a given month.
        :param month: Month to get the loan summary for.
        :return: Loan summary for a given month as a dictionary. Else None if month does not exist.
        """
        loan_schedule = self.get_loan_schedule()
        try:
            return loan_schedule[month - 1]
        except IndexError:
            return None

    def transfer_to_user(self, user_id: uuid.UUID):
        self.user_id = user_id


def create_loan_from_loan_creation_request(loan_creation_request: LoanCreationRequest) -> Loan:
    user_id = uuid.UUID(loan_creation_request.user_id)
    amount = loan_creation_request.amount
    annual_interest_rate = loan_creation_request.annual_interest_rate
    loan_term = loan_creation_request.loan_term
    loan_id = uuid.uuid4()
    loan = Loan(loan_id, user_id, amount, annual_interest_rate, loan_term)
    return loan


def validate_loan_creation_request(loan_creation_request: LoanCreationRequest) -> Optional[str]:
    """
    Validate the loan creation request. Returns
    :param loan_creation_request:
    :return: Error message string if validation fails, else None.
    """
    if uuid.UUID(loan_creation_request.user_id) not in users:
        return "User not found"
    if loan_creation_request.amount <= 0:
        return "Loan Amount must be a positive number"
    if loan_creation_request.annual_interest_rate <= 0:
        return "Interest Rate must be a positive number"
    if loan_creation_request.loan_term <= 0:
        return "Loan Term must be a positive number"
    return None