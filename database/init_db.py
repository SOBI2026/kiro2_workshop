#!/usr/bin/env python3
"""
Initialize RDS PostgreSQL database with schema
"""
import sys
import os
import boto3
import json
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def get_rds_credentials(secret_arn):
    """Get RDS credentials from Secrets Manager"""
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_arn)
    return json.loads(response['SecretString'])

def get_rds_endpoint(db_instance_id):
    """Get RDS endpoint from instance ID"""
    client = boto3.client('rds')
    response = client.describe_db_instances(DBInstanceIdentifier=db_instance_id)
    return response['DBInstances'][0]['Endpoint']['Address']

def create_database(host, port, username, password, dbname):
    """Create database if it doesn't exist"""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database='postgres',
            user=username,
            password=password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{dbname}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE {dbname}')
            print(f"Database '{dbname}' created successfully")
        else:
            print(f"Database '{dbname}' already exists")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {str(e)}")
        raise

def execute_schema(host, port, username, password, dbname, schema_file):
    """Execute schema SQL file"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=dbname,
            user=username,
            password=password
        )
        cursor = conn.cursor()
        
        # Read and execute schema file
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in schema_sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for statement in statements:
            # Skip psql meta-commands
            if statement.startswith('\\'):
                continue
            try:
                cursor.execute(statement)
                conn.commit()
            except Exception as e:
                print(f"Warning executing statement: {str(e)}")
                conn.rollback()
        
        print("Schema executed successfully")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error executing schema: {str(e)}")
        raise

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python init_db.py <secret_arn> [db_instance_id]")
        print("Example: python init_db.py arn:aws:secretsmanager:us-east-1:123456789012:secret:RDSSecret-abc123 seniorcare-db")
        sys.exit(1)
    
    secret_arn = sys.argv[1]
    db_instance_id = sys.argv[2] if len(sys.argv) > 2 else 'seniorcare-db'
    
    print("Fetching RDS credentials...")
    creds = get_rds_credentials(secret_arn)
    
    print("Fetching RDS endpoint...")
    host = get_rds_endpoint(db_instance_id)
    
    port = creds.get('port', 5432)
    username = creds['username']
    password = creds['password']
    dbname = 'seniorcare'
    
    print(f"Connecting to RDS at {host}:{port}")
    
    # Create database
    print("Creating database...")
    create_database(host, port, username, password, dbname)
    
    # Execute schema
    print("Executing schema...")
    schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
    execute_schema(host, port, username, password, dbname, schema_file)
    
    print("Database initialization complete!")

if __name__ == '__main__':
    main()
