import copy
import os
import datetime
import boto3
from logger import log


class db:
  _db = None
  _table = None
  _timestamp = False
  _cache = {}
  _cache_enabled = False

  class TYPE:
    STRING: 'S'
    NUMBER: 'N'
    BINARY: 'B'

  @staticmethod
  def init(table, schema={}, keys=None, timestamp=False, cache=False):
    if db._db is None:
      YDB_ENDPOINT = os.environ.get('YDB_ENDPOINT')
      YDB_ACCESS_KEY_ID = os.environ.get('YDB_ACCESS_KEY_ID')
      YDB_ACCESS_KEY_SECRET = os.environ.get('YDB_ACCESS_KEY_SECRET')

      db._db = boto3.resource(
          'dynamodb',
          endpoint_url=YDB_ENDPOINT,
          region_name='ru',
          aws_access_key_id=YDB_ACCESS_KEY_ID,
          aws_secret_access_key=YDB_ACCESS_KEY_SECRET
      )
      db._cache_enabled = cache
      if db._cache_enabled:
        db._cache = {}

    if db._table is not None:
      return

    table_names = [t.name for t in db._db.tables.all()]

    if table not in table_names:
      keys_seed = [
          {
              'AttributeName': 'id',
              'KeyType': 'HASH'
          }
      ]

      schema_seed = [
          {'AttributeName': 'id', 'AttributeType': 'S'}
      ]

      if keys is not None:
        for k in keys:
          keys_seed.append({
              {
                  'AttributeName': k,
                  'AttributeType': 'S'
              }
          })
      for sk in schema.keys():
        schema_seed.append({
            {
                'AttributeName': sk,
                'AttributeType': schema[sk]
            }
        })
      if timestamp:
        schema_seed.append(
            {'AttributeName': 'updated', 'AttributeType': 'S'}
        )
      db._table = db._db.create_table(
          TableName=table,
          KeySchema=keys_seed,
          AttributeDefinitions=schema_seed
      )
    else:
      db._table = db._db.Table(table)

  @staticmethod
  def insert(id: str, data):
    data['id'] = id
    if db._timestamp:
      data['updated'] = datetime.datetime.now().isoformat()

    db._table.put_item(
        Item=data
    )
    if db._cache_enabled:
      db._cache[id] = copy.deepcopy(data)

    return data

  @staticmethod
  def select(id: str = None, where: dict = None):
    seed = {}
    if id is not None:
      seed['id'] = id
    if where is not None:
      for k in where.keys():
        seed[k] = where[k]

    if db._cache_enabled and id is not None and id in db._cache:
      return copy.deepcopy(db._cache[id])

    data = None

    try:
      response = db._table.get_item(Key=seed)
      data = response['Item']
      if db._cache_enabled and id is not None:
        db._cache[id] = copy.deepcopy(data)
    except Exception as err:
      log.error('db error: {}'.format(err))
      data = None

    return data
