from fabric.api import cd, env, local, run
from fabric.contrib.files import exists
import os
import json


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_URL = 'https://github.com/pitachips/BuyBackMoa.git'

with open(os.path.join(PROJECT_DIR, "deploy.json")) as f:
    ENVS = json.loads(f.read())

env.USER = ENVS['user']
env.key_filename = ENVS['key_filename']
env.hosts = ENVS['hosts']


def _get_latest_source():
    if exists('.git'):
        run('git fetch')   # git pull이 아니라 git fetch 임
    else:
        run('git clone {} .'.format(REPO_URL))
    current_commit = local('git log -n 1 --format=%H', capture=True)
    run('git reset --hard {}'.format(current_commit))


def _update_virtualenv():
    if not exists('venv/bin/activate'):
        run('python3 -m venv ~/buybackmoa/venv')
    run('./venv/bin/pip install -r requirements.txt')


def _update_static_files():
    run('./venv/bin/python manage.py collectstatic --noinput')


def _update_database():
    run('./venv/bin/python manage.py migrate')


def _restart_server():
    run('source venv/bin/activate')
    run('sudo systemctl daemon-reload')
    run('sudo systemctl restart gunicorn')
    run('sudo nginx -t')
    run('sudo service nginx restart')
    run('sudo systemctl status gunicorn')


def deploy():
    site_folder = '/home/{}/buybackmoa'.format(env.USER)
    run('mkdir -p {}'.format(site_folder))
    with cd(site_folder):
        _get_latest_source()
        _update_virtualenv()
        _update_static_files()
        # idempotency 획득을 위해, 
        # guniorn.service 파일 생성 및 symlink 생성
        # sites-available에 nginx.conf 파일 생성 및 sites-enabled에 symlink 생성
        # gunicorn --bind 명령
        _restart_server()


## https://www.obeythetestinggoat.com/book/chapter_automate_deployment_with_fabric.html 참고
