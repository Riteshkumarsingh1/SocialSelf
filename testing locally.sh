# Install dependencies
pip install -r requirements.txt

# Initialize database (create tables)
python -c "import asyncio; from app.database import init_db; asyncio.run(init_db())"

# Run the application
python run.py