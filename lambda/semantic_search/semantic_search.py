import os
import sys
import time
import logging
import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection

_OS_CLIENT = None
_EMBEDDING_CLIENT = None
_SESSION = None


def _get_session():
    global _SESSION
    if _SESSION is None:
        _SESSION = boto3.Session()
    return _SESSION


def _get_int_from_env(env_key, default_value=0):
    string_value = os.environ.get(env_key)
    if string_value is None or len(string_value) == 0:
        return default_value

    return int(string_value)


def _get_string_from_env(env_key, default_value=""):
    string_value = os.environ.get(env_key)
    if string_value is None or len(string_value) == 0:
        return default_value

    return string_value


def _setup_logging(cur_logger) -> None:
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    handler = logging.StreamHandler(sys.stdout)
    cur_logger.propagate = False
    cur_logger.setLevel(logging.DEBUG)
    cur_logger.addHandler(handler)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
_setup_logging(logger)


class OpenSearchClient(object):
    """
    Wrapped a thin client for opensearch to get knn search results
    """

    def __init__(self,
                 request_timeout=30,
                 index_name='qa_knowledge_index',
                 boto3_session: boto3.Session = None):
        """
        Args:
            :param request_timeout: search timeout
            :param index_name: index name
            :param boto3_session: A Boto3 Session.
        """
        self._index = index_name
        self._request_timeout = request_timeout

        self._client = self._create_opensearch_client(boto3_session=boto3_session)

    def _create_opensearch_client(self,
                                  boto3_session=None):

        sm_client = boto3_session.client(service_name="secretsmanager")
        host = _get_string_from_env('host', '')
        master_user = sm_client.get_secret_value(SecretId='VectorDBMasterUserSecret')['SecretString']

        user_data = json.loads(master_user)
        username = user_data.get('username')
        password = user_data.get('password')

        auth = (username, password)  # For testing only. Don't store credentials in code.
        return OpenSearch(hosts=[{'host': host, 'port': 443}],
                          http_auth=auth,
                          use_ssl=True,
                          verify_certs=True,
                          connection_class=RequestsHttpConnection,
                          ssl_assert_hostname=False,
                          ssl_show_warn=False)

    @staticmethod
    def _get_query(manufacturing_process_number, vector=[], size_output=10, knn_k=6):
        query = {
            "size": size_output,
            "from": 0,
            "_source": {
                "excludes": ["question_vector", "answers_vector"]
            },
            "query": {
                "bool": {
                    "filter": {
                        "bool": {
                            "must": [
                                {
                                    "match": {
                                        "manufacturing_process_number": manufacturing_process_number
                                    }
                                }
                            ]
                        }
                    },
                    "must": [
                        {
                            "knn": {
                                "question_vector": {
                                    "vector": vector,
                                    "k": min(knn_k, 256),
                                }
                            }
                        }
                    ]
                }
            }
        }
        # print(query)
        return query

    def knn_search_by_text_vectors(self,
                                   manufacturing_process_number,
                                   text_vector,
                                   knn_k=6,
                                   size_output=10):
        """
        Search by vectors

        Args:
            :text_vector: text vector. must not null or empty
            :size_output: max output size
            :knn_k: param k of knn
            :min_confidence: The minimum confidence level for the labels to return
        """
        if text_vector is None or len(text_vector) == 0:
            raise ValueError('Text vectors cannot be null or empty')

        query = OpenSearchClient._get_query(manufacturing_process_number=manufacturing_process_number,
                                            vector=text_vector,
                                            size_output=size_output,
                                            knn_k=knn_k)
        try:
            logger.debug(
                f"Querying answers from index {self._index} by {manufacturing_process_number} and vector with length {len(text_vector)}")

            response = self._client.search(request_timeout=self._request_timeout,
                                           index=self._index,
                                           body=query)

            logger.debug(f"Queried answers from open search index {self._index} by {query}: {response}")
            return self._resolve_result(response)
        except Exception as e:
            logger.exception(
                f"Couldn't query image materials from open search index {self._index} by {query}")

            raise e

    @staticmethod
    def _resolve_result(response):
        """
        # return all fields and matched score excluding vectors
        """
        if response is None or response.get('hits') is None or response['hits'].get('hits') is None:
            return []

        raw_list = response['hits']['hits']
        results = []
        for item in raw_list:
            doc = {'id': item['_id'], 'score': item['_score']}
            if item.get('_source') is not None:
                source = item['_source']
                doc['source'] = source
            results.append(doc)

        return results


class SageMakerClient(object):
    """
    Encapsulates an Amazon SageMaker Client. This class is a thin wrapper
    around parts of the Boto3 Amazon Session API.
    """

    def __init__(self, endpoint_name: str = "", boto3_session: boto3.Session = None):
        """
        Args:
            :endpoint_name: A sagemaker endpoint name.
            :boto3_session: A Boto3 session.
        """
        self._endpoint_name = endpoint_name
        self._client = boto3_session.client(service_name="sagemaker-runtime")

    def _invoke(self, json_body):
        try:
            response = self._client.invoke_endpoint(EndpointName=self._endpoint_name,
                                                    ContentType='application/json',
                                                    Body=json_body,
                                                    Accept='application/json')
            return response
        except Exception as e:
            logger.exception(
                f"Invoke sagemaker endpoint {self._endpoint_name} by {json_body} has exception: {json_body}, by endpoint {self._endpoint_name}")

            raise e

    def generate_vectors(self, keywords: list[str]):
        """
        Send request to sagemaker endpoint to generate labels

        Args:
            :keywords: keywords list to generate embeddings
        """
        json_input = json.dumps({'inputs': keywords, "options": {"wait_for_model": True}})
        logger.debug(f"Generate embedding from sagemaker {self._endpoint_name} by {json_input}")

        response = self._invoke(json_body=json_input)
        try:
            vectors = json.loads(response['Body'].read())
            if not isinstance(vectors, list) or len(vectors) == 0:
                logger.warning(
                    f"Generate embedding from sagemaker {self._endpoint_name} by {json_input} has unsuccessful result: {vectors}")
                return []

            if len(vectors) != len(keywords):
                logger.warning(
                    f"Generate embedding from sagemaker {self._endpoint_name} by {json_input} has umatched output witu input, vectors len {len(vectors)} != keywords len {len(keywords)}")
                return []

            results = [vector[0][0] for vector in vectors]
            logger.debug(f"Generated embedding from  sagemaker {self._endpoint_name} by {json_input}: {results}")
            return results
        except Exception as e:
            logger.exception(
                f"Generate embedding from sagemaker {self._endpoint_name} by {json_input} has exception: {json_input}")
            raise e


def _get_opensearch_client():
    global _OS_CLIENT
    if _OS_CLIENT is None:
        _OS_CLIENT = OpenSearchClient(request_timeout=20,
                                      index_name=_get_string_from_env('index', 'qa_knowledge_index'),
                                      boto3_session=_get_session())
    return _OS_CLIENT


def _get_embedding_client():
    global _EMBEDDING_CLIENT
    if _EMBEDDING_CLIENT is None:
        _EMBEDDING_CLIENT = SageMakerClient(
            endpoint_name=_get_string_from_env('embedding_endpoint_name'), boto3_session=_get_session())
    return _EMBEDDING_CLIENT


def _not_support(error_code, message):
    return _error_response(405, error_code, message)


def _bad_request(message):
    return _error_response(400, 'ParamsError', message)


def _error_response(status_code, error_code, message):
    return _json_response(status_code, {'code': error_code, 'message': message})


def _success_response(results):
    return _json_response(200, results)


def _json_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {"content-type": "application/json", "Access-Control-Allow-Origin": '*'},
        'body': json.dumps(body),
        "isBase64Encoded": False
    }


class Stopwatch(object):
    def start(self):
        self._start = time.time()
        return self

    def stop(self):
        if self._start is None:
            raise RuntimeError('Should start first')
        return time.time() - self._start


def _lowercase(dict_obj):
    mapping = dict_obj or {}
    return {k.lower(): v for k, v in mapping.items()}


def _check_len(max_len, str_value, str_name):
    if str_value is None or len(str_value) == 0 or len(str_value) > max_len:
        return _bad_request(
            message=f'{str_name} length should be in the range of (0, {max_len}], current len is {0 if str_value is None else len(str_value)}')
    return None


def _param_check(event):
    resource_path = event.get('requestContext', {}).get('resourcePath')
    headers = _lowercase(event.get('headers'))
    content_type = headers.get('content-type', '')

    ## check headers and http method, path
    if content_type != 'application/json':
        return _not_support(error_code="UnsupportedMediaType",
                            message=f'Unsupported request with content type: {content_type}'), None, None

    if event.get('httpMethod') is None or event.get('httpMethod').upper() != 'POST':
        return _not_support(error_code="MethodNotAllowed",
                            message=f"Unsupported request with method: {event['httpMethod']}"), None, None

    if resource_path is None or resource_path != f'/smart_search':
        return _not_support(error_code="PathNotAllowed",
                            message=f'Unsupported request with path: {resource_path}, this lambda allows /smart_search'), None, None

    if 'body' not in event:
        return _bad_request(message=f'Message body is empty'), None, None

    ## check input body
    json_body = json.loads(event["body"])
    search_words = json_body.get('search_words')
    manufacturing_process_number = json_body.get('manufacturing_process_number')

    search_words_max_len = _get_int_from_env('search_words_max_size', 100)
    manufacturing_process_number_max_len = _get_int_from_env('manufacturing_process_number_max_size', 30)

    ## check search_words
    checked_search_words = _check_len(search_words_max_len, search_words, 'search_words')
    if checked_search_words:
        return checked_search_words, None, None

    ## check manufacturing_process_number
    checked_process_number = _check_len(manufacturing_process_number_max_len, manufacturing_process_number,
                                        'manufacturing_process_number')
    if checked_process_number:
        return checked_process_number, None, None

    return None, search_words, manufacturing_process_number


def _generate_embedding(search_words):
    embedding_client = _get_embedding_client()
    return embedding_client.generate_vectors([search_words])


def _synthetic_search(manufacturing_process_number, search_vector):
    opensearch_client = _get_opensearch_client()
    return opensearch_client.knn_search_by_text_vectors(manufacturing_process_number, search_vector)


def _search_response(searched_results):
    return _success_response(searched_results)


# Lambda execution starts here
def lambda_handler(event, context):
    errors, search_words, manufacturing_process_number = _param_check(event)
    if errors:
        return errors

    stopwatch = Stopwatch().start()
    logger.debug(f"Start to search by {search_words}")
    search_vector = _generate_embedding(search_words)
    searched_results = _synthetic_search(manufacturing_process_number, search_vector[0])
    lapsed = stopwatch.stop()
    logger.info(f"searched lapsed time {lapsed} by {search_words}, searched result: {searched_results}")

    return _search_response(searched_results)