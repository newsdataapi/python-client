import os,unittest,datetime
from newsdataapi import NewsDataApiClient

class test_newsdataapi(unittest.TestCase):

    def setUp(self):
        # your private API key.
        key = os.environ.get("PYTEST_TOKEN")
        self.api = NewsDataApiClient(apikey=key)

    def test_news_api(self):
        response = self.api.news_api()

        self.assertEqual(response['status'], "success")

    def test_latest_api(self):
        response = self.api.latest_api()

        self.assertEqual(response['status'], "success")

    def test_archive_api(self):
        response = self.api.archive_api(q='news')

        self.assertEqual(response['status'], "success")

    def test_sources_api(self):
        response = self.api.sources_api()

        self.assertEqual(response['status'], "success")

    def test_crypto_api(self):
        response = self.api.crypto_api(q='bitcoin')

        self.assertEqual(response['status'], "success")

    def test_market_api(self):
        response = self.api.market_api()
        self.assertEqual(response['status'], "success")

    def test_count_api(self):
        current_dt = datetime.datetime.now()
        from_date = (current_dt - datetime.timedelta(days=30)).strftime('%Y-%m-%d 00:00:00')
        to_date = current_dt.strftime('%Y-%m-%d 00:00:00')
        parms = {'language':'en','from_date':from_date,'to_date':to_date,}
        response = self.api.count_api(**parms)
        self.assertEqual(response['status'], "success")

    def test_crypto_count_api(self):
        current_dt = datetime.datetime.now()
        from_date = (current_dt - datetime.timedelta(days=30)).strftime('%Y-%m-%d 00:00:00')
        to_date = current_dt.strftime('%Y-%m-%d 00:00:00')
        parms = {'language':'en','from_date':from_date,'to_date':to_date,}
        response = self.api.crypto_count_api(**parms)
        self.assertEqual(response['status'], "success")

    def test_market_count_api(self):
        current_dt = datetime.datetime.now()
        from_date = (current_dt - datetime.timedelta(days=30)).strftime('%Y-%m-%d 00:00:00')
        to_date = current_dt.strftime('%Y-%m-%d 00:00:00')
        parms = {'language':'en','from_date':from_date,'to_date':to_date,}
        response = self.api.market_count_api(**parms)
        self.assertEqual(response['status'], "success")
