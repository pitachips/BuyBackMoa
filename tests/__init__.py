# from django.test.runner import DiscoverRunner
#
#
# class DBlessDiscoverRunner(DiscoverRunner):
#     """A test suite runner that does not set up and tear down a database."""
#
#     def setup_databases(self):
#         """Overrides DjangoTestSuiteRunner"""
#         pass
#
#     def teardown_databases(self, *args):
#         """Overrides DjangoTestSuiteRunner"""
#         pass
#


# settings.py 에 TEST_RUNNER = 'tests.DBlessDiscoverRunner' 도 등록
