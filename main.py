from typing import Optional

from fastapi import FastAPI, HTTPException
import uuid
from pydantic import BaseModel

app = FastAPI()


users = {
    uuid.UUID('e0e95d7f-cf4b-4ed0-b1d3-ea73d6879be2'): 0
}  # key is user_id. no value needed.

loans = {}


class LoanCreationRequest(BaseModel):
    user_id: str
    amount: float
    annual_interest_rate: float
    loan_term: int


def validate_loan_creation_request(loan_creation_request: LoanCreationRequest) -> Optional[str]:
    if uuid.UUID(loan_creation_request.user_id) not in users:
        return "User not found"
    if loan_creation_request.amount <= 0:
        return "Loan Amount must be a positive number"
    if loan_creation_request.annual_interest_rate <= 0:
        return "Interest Rate must be a positive number"
    if loan_creation_request.loan_term <= 0 or not isinstance(loan_creation_request.loan_term, int):
        return "Loan Term must be a positive integer"
    return None


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/users/")
async def create_user():
    new_user_id = uuid.uuid4()
    users[new_user_id] = 0
    return {"message": f"Created user {new_user_id}"}


@app.post("/loans/")
async def create_loan(loan_creation_request: LoanCreationRequest):
    error_message = validate_loan_creation_request(loan_creation_request)
    if error_message:
        raise HTTPException(status_code=400, detail=error_message)
    return loan_creation_request



