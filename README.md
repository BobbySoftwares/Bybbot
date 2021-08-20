# The Bybbot

### Power to the masses

The Bybbot is an discord bot in python written by, for and with a subset of disturbed minds from an arcane french discord server to do stuff and things, among:

- Disruptive inflationist eco-friendly vegan cryptocurrencies for everyone, based on a scientific approach to optimize for big fat all-luck-no-skill-based economy. You too, become a millionaire without having a clue how and spit on the plebeans which also happens to be millionaires but slightly less than you! Embark on a journey of social experiments without anybody to keep the ship afloat !

- Obscure french memetic sound references, also known as what mortals call a *soundboard*. Enjoy thousands of french lines taken from films, shows and games you've never heard of before unless you're french! Embrace frenchhood at is most extreme manifestation!

- Uh, hum, stuff! Like, uh, things!

- Be like us, be *habile*, be french! *Du bois, merci ! Encore un coup de ton ISP ! CUILLÈRE !*

Oh, and cheers from the *Bobbycratie* ! *Baguette !*

## How to build from sources

*Laughing in Python*

## How to *install* from sources

### Requirements

- Latest version of [Python 3](https://www.python.org/downloads/). If you're on linux, you should already have it, on macOS you may install it through your means of choice (`brew`'s my personal fav'), on Windows you should have plenty of options too, pick any.
- Latest version of `pip`.
- Latest version of [Poetry](https://python-poetry.org/).
- A discord bot token: <https://discord.com/developers/applications>.

### Getting real

Clone the repo:
```
git clone https://github.com/BobbySoftwares/Bybbot.git
```
Install requirements:
```
poetry install
```
Create a `config.json` file with the following content, replacing `"PUT YOUR TOKEN HERE"` with your actual bot token and `0`, `1` and `2` (and how many more bot admins you want) with the actuals discord ids of your crew:
```json
{
    "token": "PUT YOUR TOKEN HERE",
    "admins": [
       0,
       1,
       2
    ]
}
```
Launch the bot:
```
poetry run python main.py
```
Done.

Alternatively, you may want to run the bot through `launcher.py`:
```
poetry run python launcher.py
```
In this config, the bot will auto-reboot on shutdown, and will self-update when it reboots. Admins defined in `config.json` may trigger a reboot with the command `!sudo reboot`.

## How to use

*Coming soon!*

## How to contribute

*Coming soon!*
