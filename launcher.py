from subprocess import run
from git.cmd import Git

g = Git()

while True:
    print(g.pull())
    run("python3 main.py", shell=True)
