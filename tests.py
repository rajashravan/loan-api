import asyncio
from loans import LoanCreationRequest
from main import create_user, create_loan


async def test_normal_flow():
    user = await create_user()
    user_id = user['created_user_id']
    loan_creation_request = LoanCreationRequest(user_id=user_id, amount=10000, annual_interest_rate=10, loan_term=10)
    loan = await create_loan(loan_creation_request)
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
    assert payments == expected_payments

    loan_summary_month_1 = loan.get_loan_summary_for_month(1)
    assert loan_summary_month_1 == expected_payments[0]


async def tests():
    await test_normal_flow()


asyncio.run(tests())
