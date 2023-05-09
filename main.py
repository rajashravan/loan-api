from typing import Optional

from fastapi import FastAPI, HTTPException
import uuid
from pydantic import BaseModel

app = FastAPI()


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
            return loan_schedule[month-1]
        except IndexError:
            return None

    def transfer_to_user(self, user_id: uuid.UUID):
        self.user_id = user_id


# Dictionary for in-memory store for users. Key is user_id, value is list of user's loans.
users = {
    uuid.UUID('e0e95d7f-cf4b-4ed0-b1d3-ea73d6879be2'): [
        uuid.UUID('fca9f862-3f4c-4746-bc30-fd767a072963'),
    ],
}

# Dictionary for in-memory store for loans. Key is loan_id, value is loan object.
loans = {
    uuid.UUID('fca9f862-3f4c-4746-bc30-fd767a072963'): Loan(
        loan_id=uuid.UUID('fca9f862-3f4c-4746-bc30-fd767a072963'),
        user_id=uuid.UUID('e0e95d7f-cf4b-4ed0-b1d3-ea73d6879be2'),
        amount=1000,
        annual_interest_rate=10,
        loan_term=10,
    )
}


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


@app.get("/")
async def root():
    await tests()
    return {"message": "Hello World"}


@app.post("/users/")
async def create_user():
    new_user_id = uuid.uuid4()
    users[new_user_id] = []
    return {
        "created_user_id": str(new_user_id),
    }


@app.post("/loans/")
async def create_loan(loan_creation_request: LoanCreationRequest):
    error_message = validate_loan_creation_request(loan_creation_request)
    if error_message:
        raise HTTPException(status_code=400, detail=error_message)
    new_loan = create_loan_from_loan_creation_request(loan_creation_request)
    loans[new_loan.loan_id] = new_loan
    users[new_loan.user_id].append(new_loan.loan_id)
    return new_loan


@app.get("/loans/{loan_id}")
async def get_loan(loan_id: uuid.UUID):
    if loan_id not in loans:
        raise HTTPException(status_code=404, detail="Loan not found")

    return loans[loan_id].get_loan_metadata()


@app.get("/loans/")
async def get_loans_for_user(user_id: uuid.UUID):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    loan_ids_for_user = users[user_id]
    loans_for_user = []
    for loan_id in loan_ids_for_user:
        loans_for_user.append(loans[loan_id].get_loan_metadata())
    return loans_for_user


@app.get("/loans/{loan_id}/schedule")
async def get_loan_schedule(loan_id: uuid.UUID):
    if loan_id not in loans:
        raise HTTPException(status_code=404, detail="Loan not found")

    return loans[loan_id].get_loan_schedule()


@app.get("/loans/{loan_id}/summary/{month}")
async def get_loan_summary_for_month(loan_id: uuid.UUID, month: int):
    if loan_id not in loans:
        raise HTTPException(status_code=404, detail="Loan not found")

    summary = loans[loan_id].get_loan_summary_for_month(month)
    if not summary:
        raise HTTPException(status_code=400, detail=f"Month {month} does not exist in loan {loan_id}")
    return summary


@app.post("/loans/{loan_id}/share/")
async def share_loan_to_user(loan_id: uuid.UUID, user_id: uuid.UUID):
    """
    Interpretted this requirement from the doc as transferring a loan from one user to another.
    :param user_id: user_id to transfer the loan to
    :return:
    """

    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    if loan_id not in loans:
        raise HTTPException(status_code=404, detail="Loan not found")

    loan = loans[loan_id]
    loan.transfer_to_user(user_id)

    return loan


async def test_normal_flow():
    msg = await create_user()
    user_id = msg["created_user_id"]
    loan = Loan(loan_id=uuid.uuid4(), user_id=uuid.UUID(user_id), amount=10000, annual_interest_rate=10, loan_term=10)
    payments = loan.get_loan_schedule()
    expected_payments = [
        {'month': 1, 'remaining_balance': 9036.93, 'monthly_payment': 1046.4,
         'aggregate_principal_paid': 963.0699999999997, 'aggregate_interest_paid': 83.33},
        {'month': 2, 'remaining_balance': 8065.83, 'monthly_payment': 1046.41, 'aggregate_principal_paid': 1934.17,
         'aggregate_interest_paid': 158.64},
        {'month': 3, 'remaining_balance': 7086.64, 'monthly_payment': 1046.41,
         'aggregate_principal_paid': 2913.3599999999997, 'aggregate_interest_paid': 225.85999999999999},
        {'month': 4, 'remaining_balance': 6099.29, 'monthly_payment': 1046.41, 'aggregate_principal_paid': 3900.71,
         'aggregate_interest_paid': 284.91999999999996},
        {'month': 5, 'remaining_balance': 5103.71, 'monthly_payment': 1046.41, 'aggregate_principal_paid': 4896.29,
         'aggregate_interest_paid': 335.74999999999994},
        {'month': 6, 'remaining_balance': 4099.84, 'monthly_payment': 1046.4, 'aggregate_principal_paid': 5900.16,
         'aggregate_interest_paid': 378.28},
        {'month': 7, 'remaining_balance': 3087.6, 'monthly_payment': 1046.41, 'aggregate_principal_paid': 6912.4,
         'aggregate_interest_paid': 412.45},
        {'month': 8, 'remaining_balance': 2066.93, 'monthly_payment': 1046.3999999999999,
         'aggregate_principal_paid': 7933.07, 'aggregate_interest_paid': 438.18},
        {'month': 9, 'remaining_balance': 1037.75, 'monthly_payment': 1046.4, 'aggregate_principal_paid': 8962.25,
         'aggregate_interest_paid': 455.4},
        {'month': 10, 'remaining_balance': -0.01, 'monthly_payment': 1046.41, 'aggregate_principal_paid': 10000.01,
         'aggregate_interest_paid': 464.04999999999995},
    ]
    # for payment in payments:
    #     print(payment)
    assert payments == expected_payments

    loan_summary_month_1 = loan.get_loan_summary_for_month(1)
    assert loan_summary_month_1 == expected_payments[0]


async def tests():
    await test_normal_flow()

"""
TODO:
* tests
* proper HTTP verbage and endpoint naming and usage
"""