# Welcome to CookieCoin
## 0. Introduction
CookieCoin is a cryptocurrency I made because I was bored. Yes, that is correct. This random broke middle-schooler made a fucking cryptocurrency to procrastinate on their history essay. But you're not here because you want to know what assignment I'm procrastinating on to write this, are you? You want to run a CookieCoin node, right? Good, because this is exactly what I'm actually writing about.
## 1. Setting up
I'm writing this for Python. Why? Because I'm not masochistic enough to deal with WebSockets in C++. So... you need [Python](https://www.python.org/downloads/) version 3.11 or later installed, remember to tick the 'add python.exe to path' box. You'll also need [Git](https://git-scm.com/install/) version 2.53.0 or later, to clone this repository. Both would actually probably work with earlier versions, but these are the ones I'm running so I know it works with these. If you get an error, first check your version numbers, blah, blah, blah.
### 1.1. Cloning the repository
So navigate to wherever you want to put your node, (`cd path/to/your/folder`), and run the command 
```
git clone https://github.com/Cheezstik-Studios/CookieCoin-backend
```
That's... it.
### 1.2. Installing dependencies
Ok, I use a few libraries for this, and you'll need them. I don't think I need much more explaining for that, so just open your command prompt and type in these commands:
```
python -m venv .venv
.venv\Scripts\activate
pip install flask flask-sock websocket-client
```
So far that's all you need, but I'll be updating this when I change it so check back at this first section whenever you update your node.

## 2. Actually setting up the node