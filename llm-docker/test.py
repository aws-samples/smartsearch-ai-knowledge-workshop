# import requests module
import requests
import sys

## https://www.geeksforgeeks.org/response-iter_content-python-requests/
## https://stackoverflow.com/questions/57497833/python-requests-stream-data-from-api
def get_stream(url):
    s = requests.Session()

    with s.get(url, headers=None, stream=True) as response:
        for word in response.iter_content(decode_unicode=True):
            if word:
                print(word, end="")
    
    print()

if __name__ == '__main__':
    args = sys.argv[1:]

    words = 'Hello!'
    if len(args) >=1:
        words = args[0]
    
    get_stream(f'http://localhost:5000/tweet_stream/{words}')
# Making a get request