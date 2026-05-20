import unittest


class ImportTests(unittest.TestCase):
    def test_public_packages_import(self):
        import lima_office
        import lima_office.contracts
        import lima_office.evidence
        import lima_office.guardian
        import lima_office.runtime
        import lima_office.supervisor

        self.assertIn("phase1a", lima_office.__version__)


if __name__ == "__main__":
    unittest.main()
