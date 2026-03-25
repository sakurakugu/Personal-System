cd backend
$env:DATABASE_URL="postgresql+asyncpg://bloguser:change_me_in_production@localhost:15432/blogdb"      
python -m alembic upgrade head

versions/ 中使用 001_描述.py 的命名方式