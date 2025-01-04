# DBSage

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

DBSage is an AI-powered SQL assistant that enables users to query databases using natural language. It eliminates the need to write SQL queries manually by translating plain English prompts into executable SQL statements.

## 🚀 Features

- Natural language to SQL query conversion
- Support for multiple SQL database types
- Secure database connection management
- CSV export functionality
- RESTful API built with FastAPI
- Interactive query generation

## 🎯 Use Cases

- Data analysts who want to quickly explore databases
- Business users who need data but don't know SQL
- Developers prototyping applications
- Anyone who wants to interact with databases using natural language

## 🔧 Prerequisites

- Python 3.12 or higher
- poetry (Python dependencies manager)
- Access to a SQL database

## ⚡ Quick Start

1. Clone the repository:

```sh
git clone https://github.com/okunola11/dbsage
cd db_sage
```

2. Install dependencies in a virtual environment:

```sh
# Install dependencies
# Poetry creates the virtual environment
poetry install
```

3. Set up environment variables:

```sh
cp .env.sample .env
```

Edit the `.env` file with your configuration settings.

4. Initialize the database:

```sh
alembic upgrade head
```

5. Start the server:

```sh
poetry run start
```

## 🔍 How to Use

1. Connect to your database using the provided API endpoints
2. Input your openai api key
3. Format your query prompts with table names for context:

```plaintext
Table name: orders
Good prompt: "Show me all order where the total is greater than $1000"
Bad prompt: "Show me all orders where the total is greater than $1000"
```

4. Submit your natural language query
5. Receive the SQL query and results
6. Optionally download results as CSV

## 📚 API Documentation

Once the server is running, access the API documentation at:

- Swagger UI: `http://localhost:8000/docs`

## 🔐 Security Considerations

- User database credentials are not stored
- Only read operations are allowed to avoid unwanted writes
- Inactive database connections are cleared up
- All database connections are encrypted
- Input validation is performed on all queries
- Rate limiting is implemented to prevent abuse

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions, please open an issue in the GitHub repository.

## ⚠️ Important Notes

- Always include table names in your prompts for accurate query generation
- Review generated SQL queries before execution in production environments
