import unittest
import icecream as ic
from src.compute_resources.aws_iam_roles import IAMBatchServiceRole

class TestIAMRoles(unittest.TestCase):
    def test_something(self):
        bsr = IAMBatchServiceRole()
        ic(bsr.full_role_name())
        ic(bsr.create_role())
        ic(bsr.arn())
        ic(bsr.full_role_name())
        ic(bsr.create_role())
        ic(bsr.delete())
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
