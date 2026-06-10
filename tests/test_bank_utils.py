import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Mock the database module before importing bank_utils
mock_db = MagicMock()
sys.modules['database'] = mock_db

# Mock psycopg2 and telegram if needed (though bank_utils only imports from database)
sys.modules['psycopg2'] = MagicMock()
sys.modules['telegram'] = MagicMock()
sys.modules['telegram.ext'] = MagicMock()

import utils.bank_utils as bank_utils

class TestBankUtils(unittest.TestCase):

    def test_simulate_bank_deposit_success(self):
        """Test successful simulation of a bank deposit."""
        # Setup mocks
        mock_db.get_user.return_value = {'user_id': 123, 'naira_balance': 1000}
        
        result = bank_utils.simulate_bank_deposit(123, 5000.0)
        
        self.assertTrue(result)
        mock_db.update_balance.assert_called_with(123, naira_delta=5000.0)
        mock_db.add_transaction.assert_called()
        args, kwargs = mock_db.add_transaction.call_args
        self.assertEqual(kwargs['tx_type'], 'deposit')
        self.assertEqual(kwargs['amount'], 5000.0)

    def test_simulate_bank_deposit_user_not_found(self):
        """Test deposit simulation fails if user does not exist."""
        mock_db.get_user.return_value = None
        
        result = bank_utils.simulate_bank_deposit(999, 1000.0)
        
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
