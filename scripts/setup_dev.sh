# Install dtbase package with dev dependencies
pip install '.[dev]'

# Prepare local database environment
cp .secrets/dtenv_template.sh .secrets/dtenv_localdb.sh
sed -i '' 's/<REPLACE_ME>/your_secret_value_here/g' .secrets/dtenv_localdb.sh # Replace 'your_secret_value_here' with actual secret values
source .secrets/dtenv_localdb.sh

# Start Postgresql server in Docker container
docker run --name dt_dev -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres

# Wait for the container to initialize completely
sleep 10

# Create the database
createdb --host localhost --username postgres dt_dev

# Run tests
python -m pytest

# Start the backend API
(cd backend && DT_CONFIG_MODE=Debug ./run_localdb.sh) &


# Start the frontend
(cd webapp && npm install && FLASK_DEBUG=true DT_CONFIG_MODE=Auto-login ./run.sh) &

echo "DTBase setup complete. Backend running on http://localhost:5000, frontend on http://localhost:8000."