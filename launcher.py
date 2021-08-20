from subprocess import run
from git.cmd import Git

g = Git()

while True:
    print(g.pull())
    run("poetry install", shell=True)
    run("poetry run python main.py", shell=True)
