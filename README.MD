# API parser

Small API parser using Redis

## How to install
Download the project via git clone and run the following:
```
pip install -r requirements.txt
```
## How to use

```python
from parser import send_request_to_api

URLS = [
                'https://jsonplaceholder.typicode.ru', 
                'http://188.127.251.4:8240', 
                'http://188.127.224.245:8240'
]
parser_result = []
for i in range(1, 20):
    parser_result.append(send_request_to_api(URLS, f'posts/{i}', 2000))

print(parser_result)
```
Use the following environment variables to configure the connection to the Redis server

```
REDIS_HOSTNAME = 
REDIS_PORT = 
DB = 
```
