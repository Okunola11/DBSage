# WASIX
Wasix backend project. 

## Setup

1. Clone the repository
```sh
  git clone https://github.com/okunola11/wasix
```
2. Create a virtual environment.
 ```sh
    python3 -m venv .venv
 ```
3. Activate virtual environment. 
- Mac or Linux
```sh
    source .venv/bin/activate
```
- Windows
```sh
  .venv\Scripts\activate
```
4. Install project dependencies
```sh
  pip install -r requirements.txt
```
5. Create a .env file by copying the .env.sample file and add required fields
```
  cp .env.sample .env
```
6. Upgrade alembic head. Run:
```sh
  alembic upgrade head
```
7. Start server.
 ```sh
 python main.py
```
