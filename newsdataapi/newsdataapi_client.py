from warnings import warn
from typing import Optional
import requests,time,logging
from newsdataapi import constants
from typing import Dict, Any, List,Union
from newsdataapi.helpers import FileHandler
from requests.exceptions import RequestException
from newsdataapi.newsdataapi_exception import NewsdataException
from urllib.parse import urlencode, quote,urlparse,parse_qs,urljoin

logger = logging.getLogger(__name__)

class NewsDataApiClient(FileHandler):

    def __init__(
            self, 
            apikey: str, 
            session: Optional[bool] = False, 
            proxies: Optional[Dict[str, Any]] = None, 
            max_retries: Optional[int] = constants.DEFAULT_MAX_RETRIES, 
            retry_delay: Optional[int] = constants.DEFAULT_RETRY_DELAY,
            pagination_delay: Optional[int] = constants.PAGINATION_DELAY,
            request_timeout: Optional[int] = constants.DEFAULT_REQUEST_TIMEOUT, 
            max_result: Optional[int] = 10**10,
            max_pages: Optional[int] = 10**10,
            debug: Optional[bool] = False,
            folder_path: Optional[str] = None, 
            include_headers: Optional[bool] = False
        ) -> None:
        """Initializes newsdata client object for access Newsdata APIs."""
        self.apikey = apikey
        self.request_method = requests.Session() if session else requests
        self.max_result = max_result
        self.max_pages = max_pages
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.pagination_delay = pagination_delay
        self.proxies = proxies
        self.request_timeout = request_timeout
        # self.is_debug = debug
        self.include_headers = include_headers
        self.set_base_url()
        super().__init__(folder_path=folder_path)
        logger.info("NewsDataApiClient initialized successfully.")
    
    def set_base_url(self,new_base_url:Optional[str]=constants.BASE_URL)->None:
        self.latest_url = urljoin(new_base_url,constants.LATEST_ENDPOINT)
        self.archive_url = urljoin(new_base_url,constants.ARCHIVE_ENDPOINT)
        self.crypto_url = urljoin(new_base_url,constants.CRYPTO_ENDPOINT)
        self.sources_url = urljoin(new_base_url,constants.SOURCES_ENDPOINT)
        self.count_url = urljoin(new_base_url,constants.COUNT_ENDPOINT)
        self.crypto_count_url = urljoin(new_base_url,constants.CRYPTO_COUNT_ENDPOINT)
        self.market_url = urljoin(new_base_url,constants.MARKET_ENDPOINT)
        self.market_count_url = urljoin(new_base_url,constants.MARKET_COUNT_ENDPOINT)

    def set_retries( self, max_retries:int, retry_delay:int)->None:
        """ API maximum retry and delay"""
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        logger.info(f"Set max_retries to {max_retries} and retry_delay to {retry_delay} seconds.")

    def set_request_timeout( self, request_timeout:int)->None:
        """ API maximum timeout for the request """
        self.request_timeout = request_timeout
        logger.info(f"Set request_timeout to {request_timeout} seconds.")

    def api_proxies( self, proxies:dict)->None:
        """ Configure Proxie dictionary """
        self.proxies = proxies
        logger.info(f"Proxies set to: {proxies}")
    
    def set_pagination_delay( self, pagination_delay:int)->None:
        """ Set delay between paginated requests """
        self.pagination_delay = pagination_delay
        logger.info(f"Set pagination_delay to {pagination_delay} seconds.")

    def __validate_parms(self, user_param: Dict[str, Any]) -> Dict[str, Any]:
        bool_params = {'full_content','image','video','removeduplicate'}
        int_params = {'size'}
        string_params = {
            'q','qInTitle','country','category','language','domain','domainurl','excludedomain','timezone',
            'from_date','to_date','qInMeta','prioritydomain','timeframe','tag','sentiment','region','coin',
            'excludefield','excludecategory','id','excludelanguage','organization','url','sort','symbol',
            'excludecountry','page','interval'
        }
        
        def validate_url(url:str)-> str:
            valid_fn_parms = {k.lower() for k in user_param.keys()}
            parsed_url = urlparse(url)
            if parsed_url.netloc:
                q_string = parse_qs(parsed_url.query)
            else:
                q_string = parse_qs(url)
            
            valid_q_string = {}
            for k,v in q_string.items():
                k = k.strip().strip('%').strip('?').lower()
                if k in valid_fn_parms:
                    valid_q_string[k] = v[0]
                else:
                    raise TypeError(f'Provided parameter is invalid: {k}')
            
            return valid_q_string
        
        if user_param.get('raw_query'):
            value = user_param['raw_query']
            if not isinstance(value,str):
                raise TypeError('raw_query should be of type string.')
            return validate_url(url=value)

        valid_parms = {}
        for param,value in user_param.items():
            if value is None:
                continue
            
            if param in string_params:
                if isinstance(value,list):
                    value = ','.join(value)
                if not isinstance(value,str):
                    raise TypeError(f'{param} should be of type string.')
            elif param in bool_params:
                if not isinstance(value,bool):
                    raise TypeError(f'{param} should be of type bool.')
                value = 1 if value == True else 0
            elif param in int_params:
                if not isinstance(value,int):
                    raise TypeError(f'{param} should be of type int.')
            
            valid_parms[param] = value

        return valid_parms
    
    def __get_feeds(self, endpoint: str, query_params: dict) -> Dict[str, Any]:
        for retry_count in range(1,self.max_retries+1):
            try:
                s_time = time.perf_counter()
                params = query_params.copy()
                params['apikey'] = self.apikey
                url = f"{endpoint}?{urlencode(params, quote_via=quote)}"

                logger.info(f"Fetching data from URL: {url}")
                response = self.request_method.get(url=url, proxies=self.proxies, timeout=self.request_timeout)
                logger.info(f"Time taken to fetch data: {time.perf_counter() - s_time:.2f} seconds")

                X_API_Limit_Remaining = response.headers.get("X-API-Limit-Remaining")
                X_RateLimit_Remaining = response.headers.get("X-RateLimit-Remaining")
                logger.info(f"X-API-Limit-Remaining: {X_API_Limit_Remaining}, X-RateLimit-Remaining: {X_RateLimit_Remaining}")

                feeds_data: dict = response.json()
                
                if (
                    response.status_code == 200 
                    and feeds_data.get('status') == 'success' 
                    and feeds_data.get('results') is not None
                ):
                    if self.include_headers:
                        feeds_data['response_headers'] = dict(response.headers)
                    return feeds_data

                elif response.status_code == 500:
                    logger.error(f"Encountered 'ServerError' - sleeping for {self.retry_delay}s. (Attempt {retry_count}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                    continue

                elif response.status_code == 429:
                    Retry_After = int(response.headers.get("Retry-After", self.retry_delay))
                    logger.error(f"Rate limit exceeded - sleeping for {Retry_After}s. (Attempt {retry_count}/{self.max_retries})")
                    time.sleep(Retry_After)
                    continue

                else:
                    raise NewsdataException(feeds_data)
            
            except NewsdataException as e:
                raise e

            except RequestException as e:
                logger.error(f"ConnectionError on attempt {retry_count}/{self.max_retries}: {e}. Sleeping {self.retry_delay}s.")
                time.sleep(self.retry_delay)
            
            except Exception as e:
                logger.error(f"Unexpected error on attempt {retry_count}/{self.max_retries}: {e}. Sleeping {self.retry_delay}s.")
                time.sleep(self.retry_delay)

        raise NewsdataException(f"Maximum retry limit reached: {self.max_retries}.")

    def __get_feeds_all(self, endpoint:str,query_params:dict, max_result: Optional[int] = None) -> Dict[str, Any]:

        if max_result is None:
            max_result = self.max_result
        
        self.request_method = requests.Session()
        logger.info('Switched to Session for scrolling through all results.')

        data = {'totalResults':None,'results':[],'nextPage':None}
        while True:
            response:dict = self.__get_feeds(endpoint=endpoint,query_params=query_params)
            data['totalResults'] = response.get('totalResults')
            data['results'].extend(response.get('results',[]))
            data['nextPage'] = response.get('nextPage')

            query_params['page'] = data['nextPage']
                
            if self.include_headers:
                data['response_headers'] = response.get('response_headers')
        
            logger.info(f"Total results: {data['totalResults']} | Extracted: {len(data['results'])}")
            
            if not data['nextPage']:
                return data
            
            if max_result and len(data['results']) >= max_result:
                return data

            time.sleep(self.pagination_delay)

    def __paginate_results(self,endpoint:str,query_params:dict,max_pages: Optional[int] = None, is_count: Optional[bool] = False):
        if max_pages is None:
            max_pages = self.max_pages

        self.request_method = requests.Session()
        logger.info('Switched to Session for paginating through results.')

        current_result_count = 0
        page = 0
        while True:
            response = self.__get_feeds(endpoint=endpoint,query_params=query_params)
            results = response.get('results')
            if is_count:
                if isinstance(results, dict):
                    yield response
                    return
                
                current_result_count += len(results)
                page += 1
                logger.info(f"Result fetched: {current_result_count}, Page: {page}")
                yield response
            else:
                current_result_count += len(results)
                page += 1
                logger.info(f"Total result: {response['totalResults']}, Current result count: {current_result_count}, Page: {page}")
                yield response
            
            if page >= max_pages:
                logger.info(f"Reached maximum page limit: {max_pages}, ending pagination.")
                return
            
            if response['nextPage'] is None:
                logger.info("No more pages to fetch, ending pagination.")
                return
            
            query_params['page'] = response['nextPage']
            time.sleep(self.pagination_delay)

    def news_api(
            self, 
            q:Optional[str]=None, 
            qInTitle:Optional[str]=None, 
            country:Optional[Union[str, List[str]]]=None, 
            category:Optional[Union[str, List[str]]]=None,
            language:Optional[Union[str, List[str]]]=None, 
            domain:Optional[Union[str, List[str]]]=None, 
            timeframe:Optional[Union[int, str]]=None, 
            size:Optional[int]=None,
            domainurl:Optional[Union[str, List[str]]]=None, 
            excludedomain:Optional[Union[str, List[str]]]=None, 
            timezone:Optional[str]=None, 
            full_content:Optional[bool]=None,
            image:Optional[bool]=None, 
            video:Optional[bool]=None, 
            prioritydomain:Optional[str]=None, 
            page:Optional[str]=None, 
            scroll:Optional[bool]=False,
            max_result:Optional[int]=None, 
            qInMeta:Optional[str]=None, 
            tag:Optional[Union[str, List[str]]]=None, 
            sentiment:Optional[str]=None,
            region:Optional[Union[str, List[str]]]=None,
            excludefield:Optional[Union[str, List[str]]]=None,
            removeduplicate:Optional[bool]=None,
            raw_query:Optional[str]=None
        )->dict:
        """
        Sending GET request to the news api.
        For more information about parameters and input, Please visit our documentation page: https://newsdata.io/documentation
        """
        warn('This method is deprecated and will be removed in upcoming updates, Instead use latest_api()', DeprecationWarning, stacklevel=2)
        params = {
            'q':q,
            'qInTitle':qInTitle,
            'country':country,
            'category':category,
            'language':language,
            'domain':domain,
            'timeframe':str(timeframe) if timeframe else timeframe,
            'size':size,
            'domainurl':domainurl,
            'excludedomain':excludedomain,
            'timezone':timezone,
            'full_content':full_content,
            'image':image,
            'video':video,
            'prioritydomain':prioritydomain,
            'page':page,
            'qInMeta':qInMeta,
            'tag':tag, 
            'sentiment':sentiment, 
            'region':region,
            'excludefield':excludefield,
            'removeduplicate':removeduplicate,
            'raw_query':raw_query
        }
        URL_parameters = self.__validate_parms(user_param=params)
        if scroll:
            return self.__get_feeds_all(endpoint=self.latest_url,query_params=URL_parameters,max_result=max_result)
        else:
            return self.__get_feeds(endpoint=self.latest_url,query_params=URL_parameters)
    
    def latest_api(
            self, 
            q: Optional[str] = None, 
            qInTitle: Optional[str] = None, 
            qInMeta: Optional[str] = None, 
            country: Optional[Union[str, List[str]]] = None, 
            excludecountry: Optional[Union[str, List[str]]] = None,
            category: Optional[Union[str, List[str]]] = None,
            language: Optional[Union[str, List[str]]] = None, 
            domain: Optional[Union[str, List[str]]] = None, 
            domainurl: Optional[Union[str, List[str]]] = None, 
            prioritydomain: Optional[str] = None, 
            excludedomain: Optional[Union[str, List[str]]] = None, 
            timeframe: Optional[Union[int, str]] = None, 
            size: Optional[int] = None,
            timezone: Optional[str] = None, 
            full_content: Optional[bool] = None,
            image: Optional[bool] = None, 
            video: Optional[bool] = None, 
            page: Optional[str] = None, 
            tag: Optional[Union[str, List[str]]] = None, 
            sentiment: Optional[str] = None,
            region: Optional[Union[str, List[str]]] = None, 
            excludefield: Optional[Union[str, List[str]]] = None, 
            removeduplicate: Optional[bool] = None, 
            excludecategory: Optional[Union[str, List[str]]] = None, 
            id: Optional[str] = None, 
            excludelanguage: Optional[Union[str, List[str]]] = None,
            organization: Optional[Union[str, List[str]]] = None, 
            url: Optional[str] = None, 
            sort: Optional[str] = None,

            raw_query: Optional[str] = None,
            max_result: Optional[int] = None, 
            scroll: Optional[bool] = False,
            paginate: Optional[bool] = False,
            max_pages: Optional[int] = None,
        ) -> Dict[str, Any]:
        """ 
            Sending GET request to the latest api.
            For more information about parameters and input, Please visit our documentation page: https://newsdata.io/documentation
        """
        params = {
            'q':q,
            'qInTitle':qInTitle,
            'country':country,
            'excludecountry':excludecountry,
            'category':category,
            'language':language,
            'domain':domain,
            'timeframe':str(timeframe) if timeframe else timeframe,
            'size':size,
            'domainurl':domainurl,
            'excludedomain':excludedomain,
            'timezone':timezone,
            'full_content':full_content,
            'image':image,
            'video':video,
            'prioritydomain':prioritydomain,
            'page':page,
            'qInMeta':qInMeta,
            'tag':tag, 
            'sentiment':sentiment, 
            'region':region,
            'excludefield':excludefield,
            'removeduplicate':removeduplicate,
            'raw_query':raw_query,
            'excludecategory':excludecategory,
            'id':id, 
            'excludelanguage':excludelanguage, 
            'organization':organization, 
            'url':url, 
            'sort':sort
        }
        if scroll and paginate:
            raise NewsdataException("Both 'scroll' and 'paginate' cannot be True at the same time.")
        
        URL_parameters = self.__validate_parms(user_param=params)
        if scroll:
            return self.__get_feeds_all(endpoint=self.latest_url,query_params=URL_parameters,max_result=max_result)
        elif paginate:
            return self.__paginate_results(endpoint=self.latest_url,query_params=URL_parameters,max_pages=max_pages)
        else:
            return self.__get_feeds(endpoint=self.latest_url,query_params=URL_parameters)

    def archive_api(
            self, 
            q: Optional[str] = None, 
            qInTitle: Optional[str] = None, 
            country: Optional[Union[str, List[str]]] = None, 
            excludecountry: Optional[Union[str, List[str]]] = None,
            category: Optional[Union[str, List[str]]] = None,
            language: Optional[Union[str, List[str]]] = None, 
            domain: Optional[Union[str, List[str]]] = None, 
            size: Optional[int] = None, 
            domainurl: Optional[Union[str, List[str]]] = None,
            excludedomain: Optional[Union[str, List[str]]] = None, 
            timezone: Optional[str] = None, 
            full_content: Optional[bool] = None, 
            image: Optional[bool] = None,
            video: Optional[bool] = None, 
            prioritydomain: Optional[str] = None, 
            page: Optional[str] = None, 
            from_date: Optional[str] = None, 
            to_date: Optional[str] = None, 
            qInMeta: Optional[str] = None, 
            excludefield: Optional[Union[str, List[str]]] = None, 
            excludecategory: Optional[Union[str, List[str]]] = None, 
            id: Optional[str] = None, 
            excludelanguage: Optional[Union[str, List[str]]] = None,
            url: Optional[str] = None, 
            sort: Optional[str] = None,

            raw_query: Optional[str] = None,
            scroll: Optional[bool] = False, 
            max_result: Optional[int] = None,
            paginate: Optional[bool] = False,
            max_pages: Optional[int] = None,
        ) -> Dict[str, Any]:
        """
        Sending GET request to the archive api
        For more information about parameters and input, Please visit our documentation page: https://newsdata.io/documentation
        """
        params = {
            'q':q,
            'qInTitle':qInTitle,
            'country':country,
            'excludecountry':excludecountry,
            'category':category,
            'language':language,
            'domain':domain,
            'size':size,
            'domainurl':domainurl,
            'excludedomain':excludedomain,
            'timezone':timezone,
            'full_content':full_content,
            'image':image,
            'video':video,
            'prioritydomain':prioritydomain,
            'page':page,
            'from_date':from_date,
            'to_date':to_date,
            'qInMeta':qInMeta,
            'excludefield':excludefield,
            'raw_query':raw_query,
            'excludecategory':excludecategory,
            'id':id,
            'excludelanguage':excludelanguage, 
            'url':url, 
            'sort':sort
        }
        if scroll and paginate:
            raise NewsdataException("Both 'scroll' and 'paginate' cannot be True at the same time.")
        
        URL_parameters = self.__validate_parms(user_param=params)
        if scroll:
            return self.__get_feeds_all(endpoint=self.archive_url,query_params=URL_parameters,max_result=max_result)
        elif paginate:
            return self.__paginate_results(endpoint=self.archive_url,query_params=URL_parameters,max_pages=max_pages)
        else:
            return self.__get_feeds(endpoint=self.archive_url,query_params=URL_parameters)
    
    def sources_api(
            self, 
            country:  Optional[Union[str, List[str]]]= None, 
            category: Optional[Union[str, List[str]]] = None, 
            language: Optional[Union[str, List[str]]] = None, 
            prioritydomain: Optional[str] = None,
            domainurl: Optional[Union[str, List[str]]] = None,

            raw_query: Optional[str] = None
        ) -> Dict[str, Any]:
        """ 
        Sending GET request to the sources api
        For more information about parameters and input, Please visit our documentation page: https://newsdata.io/documentation
        """
        params = {
            'country':country,
            'category':category,
            'language':language,
            'prioritydomain':prioritydomain,
            'domainurl':domainurl,
            'raw_query':raw_query
        }
        URL_parameters = self.__validate_parms(user_param=params)
        return self.__get_feeds(endpoint=self.sources_url,query_params=URL_parameters)

    def crypto_api(
            self, 
            q: Optional[str] = None, 
            qInTitle: Optional[str] = None, 
            language: Optional[Union[str, List[str]]] = None, 
            domain: Optional[Union[str, List[str]]] = None,
            timeframe: Optional[Union[int, str]] = None, 
            size: Optional[int] = None, 
            domainurl: Optional[Union[str, List[str]]] = None, 
            excludedomain: Optional[Union[str, List[str]]] = None,
            timezone: Optional[str] = None, 
            full_content: Optional[bool] = None, 
            image: Optional[bool] = None, 
            video: Optional[bool] = None, 
            prioritydomain: Optional[str] = None, 
            page: Optional[str] = None, 
            qInMeta: Optional[str] = None, 
            tag: Optional[Union[str, List[str]]] = None, 
            sentiment: Optional[str] = None, 
            coin: Optional[Union[str, List[str]]] = None,
            excludefield: Optional[Union[str, List[str]]] = None, 
            from_date: Optional[str] = None, 
            to_date: Optional[str] = None,
            removeduplicate: Optional[bool] = None, 
            raw_query: Optional[str] = None, 
            id: Optional[str] = None,
            excludelanguage: Optional[Union[str, List[str]]] = None, 
            url: Optional[str] = None, 
            sort: Optional[str] = None,

            scroll: Optional[bool] = False, 
            max_result: Optional[int] = None, 
            paginate: Optional[bool] = False,
            max_pages: Optional[int] = None,
        ) -> Dict[str, Any]:
        """ 
        Sending GET request to the crypto api
        For more information about parameters and input, Please visit our documentation page: https://newsdata.io/documentation
        """

        params = {
            'q':q,
            'qInTitle':qInTitle,
            'language':language,
            'domain':domain,
            'size':size,
            'domainurl':domainurl,
            'excludedomain':excludedomain,
            'timezone':timezone,
            'full_content':full_content,
            'image':image,
            'video':video,
            'prioritydomain':prioritydomain,
            'page':page,
            'timeframe':str(timeframe) if timeframe else timeframe,
            'qInMeta':qInMeta,
            'tag':tag, 
            'sentiment':sentiment,
            'coin':coin,
            'excludefield':excludefield,
            'from_date':from_date,
            'to_date':to_date,
            'removeduplicate':removeduplicate,
            'raw_query':raw_query,
            'id':id,
            'excludelanguage':excludelanguage, 
            'url':url, 
            'sort':sort
        }
        if scroll and paginate:
            raise NewsdataException("Both 'scroll' and 'paginate' cannot be True at the same time.")
        
        URL_parameters = self.__validate_parms(user_param=params)
        if scroll:
            return self.__get_feeds_all(endpoint=self.crypto_url,query_params=URL_parameters,max_result=max_result)
        elif paginate:
            return self.__paginate_results(endpoint=self.crypto_url,query_params=URL_parameters,max_pages=max_pages)
        else:
            return self.__get_feeds(endpoint=self.crypto_url,query_params=URL_parameters)

    def market_api(
        self, 
        q: Optional[str] = None, 
        qInTitle: Optional[str] = None, 
        qInMeta: Optional[str] = None, 
        from_date: Optional[str] = None,
        to_date: Optional[str] = None, 
        domain: Optional[str] = None, 
        language: Optional[Union[str, List[str]]] = None, 
        page: Optional[str] = None,
        full_content: Optional[bool] = None, 
        image: Optional[bool] = None,
        video: Optional[bool] = None, 
        timeframe: Optional[Union[int, str]] = None, 
        prioritydomain: Optional[str] = None, 
        timezone: Optional[str] = None,
        size: Optional[int] = None, 
        domainurl: Optional[Union[str, List[str]]] = None, 
        excludedomain: Optional[Union[str, List[str]]] = None, 
        tag: Optional[Union[str, List[str]]] = None,
        sentiment: Optional[str] = None, 
        id: Optional[str] = None, 
        excludefield: Optional[Union[str, List[str]]] = None, 
        removeduplicate: Optional[bool] = None,
        excludelanguage: Optional[Union[str, List[str]]] = None, 
        organization: Optional[Union[str, List[str]]] = None, 
        url: Optional[str] = None,
        sort: Optional[str] = None, 
        symbol: Optional[str] = None, 
        country: Optional[Union[str, List[str]]] = None,
        excludecountry: Optional[Union[str, List[str]]] = None,

        max_result: Optional[int] = None,
        scroll: Optional[bool] = False,
        paginate: Optional[bool] = False,
        max_pages: Optional[int] = None,
        ) -> Dict[str, Any]:
        """
        Sending GET request to the market api
        For more information about parameters and input, Please visit our documentation page: https://newsdata.io/documentation
        """
        params = {
            'domain': domain, 
            'language': language, 
            'page': page, 
            'q': q, 
            'qInTitle': qInTitle, 
            'qInMeta': qInMeta,
            'from_date': from_date, 
            'to_date': to_date,
            'full_content': full_content, 
            'image': image, 
            'video': video,
            'timeframe': str(timeframe) if timeframe else timeframe, 
            'prioritydomain': prioritydomain, 
            'timezone': timezone, 
            'size': size,
            'domainurl': domainurl, 
            'excludedomain': excludedomain, 
            'tag': tag, 
            'sentiment': sentiment, 
            'id': id, 
            'excludefield': excludefield,
            'removeduplicate': removeduplicate, 
            'excludelanguage': excludelanguage, 
            'organization': organization,
            'url': url, 
            'sort': sort, 
            'symbol': symbol, 
            'country': country,
            'excludecountry': excludecountry,
        }
        if scroll and paginate:
            raise NewsdataException("Both 'scroll' and 'paginate' cannot be True at the same time.")
        
        URL_parameters = self.__validate_parms(user_param=params)
        if scroll:
            return self.__get_feeds_all(endpoint=self.market_url,query_params=URL_parameters,max_result=max_result)
        elif paginate:
            return self.__paginate_results(endpoint=self.market_url,query_params=URL_parameters,max_pages=max_pages)
        else:
            return self.__get_feeds(endpoint=self.market_url,query_params=URL_parameters)

    def count_api(
            self, 
            from_date: Optional[str],
            to_date: Optional[str],
            q: Optional[str] = None, 
            qInTitle: Optional[str] = None, 
            qInMeta: Optional[str] = None, 
            country: Optional[Union[str, List[str]]] = None,
            category: Optional[Union[str, List[str]]] = None, 
            language: Optional[Union[str, List[str]]] = None, 
            domain: Optional[Union[str, List[str]]] = None,
            domainurl: Optional[Union[str, List[str]]] = None,
            excludedomain: Optional[Union[str, List[str]]] = None,
            excludecountry: Optional[Union[str, List[str]]] = None,
            excludelanguage: Optional[Union[str, List[str]]] = None,
            excludecategory: Optional[Union[str, List[str]]] = None,
            full_content: Optional[bool] = None,
            image: Optional[bool] = None,
            page: Optional[str] = None,
            prioritydomain: Optional[str] = None,
            size: Optional[int] = None,
            sort: Optional[str] = None,
            video: Optional[bool] = None,
            interval: Optional[str] = None,

            raw_query: Optional[str] = None,
            paginate: Optional[bool] = False,
            max_pages: Optional[int] = None,
        ) -> Dict[str, Any]:
        """
        Sending GET request to the count API.
        """
        
        params = {
            'q': q,
            'qInTitle': qInTitle,
            'qInMeta': qInMeta,
            'country': country,
            'category': category,
            'language': language,
            'from_date': from_date,
            'to_date': to_date,
            'domain': domain,
            'domainurl': domainurl,
            'excludedomain': excludedomain,
            'excludecountry': excludecountry,
            'excludelanguage': excludelanguage,
            'excludecategory': excludecategory,
            'full_content': full_content,
            'image': image,
            'page': page,
            'prioritydomain': prioritydomain,
            'size': size,
            'sort': sort,
            'video': video,
            'interval': interval,
            'raw_query': raw_query
        }

        URL_parameters = self.__validate_parms(user_param=params)
        if paginate:
            return self.__paginate_results(
                endpoint=self.count_url,
                query_params=URL_parameters,
                max_pages=max_pages,
                is_count=True
            )
        else:
            return self.__get_feeds(endpoint=self.count_url,query_params=URL_parameters)
 
    def crypto_count_api(
            self,
            from_date: Optional[str],
            to_date: Optional[str],
            q: Optional[str] = None,
            qInTitle: Optional[str] = None,
            qInMeta: Optional[str] = None,
            language: Optional[Union[str, List[str]]] = None,
            coin: Optional[Union[str, List[str]]] = None,
            domain: Optional[Union[str, List[str]]] = None,
            domainurl: Optional[Union[str, List[str]]] = None,
            excludedomain: Optional[Union[str, List[str]]] = None,
            excludelanguage: Optional[Union[str, List[str]]] = None,
            full_content: Optional[bool] = None,
            image: Optional[bool] = None,
            page: Optional[str] = None,
            prioritydomain: Optional[str] = None,
            sentiment: Optional[str] = None,
            size: Optional[int] = None,
            sort: Optional[str] = None,
            tag: Optional[Union[str, List[str]]] = None,
            video: Optional[bool] = None,
            interval: Optional[str] = None,
            removeduplicate: Optional[bool] = None,

            raw_query: Optional[str] = None,
            paginate: Optional[bool] = False,
            max_pages: Optional[int] = None,
        ) -> Dict[str, Any]:
        """
        Sending GET request to the crypto count api
        Supports all parameters available in v2 crypto_count specification.
        """

        params = {
            'q': q,
            'qInTitle': qInTitle,
            'qInMeta': qInMeta,
            'language': language,
            'from_date': from_date,
            'to_date': to_date,
            'coin': coin,
            'domain': domain,
            'domainurl': domainurl,
            'excludedomain': excludedomain,
            'excludelanguage': excludelanguage,
            'full_content': full_content,
            'image': image,
            'page': page,
            'prioritydomain': prioritydomain,
            'sentiment': sentiment,
            'size': size,
            'sort': sort,
            'tag': tag,
            'video': video,
            'interval': interval,
            'removeduplicate': removeduplicate,
            'raw_query': raw_query,
        }

        URL_parameters = self.__validate_parms(user_param=params)
        if paginate:
            return self.__paginate_results(
                endpoint=self.crypto_count_url,
                query_params=URL_parameters,
                max_pages=max_pages,
                is_count=True
            )
        else:
            return self.__get_feeds(endpoint=self.crypto_count_url,query_params=URL_parameters)

    def market_count_api(
            self,
            from_date: Optional[str],
            to_date: Optional[str],
            q: Optional[str] = None,
            qInTitle: Optional[str] = None,
            qInMeta: Optional[str] = None,
            country: Optional[Union[str, List[str]]] = None,
            domain: Optional[Union[str, List[str]]] = None,
            domainurl: Optional[Union[str, List[str]]] = None,
            excludedomain: Optional[Union[str, List[str]]] = None,
            excludecountry: Optional[Union[str, List[str]]] = None,
            excludelanguage: Optional[Union[str, List[str]]] = None,
            full_content: Optional[bool] = None,
            image: Optional[bool] = None,
            language: Optional[Union[str, List[str]]] = None,
            organization: Optional[Union[str, List[str]]] = None,
            page: Optional[str] = None,
            prioritydomain: Optional[str] = None,
            removeduplicate: Optional[bool] = None,
            sentiment: Optional[str] = None,
            size: Optional[int] = None,
            sort: Optional[str] = None,
            tag: Optional[Union[str, List[str]]] = None,
            video: Optional[bool] = None,
            symbol: Optional[Union[str, List[str]]] = None,
            interval: Optional[str] = None,

            raw_query: Optional[str] = None,
            paginate: Optional[bool] = False,
            max_pages: Optional[int] = None,
        ) -> Dict[str, Any]:
        """
        Sending GET request to the Market Count API.
        Supports all parameters available in the market_count specification.
        """

        params = {
            'q': q,
            'qInTitle': qInTitle,
            'qInMeta': qInMeta,
            'country': country,
            'domain': domain,
            'domainurl': domainurl,
            'excludedomain': excludedomain,
            'excludecountry': excludecountry,
            'excludelanguage': excludelanguage,
            'from_date': from_date,
            'to_date': to_date,
            'full_content': full_content,
            'image': image,
            'language': language,
            'organization': organization,
            'page': page,
            'prioritydomain': prioritydomain,
            'removeduplicate': removeduplicate,
            'sentiment': sentiment,
            'size': size,
            'sort': sort,
            'tag': tag,
            'video': video,
            'symbol': symbol,
            'interval': interval,
            'raw_query': raw_query,
        }

        URL_parameters = self.__validate_parms(user_param=params)

        if paginate:
            return self.__paginate_results(
                endpoint=self.market_count_url,
                query_params=URL_parameters,
                max_pages=max_pages,
                is_count=True
            )

        return self.__get_feeds(endpoint=self.market_count_url,query_params=URL_parameters)
    
    def __del__(self):
        if isinstance(self.request_method,requests.Session):
            self.request_method.close()
            logger.info("Closed the requests Session.")
