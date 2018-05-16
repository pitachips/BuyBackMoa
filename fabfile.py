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


def _initial_setup():
    run('sudo apt-get -y upgrade')
    run('sudo apt-get -y update')
    run('sudo apt-get -y install python3-pip python3-dev python3-venv nginx memcached git')
    run('sudo apt-get update')
    run('pip3 --version')
    run('pip3 install --upgrade pip setuptools')
    run('pip --version')


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


def _configure_gunicorn():
    run('source venv/bin/activate')
    # run('./venv/bin/gunicorn --bind 0.0.0.0:8000 buybackmoa.wsgi:application')
    if exists('/etc/systemd/system/gunicorn.service'):
        run('sudo rm -f /etc/systemd/system/gunicorn.service')
    run('sudo ln -s ~/buybackmoa/buybackmoa/gunicorn.service /etc/systemd/system/')
    run('sudo systemctl daemon-reload')
    run('sudo systemctl start gunicorn')


def _configure_nginx():
    if exists('/etc/nginx/sites-enabled/default'):
        run('sudo rm /etc/nginx/sites-enabled/default')
    if exists('/etc/nginx/sites-enabled/buybackmoa'):
        run('sudo rm -f /etc/nginx/sites-enabled/buybackmoa')
    run('sudo ln -s ~/buybackmoa/buybackmoa/nginxconf_buybackmoa /etc/nginx/sites-enabled/buybackmoa')


def _restart_server():
    run('source venv/bin/activate')
    run('sudo systemctl restart gunicorn')
    run('sudo nginx -t')
    run('sudo service nginx restart')
    # run('sudo systemctl status gunicorn')


def deploy():
    site_folder = '/home/{}/buybackmoa'.format(env.USER)
    run('mkdir -p {}'.format(site_folder))
    with cd(site_folder):
        _initial_setup()
        _get_latest_source()
        _update_virtualenv()
        _update_static_files()
        _configure_gunicorn()
        _configure_nginx()
        _restart_server()


## https://www.obeythetestinggoat.com/book/chapter_automate_deployment_with_fabric.html 참고
