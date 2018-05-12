import random
from fabric.api import cd, env, local, run
from fabric.contrib.files import exists, append


env.USER = 'ubuntu'
env.key_filename = ['/Users/pita/Desktop/buybackmoa-ec2.pem']
env.hosts = ['ubuntu@ec2-13-209-69-177.ap-northeast-2.compute.amazonaws.com']

REPO_URL = 'https://github.com/pitachips/BuyBackMoa.git'


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
    append('.env', 'PROJECT_ENV=prod')
    append('.env', 'SITENAME=buybackmoa')
    current_contents = run('cat .env')
    if 'SECRET_KEY' not in current_contents:
        new_secret = ''.join(random.SystemRandom().choices(r'!@#$%^&*()ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=50))
        append('.env', 'SECRET_KEY={}'.format(new_secret))


def _update_static_files():
    run('./venv/bin/python manage.py collectstatic')


def _update_database():
    run('./venv/bin/python manage.py migrate')


def deploy():
    site_folder = '/home/{}/buybackmoa'.format(env.USER)
    run('mkdir -p {}'.format(site_folder))
    with cd(site_folder):
        _get_latest_source()
        _update_virtualenv()
        _create_or_update_dotenv()
        _update_static_files()


## https://www.obeythetestinggoat.com/book/chapter_automate_deployment_with_fabric.html 참고
