import uuid
from fastapi import FastAPI, HTTPException
from loans import Loan, LoanCreationRequest, validate_loan_creation_request, create_loan_from_loan_creation_request

app = FastAPI()

# Dictionary for in-memory store for users. Key is user_id, value is list of user's loans. Seeded with example data.
users = {
    uuid.UUID('e0e95d7f-cf4b-4ed0-b1d3-ea73d6879be2'): [
        uuid.UUID('fca9f862-3f4c-4746-bc30-fd767a072963'),
    ],
}

# Dictionary for in-memory store for loans. Key is loan_id, value is loan object. Seeded with example data.
loans = {
    uuid.UUID('fca9f862-3f4c-4746-bc30-fd767a072963'): Loan(
        loan_id=uuid.UUID('fca9f862-3f4c-4746-bc30-fd767a072963'),
        user_id=uuid.UUID('e0e95d7f-cf4b-4ed0-b1d3-ea73d6879be2'),
        amount=1000,
        annual_interest_rate=10,
        loan_term=10,
    )
}


def validate_loan_exists(loan_id: uuid.UUID):
    if loan_id not in loans:
        raise HTTPException(status_code=400, detail="Loan not found")


def validate_user_exists(user_id: uuid.UUID):
    if user_id not in users:
        raise HTTPException(status_code=400, detail="User not found")


@app.get("/")
async def root():
    return {"message": "Welcome to the Greystone Labs Loan API!"}


@app.post("/users/")
async def create_user():
    new_user_id = uuid.uuid4()
    users[new_user_id] = []
    return {
        "created_user_id": str(new_user_id),
    }


@app.post("/loans/")
async def create_loan(loan_creation_request: LoanCreationRequest):
    validate_user_exists(uuid.UUID(loan_creation_request.user_id))
    error_message = validate_loan_creation_request(loan_creation_request)
    if error_message:
        raise HTTPException(status_code=400, detail=error_message)

    new_loan = create_loan_from_loan_creation_request(loan_creation_request)
    loans[new_loan.loan_id] = new_loan
    users[new_loan.user_id].append(new_loan.loan_id)
    return new_loan


@app.get("/loans/{loan_id}")
async def get_loan(loan_id: uuid.UUID):
    validate_loan_exists(loan_id)

    return loans[loan_id].get_loan_metadata()


@app.get("/loans/")
async def get_loans_for_user(user_id: uuid.UUID):
    validate_user_exists(user_id)

    loan_ids_for_user = users[user_id]
    loans_for_user = []
    for loan_id in loan_ids_for_user:
        loans_for_user.append(loans[loan_id].get_loan_metadata())

    return loans_for_user


@app.get("/loans/{loan_id}/schedule")
async def get_loan_schedule(loan_id: uuid.UUID):
    validate_loan_exists(loan_id)

    return loans[loan_id].get_loan_schedule()


@app.get("/loans/{loan_id}/summary/{month}")
async def get_loan_summary_for_month(loan_id: uuid.UUID, month: int):
    validate_loan_exists(loan_id)

    summary = loans[loan_id].get_loan_summary_for_month(month)
    if not summary:
        raise HTTPException(status_code=400, detail=f"Month {month} does not exist in loan {loan_id}")

    return summary


@app.put("/loans/{loan_id}/share/")
async def share_loan_to_user(loan_id: uuid.UUID, user_id: uuid.UUID):
    """
    Interpretted this requirement from the doc as: transferring a loan from one user to another.
    :param loan_id: loan_id of loan to transfer
    :param user_id: user_id to transfer the loan to
    :return: Transferred Loan
    """

    validate_loan_exists(loan_id)
    validate_user_exists(user_id)

    loan = loans[loan_id]
    previous_owner_id = loan.user_id
    users[previous_owner_id].remove(loan.loan_id)

    loan.transfer_to_user(user_id)
    users[loan.user_id].append(loan.loan_id)

    return loan
