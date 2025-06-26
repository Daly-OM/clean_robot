
 1829  alembic revision --autogenerate -m "Initial API schema"  // to generate the data base tables
 1832  alembic upgrade head // save the actual DB state
 1833  alembic current // current SHa1 of the DB
