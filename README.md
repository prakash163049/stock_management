# Stock Management System

A web-based stock management system built with Flask and MongoDB.

## Features

- User Authentication
- Product Management
- Stock Tracking
- Basic Reporting
- Responsive Design

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Unix/MacOS:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with the following content:
```
MONGODB_URI=mongodb://localhost:27017/stock_management
SECRET_KEY=your_secret_key_here
```

5. Run the application:
```bash
python app.py
```

## Project Structure

```
stock_management/
├── app.py
├── config.py
├── requirements.txt
├── .env
├── static/
│   ├── css/
│   └── js/
└── templates/
    ├── base.html
    ├── auth/
    └── products/
``` #   s t o c k _ m a n a g e m e n t  
 