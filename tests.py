import math
import unittest
import uuid
from fastapi import HTTPException

from loans import LoanCreationRequest
from main import create_user, create_loan, get_loan_summary_for_month, get_loan, get_loans_for_user, share_loan_to_user


# In our tests, we allow a margin of error of 1 penny.

class GreyStoneTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_integration_normal_flow(self):
        user = await create_user()
        user_id = user['created_user_id']
        loan_term = 10
        loan_creation_request = LoanCreationRequest(user_id=user_id, amount=10000, annual_interest_rate=10,
                                                    loan_term=loan_term)
        loan = await create_loan(loan_creation_request)
        payments = loan.get_loan_schedule()
        expected_payments = [
            {'month': 1, 'remaining_balance': 9036.93, 'monthly_payment': 1046.4,
             'aggregate_principal_paid': 963.07, 'aggregate_interest_paid': 83.33},
            {'month': 2, 'remaining_balance': 8065.83, 'monthly_payment': 1046.41, 'aggregate_principal_paid': 1934.17,
             'aggregate_interest_paid': 158.64},
            {'month': 3, 'remaining_balance': 7086.64, 'monthly_payment': 1046.41,
             'aggregate_principal_paid': 2913.36, 'aggregate_interest_paid': 225.86},
            {'month': 4, 'remaining_balance': 6099.29, 'monthly_payment': 1046.41, 'aggregate_principal_paid': 3900.71,
             'aggregate_interest_paid': 284.92},
            {'month': 5, 'remaining_balance': 5103.71, 'monthly_payment': 1046.41, 'aggregate_principal_paid': 4896.29,
             'aggregate_interest_paid': 335.75},
            {'month': 6, 'remaining_balance': 4099.84, 'monthly_payment': 1046.4, 'aggregate_principal_paid': 5900.16,
             'aggregate_interest_paid': 378.28},
            {'month': 7, 'remaining_balance': 3087.6, 'monthly_payment': 1046.41, 'aggregate_principal_paid': 6912.4,
             'aggregate_interest_paid': 412.45},
            {'month': 8, 'remaining_balance': 2066.93, 'monthly_payment': 1046.4,
             'aggregate_principal_paid': 7933.07, 'aggregate_interest_paid': 438.18},
            {'month': 9, 'remaining_balance': 1037.75, 'monthly_payment': 1046.4, 'aggregate_principal_paid': 8962.25,
             'aggregate_interest_paid': 455.4},
            {'month': 10, 'remaining_balance': 0, 'monthly_payment': 1046.41, 'aggregate_principal_paid': 10000,
             'aggregate_interest_paid': 464.05},
        ]
        for i in range(loan_term):
            payment = payments[i]
            expected_payment = expected_payments[i]
            assert math.isclose(payment['remaining_balance'], expected_payment['remaining_balance'], rel_tol=0.01)
            assert math.isclose(payment['monthly_payment'], expected_payment['monthly_payment'], rel_tol=0.01)
            assert math.isclose(payment['aggregate_principal_paid'], expected_payment['aggregate_principal_paid'],
                                rel_tol=0.01)
            assert math.isclose(payment['aggregate_interest_paid'], expected_payment['aggregate_interest_paid'],
                                rel_tol=0.01)

        # Loan Summary Tests
        loan_summary_month_1 = await get_loan_summary_for_month(loan.loan_id, 10)
        expected_summary_month_1 = expected_payments[9]
        assert math.isclose(loan_summary_month_1['remaining_balance'], expected_summary_month_1['remaining_balance'],
                            rel_tol=0.01)
        assert math.isclose(loan_summary_month_1['monthly_payment'], expected_summary_month_1['monthly_payment'],
                            rel_tol=0.01)
        assert math.isclose(loan_summary_month_1['aggregate_principal_paid'],
                            expected_summary_month_1['aggregate_principal_paid'],
                            rel_tol=0.01)
        assert math.isclose(loan_summary_month_1['aggregate_interest_paid'],
                            expected_summary_month_1['aggregate_interest_paid'],
                            rel_tol=0.01)

        loan_summary_month_too_low = loan.get_loan_summary_for_month(0)
        self.assertEqual(loan_summary_month_too_low, None)

        loan_summary_month_too_high = loan.get_loan_summary_for_month(11)
        self.assertEqual(loan_summary_month_too_high, None)

    async def test_get_loan(self):
        """
        Assert that loan metadata retrieved from get_loan endpoint contains all expected fields
        (i.e everything except loan_schedule)
        """
        user = await create_user()
        user_id = user['created_user_id']
        loan_creation_request = LoanCreationRequest(user_id=user_id, amount=4000, annual_interest_rate=10,
                                                    loan_term=12)
        create_loan_response = await create_loan(loan_creation_request)
        loan = await get_loan(create_loan_response.loan_id)

        self.assertEqual(loan['loan_id'], create_loan_response.loan_id)
        self.assertEqual(loan['user_id'], create_loan_response.user_id)
        self.assertTrue('loan_schedule' not in loan)

    async def test_get_loans_for_user(self):
        """
        Creates multiple loans for a user, expects that all loans are returned from get_loans_for_user endpoint
        """
        user = await create_user()
        user_id = user['created_user_id']
        loan_creation_request_1 = LoanCreationRequest(user_id=user_id, amount=10000, annual_interest_rate=10,
                                                      loan_term=10)
        create_loan_response_1 = await create_loan(loan_creation_request_1)
        loan_1 = await get_loan(create_loan_response_1.loan_id)

        loan_creation_request_2 = LoanCreationRequest(user_id=user_id, amount=10000, annual_interest_rate=10,
                                                      loan_term=10)
        create_loan_response_2 = await create_loan(loan_creation_request_2)
        loan_2 = await get_loan(create_loan_response_2.loan_id)

        expected_loans = [loan_1, loan_2]
        loans = await get_loans_for_user(uuid.UUID(user_id))

        self.assertListEqual(expected_loans, loans)

    async def test_share_loan_to_user(self):
        """
        Creates a loan for a user, transfers the loan to a different user
        """
        original_owner = await create_user()
        original_owner_id = original_owner['created_user_id']
        loan_creation_request = LoanCreationRequest(user_id=original_owner_id, amount=10000, annual_interest_rate=10,
                                                    loan_term=10)
        loan = await create_loan(loan_creation_request)
        self.assertEqual(loan.user_id, uuid.UUID(original_owner_id))

        new_owner = await create_user()
        new_owner_id = new_owner['created_user_id']

        await share_loan_to_user(loan.loan_id, uuid.UUID(new_owner_id))
        loan_after_share = await get_loan(loan.loan_id)
        self.assertEqual(loan_after_share['user_id'], uuid.UUID(new_owner_id))

        original_owner_loans = await get_loans_for_user(uuid.UUID(original_owner_id))
        self.assertEqual(original_owner_loans, [])

    async def test_invalid_user(self):
        """
        Test that a user cannot create a loan with an invalid user id
        """
        non_existent_user_id = str(uuid.uuid4())
        loan_creation_request = LoanCreationRequest(user_id=non_existent_user_id, amount=10000, annual_interest_rate=10,
                                                    loan_term=10)
        with self.assertRaises(HTTPException) as context:
            await create_loan(loan_creation_request)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, 'User not found')

    async def test_invalid_amount(self):
        """
        Test that a user cannot create a loan with an invalid amount
        """
        user = await create_user()
        user_id = user['created_user_id']
        loan_creation_request = LoanCreationRequest(user_id=user_id, amount=-10, annual_interest_rate=10,
                                                    loan_term=10)

        with self.assertRaises(HTTPException) as context:
            await create_loan(loan_creation_request)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, 'Loan Amount must be a positive number')

    async def test_invalid_interest_rate(self):
        """
        Test that a user cannot create a loan with an invalid amount
        """
        user = await create_user()
        user_id = user['created_user_id']
        loan_creation_request = LoanCreationRequest(user_id=user_id, amount=10, annual_interest_rate=-10,
                                                    loan_term=10)

        with self.assertRaises(HTTPException) as context:
            await create_loan(loan_creation_request)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, 'Interest Rate must be a positive number')

    async def test_loan_term_decimal_parsed_correctly(self):
        """
        Test that a loan term given as a float instead of an integer is rounded down
        """
        user = await create_user()
        user_id = user['created_user_id']
        loan_creation_request = LoanCreationRequest(user_id=user_id, amount=10, annual_interest_rate=10,
                                                    loan_term=10.999)

        loan = await create_loan(loan_creation_request)
        self.assertEqual(loan.loan_term, 10)


unittest.main()
