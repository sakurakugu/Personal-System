cd backend
$env:DATABASE_URL="postgresql+asyncpg://bloguser:change_me_in_production@localhost:15432/blogdb"      
python -m alembic upgrade head