
import json

from logger import log

RESPONSE_OK = {
    'statusCode': 200,
    'headers': {'Content-Type': 'application/json'},
    'body': json.dumps({'statusCode': 200})
}
RESPONSE_ERROR = {
    'statusCode': 400,
    'body': json.dumps({'statusCode': 400})
}


def handler(event, context):  # main handler
  try:
    log.info('event: %e', event)

    return RESPONSE_OK
  except:
    return RESPONSE_ERROR


if __name__ == '__main__':
  handler(None, None)
