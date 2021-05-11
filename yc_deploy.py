
import os
import sys
import subprocess
import zipfile
import json
import re
import io
import base64
import time
import requests

IGNORED_FILES = [
    '.deploy.zip',
    '.env',
    '.env.example',
    '.editorconfig',
    '.directory',
    '.gitignore',
    'makefile',
    'README.md',
    'yc_deploy.py',
]

IGNORED_FOLDERS = [
    './.git',
    './.vscode',
    './.idea',
    './__pycache__',
]


class yc:
  config = {}
  iam_token = None
  folder_id = None
  function_id = None

  @staticmethod
  def token():
    if yc.iam_token is not None:
      return yc.iam_token

    t = subprocess.check_output(['yc', 'iam', 'create-token'])

    yc.iam_token = t.decode('utf-8').strip()
    return yc.iam_token

  @staticmethod
  def folder():
    if yc.folder_id is not None:
      return yc.folder_id

    f_id = subprocess.check_output(['yc', 'config', 'get', 'folder-id'])

    yc.folder_id = f_id.decode('utf-8').strip()
    return yc.folder_id

  @staticmethod
  def function(check=False):
    if yc.function_id is not None:
      return yc.function_id

    response = requests.get('https://serverless-functions.api.cloud.yandex.net/functions/v1/functions', params={
        'folderId': yc.folder(),
        'filter': 'name="{}"'.format(yc.config['YCF_NAME'])
    }, headers={
        'Authorization': 'Bearer {}'.format(yc.token())
    })

    seed = json.loads(response.text)
    description = ''
    if 'YCF_DESCRIPTION' in yc.config:
      description = yc.config['YCF_DESCRIPTION']

    if not check and 'functions' not in seed or len(seed['functions']) < 1:
      response = requests.post('https://serverless-functions.api.cloud.yandex.net/functions/v1/functions', json={
          'folderId': yc.folder(),
          'name': yc.config['YCF_NAME'],
          'description': description,
      }, headers={
          'Authorization': 'Bearer {}'.format(yc.token())
      })
      retry = 0
      while yc.function_id == None and retry < 5:
        time.sleep(1)
        yc.function()
        retry += 1
      if retry == 5:
        print('error function create timeout')
        sys.exit(1)
    else:
      if 'functions' in seed and len(seed['functions']) > 0:
        yc.function_id = seed['functions'][0]['id']

    return yc.function_id

  @staticmethod
  def env():
    try:
      from dotenv import dotenv_values
    except ImportError:
      subprocess.check_call(
          [sys.executable, '-m', 'pip', 'install', 'python-dotenv'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
      from dotenv import dotenv_values

    yc.config = dotenv_values('./.env')

  @staticmethod
  def zip():
    if os.path.exists('./.deploy.zip'):
      os.remove('./.deploy.zip')

    path = './'
    with zipfile.ZipFile('./.deploy.zip', "w", zipfile.ZIP_DEFLATED) as f:
      for root, dirs, files in os.walk(path):
        if any([root.startswith(iF) for iF in IGNORED_FOLDERS]):
          continue
        for file in files:
          if file in IGNORED_FILES or re.search(r'^\..+?\.json', file):
            continue
          f.write(os.path.join(root, file),
                  os.path.relpath(os.path.join(root, file), path))
    return

  @staticmethod
  def zip_memory():
    path = './'

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as f:
      for root, dirs, files in os.walk(path):
        if any([root.startswith(iF) for iF in IGNORED_FOLDERS]):
          continue
        for file in files:
          if file in IGNORED_FILES or re.search(r'^\..+?\.json', file):
            continue
          with open(os.path.join(root, file), 'rb') as fb:
            f.writestr(os.path.relpath(
                os.path.join(root, file), path), fb.read())
    return zip_buffer.getvalue()

  @staticmethod
  def publish_cli():
    hook = 'TG_WEBHOOK' in yc.config and yc.config['TG_WEBHOOK']

    seed = 'deny'
    if hook == 'true' or hook == '1':
      invoke_url = json.loads(subprocess.check_output(
          ['yc', 'serverless', 'get', yc.config['YCF_NAME'], '--format=json']))['http_invoke_url']
      from tg import tg
      tg.webhook(invoke_url)

    yc_deploy_runtime = ['yc', 'serverless', 'function']
    yc_deploy_runtime.append('{}-unauthenticated-invoke'.format(
        seed
    ))
    yc_deploy_runtime.append(yc.config['YCF_NAME'])

    subprocess.run(yc_deploy_runtime)

  @staticmethod
  def publish_rest():
    hook = 'TG_WEBHOOK' in yc.config and yc.config['TG_WEBHOOK']

    seed = 'allAuthenticatedUsers'
    if hook == 'true' or hook == '1':
      seed = 'allUsers'
      invoke_url = json.loads(requests.get(
          'https://serverless-functions.api.cloud.yandex.net/functions/v1/functions/{}'.format(
              yc.function()), headers={
              'Authorization': 'Bearer {}'.format(yc.token())
          }
      ).text)['httpInvokeUrl']
      os.environ['TG_BOT_TOKEN'] = yc.config['TG_BOT_TOKEN']
      from tg import tg
      tg.webhook(invoke_url)

    function_id = yc.function()
    url = 'https://serverless-functions.api.cloud.yandex.net/functions/v1/functions/{}:setAccessBindings'.format(
        function_id
    )
    requests.post(url, json={
        'accessBindings': [
            {
                'roleId': 'serverless.functions.invoker',
                'subject': {
                    'id': seed,
                    'type': 'system'
                }
            }
        ]
    },
        headers={
        'Authorization': 'Bearer {}'.format(yc.token())
    })

  @staticmethod
  def deploy_rest():
    content = yc.zip_memory()

    memory_seed = yc.config['YCF_MEMORY'].lower()
    memory = int(re.sub(r'[^\d]', '', memory_seed))
    if 'kb' in memory_seed:
      memory = memory * 1024 * 1024 * 1024
    if 'mb' in memory_seed:
      memory = memory * 1024 * 1024
    if 'gb' in memory_seed:
      memory = memory * 1024 * 1024 * 1024

    environment = {}
    for k in yc.config.keys():
      if k.startswith('YCF_'):
        continue
      if yc.config[k].strip() == '':
        continue

      value = yc.config[k]

      if value.endswith('.json'):
        with open(value, 'r', encoding='utf-8') as f:
          value = json.dumps(json.loads(f.read()))

      environment[k] = value

    requests.post(
        'https://serverless-functions.api.cloud.yandex.net/functions/v1/versions',
        json={
            'functionId': yc.function(),
            'runtime': yc.config['YCF_RUNTIME'],
            'entrypoint': yc.config['YCF_ENTRYPOINT'],
            'resources': {
                'memory': memory
            },
            'content': base64.b64encode(content).decode('ascii'),
            'executionTimeout': yc.config['YCF_TIMEOUT'],
            'environment': environment,
        },
        headers={
            'Authorization': 'Bearer {}'.format(yc.token())
        }
    )

    description = ''
    if 'YCF_DESCRIPTION' in yc.config:
      description = yc.config['YCF_DESCRIPTION']
    if description != '':
      requests.patch(
          'https://serverless-functions.api.cloud.yandex.net/functions/v1/functions/{}'.format(
              yc.function()),
          json={
              'description': description,
          },
          headers={
              'Authorization': 'Bearer {}'.format(yc.token())
          }
      )

    print('deploy done...')

  @staticmethod
  def deploy_cli():
    yc_deploy_runtime = [
        'yc', 'serverless', 'function', 'version', 'create',
        '--function-name={}'.format(yc.config['YCF_NAME']),
        '--runtime={}'.format(yc.config['YCF_RUNTIME']),
        '--entrypoint={}'.format(yc.config['YCF_ENTRYPOINT']),
        '--memory={}'.format(yc.config['YCF_MEMORY']),
        '--execution-timeout={}'.format(yc.config['YCF_TIMEOUT']),
    ]

    for k in yc.config.keys():
      if k.startswith('YCF_'):
        continue
      if yc.config[k].strip() == '':
        continue

      seed = '--environment="{}={}"'.format(k, yc.config[k])

      if yc.config[k].endswith('.json'):
        f = open(yc.config[k], 'r')
        value = '{}'.format(
            json.dumps(json.loads(f.read()))
            # .replace('=', '%3d')
        )
        f.close()
        seed = '--environment="{}={}"'.format(
            k,
            value
        )

      yc_deploy_runtime.append(seed)

    yc.zip()

    yc_deploy_runtime.append('--source-path=./.deploy.zip')
    yc_deploy_runtime.append('--format=json')

    subprocess.run(yc_deploy_runtime)

    if os.path.exists('./.deploy.zip'):
      os.remove('./.deploy.zip')


if __name__ == '__main__':
  yc.env()

  if len(sys.argv) > 1 and sys.argv[1].strip() == 'by-rest':
    yc.deploy_rest()
    yc.publish_rest()
  else:
    yc.deploy_cli()
    yc.publish_cli()
