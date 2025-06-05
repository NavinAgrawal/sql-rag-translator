# Test PostgreSQL 17
psql --version
createdb test_connection
psql test_connection -c "SELECT version();"
dropdb test_connection

# Test MySQL 9.3
mysql --version
mysql -u root -e "SELECT VERSION();"

# Test Docker images
docker images | grep -E "(oracle|mssql)"

# Test Python packages
python -c "import sqlglot; print(f'SQLGlot: {sqlglot.__version__}')"
python -c "import sqlalchemy; print(f'SQLAlchemy: {sqlalchemy.__version__}')"