import os
import json
import sys
import traceback

## transformer
from transformers import AutoTokenizer, AutoModel
from flask import Flask, request
from flask_cors import CORS


tokenizer = AutoTokenizer.from_pretrained("chatglm-6b", trust_remote_code=True)
model = AutoModel.from_pretrained("chatglm-6b", device_map='auto', trust_remote_code=True)

def preprocess(text):
    text = text.replace("\n", "\\n").replace("\t", "\\t")
    return text

def postprocess(text):
    return text.replace("\\n", "\n").replace("\\t", "\t")

def predict_fn(words):
    """
    Apply model to the incoming request
    """
    print('input words: ', words)

    try:
        text = preprocess(words)
        response, _ = model.chat(tokenizer, text, history=[], temperature=0.632)
        return postprocess(response)

    except Exception as ex:
        traceback.print_exc(file=sys.stdout)
        print(f"=================Exception================={ex}")

    return 'Not found answer'

# declare flask
app = Flask(__name__)
cors = CORS(app, resources={r"/summarize": {"origins": "*"}})


prompt_template_llm = """As a sophisticated expert in Manufacturing, based on the customer's question ```{question}```, please provide a concise and professional analysis based on the known information and answers provided answers by the following triple backquotes (```) and tell what information the answer is based on. If you cannot give an analysis from it, please say "insufficient information provided". It is not allowed to add hallucinations to the analysis. Please note that the analysis must be provided in English.
Known information and answers:
  ```
  {answers}
  ```
"""

def preprocess_qa(question, answers):
    trunked = "。\n".join(answers)[:5000-len(prompt_template_llm)-len(question)]
    return prompt_template_llm.format(question=question, answers=trunked)

def _get_int_from_env(env_key, default_value=0):
    string_value = os.environ.get(env_key)
    if string_value is None or len(string_value) == 0:
        return default_value

    return int(string_value)

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

def _invalid_str(string_value:str, max_len:int):
    if string_value is None or len(string_value) <=0 or len(string_value)>max_len:
        return True
    return False

def _invalid(list_value:list[str], max_len:int, max_per_item:int):
    if list_value is None or len(list_value) <=0 or len(list_value)>max_len:
        return True
    for value in list_value:
        if _invalid_str(value, max_per_item):
            return True
    return False


@app.route('/summarize', methods=['POST'])
def summarize_stream():
    """
    Do the summarization from input answers and streams out the response.
    """
    request_data = request.get_json()

    question_max_len = _get_int_from_env('question_max_len', 200)
    answers_max_len = _get_int_from_env('answers_max_len', 10)
    max_len_per_answer = _get_int_from_env('max_len_per_answer', 2000)
    default_temperature = _get_int_from_env('chat_temperature', 0.4)

    answers = request_data['answers']
    question = request_data['question']
    temperature = request_data.get('temperature')
    temperature = temperature if temperature is not None else default_temperature
    if _invalid_str(question, question_max_len):
        return _bad_request(f'Question({question}) len is not correct. Length should be [1, {question_max_len}]')

    if _invalid(answers, answers_max_len, max_len_per_answer):
        return _bad_request(f'answers({answers}) len is not correct. Length should be [1, {answers_max_len}], each answer should be[1, {max_len_per_answer}]')

    stream_input_text = preprocess_qa(question, answers)
    
    # generate streaming response
    def summarize_generate():
        history = []
        response = ""
        pre_response = None
        for idx, (response, history) in enumerate(model.stream_chat(tokenizer, stream_input_text, temperature=temperature, history=history, max_length=6000)):            
            if pre_response is not None:
                word = response[len(pre_response):]
                pre_response = response
                yield word.encode('utf-8')
            else:
                pre_response = response
                yield response.encode('utf-8')

    return app.response_class(summarize_generate())

# define a check api
@app.route('/tweet/<string:words>', methods=['GET'])
def tweet(words):
    """
    A quick check of the application status
    """
    response = predict_fn(words)
    return json.dumps(
        {
            'answer': response
        }
    )