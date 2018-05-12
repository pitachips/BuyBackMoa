import random
from fabric.api import cd, env, local, run
from fabric.contrib.files import exists, append
import os
import json


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_URL = 'https://github.com/pitachips/BuyBackMoa.git'

with open(os.path.join(PROJECT_DIR, "secret.json")) as f:
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


def _create_or_update_dotenv():
    # ENVS['PROJECT_ENV'] = "prod"
    if 'SECRET_KEY' not in ENVS:
        new_secret = ''.join(random.SystemRandom().choices(r'!@#$%^&*()ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=50))
        ENVS['SECRET_KEY'] = new_secret


def _update_static_files():
    run('./venv/bin/python manage.py collectstatic')


def _update_database():
    run('./venv/bin/python manage.py migrate')


def deploy():
    site_folder = '/home/{}/buybackmoa'.format(env.USER)
    run('mkdir -p {}'.format(site_folder))
    with cd(site_folder):
        run('whoami')
        _get_latest_source()
        _update_virtualenv()
        _create_or_update_dotenv()
        _update_static_files()


## https://www.obeythetestinggoat.com/book/chapter_automate_deployment_with_fabric.html 참고
