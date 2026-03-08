import boto3
import uuid
import os
from decimal import Decimal
from datetime import datetime, date

# AWS Configuration
# For local development
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Set up boto3 session
if AWS_ACCESS_KEY and AWS_SECRET_KEY:
    # Local development with explicit credentials
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )
else:
    # EC2 instance with IAM role
    session = boto3.Session(region_name=AWS_REGION)

# Create DynamoDB resource and client
dynamodb = session.resource('dynamodb')
dynamodb_client = session.client('dynamodb')

# Define table names
USER_TABLE = 'stocker_users'
STOCK_TABLE = 'stocker_stocks'
TRANSACTION_TABLE = 'stocker_transactions'
PORTFOLIO_TABLE = 'stocker_portfolio'

# Check if tables exist, if not create them
existing_tables = dynamodb_client.list_tables()['TableNames']

def create_table_if_not_exists(table_name, key_schema, attribute_definitions):
    if table_name not in existing_tables:
        print(f"Creating table: {table_name}")
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            BillingMode='PAY_PER_REQUEST'  # On-demand capacity
        )
        # Wait until table is created
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print(f"Table {table_name} created successfully!")
    else:
        print(f"Table {table_name} already exists.")

# Create Users Table
create_table_if_not_exists(
    USER_TABLE,
    key_schema=[
        {'AttributeName': 'email', 'KeyType': 'HASH'}  # Partition key
    ],
    attribute_definitions=[
        {'AttributeName': 'email', 'AttributeType': 'S'}
    ]
)

# Create Stocks Table
create_table_if_not_exists(
    STOCK_TABLE,
    key_schema=[
        {'AttributeName': 'id', 'KeyType': 'HASH'}  # Partition key
    ],
    attribute_definitions=[
        {'AttributeName': 'id', 'AttributeType': 'S'}
    ]
)

# Create Transactions Table
create_table_if_not_exists(
    TRANSACTION_TABLE,
    key_schema=[
        {'AttributeName': 'id', 'KeyType': 'HASH'}  # Partition key
    ],
    attribute_definitions=[
        {'AttributeName': 'id', 'AttributeType': 'S'}
    ]
)

# Create Portfolio Table
create_table_if_not_exists(
    PORTFOLIO_TABLE,
    key_schema=[
        {'AttributeName': 'user_id', 'KeyType': 'HASH'},  # Partition key
        {'AttributeName': 'stock_id', 'KeyType': 'RANGE'}  # Sort key
    ],
    attribute_definitions=[
        {'AttributeName': 'user_id', 'AttributeType': 'S'},
        {'AttributeName': 'stock_id', 'AttributeType': 'S'}
    ]
)

# Sample data setup
def add_sample_data():
    # Add Users
    user_table = dynamodb.Table(USER_TABLE)
    users = [
        {"id": str(uuid.uuid4()), "username": "Admin User", "email": "admin@example.com", "password": "admin123", "role": "admin"},
        {"id": str(uuid.uuid4()), "username": "Trader One", "email": "trader1@example.com", "password": "trader123", "role": "trader"},
        {"id": str(uuid.uuid4()), "username": "Trader Two", "email": "trader2@example.com", "password": "trader123", "role": "trader"}
    ]
    
    for user in users:
        # Check if user exists
        response = user_table.get_item(Key={'email': user['email']})
        if 'Item' not in response:
            user_table.put_item(Item=user)
            print(f"Added user: {user['username']}")
        else:
            print(f"User {user['email']} already exists.")
    
    # Get the created users for reference in other tables
    trader1 = None
    trader2 = None
    for user in users:
        if user['email'] == 'trader1@example.com':
            trader1 = user
        elif user['email'] == 'trader2@example.com':
            trader2 = user
    
    # Add Stocks
    stock_table = dynamodb.Table(STOCK_TABLE)
    nifty50_sample = [
        {"id": str(uuid.uuid4()), "symbol": "RELIANCE", "name": "Reliance Industries Ltd", "price": Decimal('2500.00'), "market_cap": Decimal('1700000'), "sector": "Energy", "industry": "Oil & Gas", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "TCS", "name": "Tata Consultancy Services Ltd", "price": Decimal('3600.00'), "market_cap": Decimal('1300000'), "sector": "IT", "industry": "IT Services", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "HDFCBANK", "name": "HDFC Bank Ltd", "price": Decimal('1600.00'), "market_cap": Decimal('1100000'), "sector": "Financials", "industry": "Bank", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "ICICIBANK", "name": "ICICI Bank Ltd", "price": Decimal('1100.00'), "market_cap": Decimal('800000'), "sector": "Financials", "industry": "Bank", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "INFY", "name": "Infosys Ltd", "price": Decimal('1500.00'), "market_cap": Decimal('700000'), "sector": "IT", "industry": "IT Services", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd", "price": Decimal('2500.00'), "market_cap": Decimal('650000'), "sector": "Consumer Goods", "industry": "FMCG", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "ITC", "name": "ITC Ltd", "price": Decimal('450.00'), "market_cap": Decimal('550000'), "sector": "Consumer Goods", "industry": "FMCG", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank Ltd", "price": Decimal('1700.00'), "market_cap": Decimal('450000'), "sector": "Financials", "industry": "Bank", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "LT", "name": "Larsen & Toubro Ltd", "price": Decimal('3300.00'), "market_cap": Decimal('400000'), "sector": "Industrials", "industry": "Construction", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "SBIN", "name": "State Bank of India", "price": Decimal('750.00'), "market_cap": Decimal('380000'), "sector": "Financials", "industry": "Bank", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd", "price": Decimal('1000.00'), "market_cap": Decimal('350000'), "sector": "Communication", "industry": "Telecom", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "BAJFINANCE", "name": "Bajaj Finance Ltd", "price": Decimal('7000.00'), "market_cap": Decimal('300000'), "sector": "Financials", "industry": "NBFC", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "ASIANPAINT", "name": "Asian Paints Ltd", "price": Decimal('3200.00'), "market_cap": Decimal('250000'), "sector": "Consumer Goods", "industry": "Paints", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "AXISBANK", "name": "Axis Bank Ltd", "price": Decimal('1000.00'), "market_cap": Decimal('240000'), "sector": "Financials", "industry": "Bank", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "HCLTECH", "name": "HCL Technologies Ltd", "price": Decimal('1600.00'), "market_cap": Decimal('230000'), "sector": "IT", "industry": "IT Services", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "MARUTI", "name": "Maruti Suzuki India Ltd", "price": Decimal('12000.00'), "market_cap": Decimal('220000'), "sector": "Consumer Goods", "industry": "Automobiles", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries Ltd", "price": Decimal('1300.00'), "market_cap": Decimal('210000'), "sector": "Healthcare", "industry": "Pharma", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "BAJAJFINSV", "name": "Bajaj Finserv Ltd", "price": Decimal('1700.00'), "market_cap": Decimal('200000'), "sector": "Financials", "industry": "NBFC", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "TITAN", "name": "Titan Company Ltd", "price": Decimal('3500.00'), "market_cap": Decimal('195000'), "sector": "Consumer Goods", "industry": "Luxury Goods", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "ULTRACEMCO", "name": "UltraTech Cement Ltd", "price": Decimal('9000.00'), "market_cap": Decimal('180000'), "sector": "Industrials", "industry": "Cement", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "NTPC", "name": "NTPC Ltd", "price": Decimal('300.00'), "market_cap": Decimal('170000'), "sector": "Utilities", "industry": "Power", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "POWERGRID", "name": "Power Grid Corporation of India Ltd", "price": Decimal('250.00'), "market_cap": Decimal('160000'), "sector": "Utilities", "industry": "Power", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "ADANIENT", "name": "Adani Enterprises Ltd", "price": Decimal('3100.00'), "market_cap": Decimal('150000'), "sector": "Conglomerate", "industry": "Diversified", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "JSWSTEEL", "name": "JSW Steel Ltd", "price": Decimal('900.00'), "market_cap": Decimal('140000'), "sector": "Materials", "industry": "Steel", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "TATASTEEL", "name": "Tata Steel Ltd", "price": Decimal('150.00'), "market_cap": Decimal('130000'), "sector": "Materials", "industry": "Steel", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "HDFCLIFE", "name": "HDFC Life Insurance Company Ltd", "price": Decimal('600.00'), "market_cap": Decimal('120000'), "sector": "Financials", "industry": "Insurance", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "TECHM", "name": "Tech Mahindra Ltd", "price": Decimal('1200.00'), "market_cap": Decimal('115000'), "sector": "IT", "industry": "IT Services", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "WIPRO", "name": "Wipro Ltd", "price": Decimal('600.00'), "market_cap": Decimal('110000'), "sector": "IT", "industry": "IT Services", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "BRITANNIA", "name": "Britannia Industries Ltd", "price": Decimal('5000.00'), "market_cap": Decimal('100000'), "sector": "Consumer Goods", "industry": "FMCG", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "CIPLA", "name": "Cipla Ltd", "price": Decimal('1200.00'), "market_cap": Decimal('95000'), "sector": "Healthcare", "industry": "Pharma", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "DIVISLAB", "name": "Divi's Laboratories Ltd", "price": Decimal('3700.00'), "market_cap": Decimal('90000'), "sector": "Healthcare", "industry": "Pharma", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "GRASIM", "name": "Grasim Industries Ltd", "price": Decimal('2200.00'), "market_cap": Decimal('85000'), "sector": "Materials", "industry": "Cement", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "BPCL", "name": "Bharat Petroleum Corporation Ltd", "price": Decimal('550.00'), "market_cap": Decimal('80000'), "sector": "Energy", "industry": "Oil & Gas", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "ONGC", "name": "Oil and Natural Gas Corporation Ltd", "price": Decimal('250.00'), "market_cap": Decimal('75000'), "sector": "Energy", "industry": "Oil & Gas", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "ADANIPORTS", "name": "Adani Ports and Special Economic Zone Ltd", "price": Decimal('1200.00'), "market_cap": Decimal('70000'), "sector": "Industrials", "industry": "Logistics", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "DRREDDY", "name": "Dr. Reddy's Laboratories Ltd", "price": Decimal('5700.00'), "market_cap": Decimal('65000'), "sector": "Healthcare", "industry": "Pharma", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "HINDALCO", "name": "Hindalco Industries Ltd", "price": Decimal('650.00'), "market_cap": Decimal('60000'), "sector": "Materials", "industry": "Aluminium", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "INDUSINDBK", "name": "IndusInd Bank Ltd", "price": Decimal('1400.00'), "market_cap": Decimal('58000'), "sector": "Financials", "industry": "Bank", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "EICHERMOT", "name": "Eicher Motors Ltd", "price": Decimal('4000.00'), "market_cap": Decimal('56000'), "sector": "Consumer Goods", "industry": "Automobiles", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "HEROMOTOCO", "name": "Hero MotoCorp Ltd", "price": Decimal('3200.00'), "market_cap": Decimal('54000'), "sector": "Consumer Goods", "industry": "Automobiles", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "APOLLOHOSP", "name": "Apollo Hospitals Enterprise Ltd", "price": Decimal('5400.00'), "market_cap": Decimal('50000'), "sector": "Healthcare", "industry": "Hospitals", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "SBILIFE", "name": "SBI Life Insurance Company Ltd", "price": Decimal('1400.00'), "market_cap": Decimal('48000'), "sector": "Financials", "industry": "Insurance", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "ICICIPRULI", "name": "ICICI Prudential Life Insurance Company Ltd", "price": Decimal('550.00'), "market_cap": Decimal('46000'), "sector": "Financials", "industry": "Insurance", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "TATACONSUM", "name": "Tata Consumer Products Ltd", "price": Decimal('900.00'), "market_cap": Decimal('44000'), "sector": "Consumer Goods", "industry": "FMCG", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "UPL", "name": "UPL Ltd", "price": Decimal('600.00'), "market_cap": Decimal('42000'), "sector": "Materials", "industry": "Agro Chemicals", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "COALINDIA", "name": "Coal India Ltd", "price": Decimal('300.00'), "market_cap": Decimal('40000'), "sector": "Materials", "industry": "Mining", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "SHREECEM", "name": "Shree Cement Ltd", "price": Decimal('27000.00'), "market_cap": Decimal('38000'), "sector": "Industrials", "industry": "Cement", "date_added": date.today().isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "BAJAJ-AUTO", "name": "Bajaj Auto Ltd", "price": Decimal('5000.00'), "market_cap": Decimal('36000'), "sector": "Consumer Goods", "industry": "Automobiles", "date_added": date.today().isoformat()}        
    ]
    
    # Create a dictionary to store stock ids for reference
    stock_ids = {}
    
    for stock in nifty50_sample:
        # Check if stock exists by symbol
        response = stock_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('symbol').eq(stock['symbol'])
        )
        
        if not response.get('Items'):
            stock_table.put_item(Item=stock)
            print(f"Added stock: {stock['symbol']}")
            stock_ids[stock['symbol']] = stock['id']
        else:
            existing_stock = response['Items'][0]
            print(f"Stock {stock['symbol']} already exists.")
            stock_ids[stock['symbol']] = existing_stock['id']
    
    # Add sample transactions and portfolio items if traders and stocks exist
    if trader1 and trader2 and stock_ids:
        transaction_table = dynamodb.Table(TRANSACTION_TABLE)
        portfolio_table = dynamodb.Table(PORTFOLIO_TABLE)
        
        # Trader 1 buys RELIANCE and TCS
        if 'RELIANCE' in stock_ids and 'TCS' in stock_ids:
            # Transaction for RELIANCE
            reliance_txn = {
                'id': str(uuid.uuid4()),
                'user_id': trader1['id'],
                'stock_id': stock_ids['RELIANCE'],
                'action': 'buy',
                'quantity': 10,
                'price': Decimal('2500.00'),
                'status': 'completed',
                'transaction_date': datetime.now().isoformat()
            }
            
            # Check if transaction exists (by user_id and stock_id)
            response = transaction_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('user_id').eq(trader1['id']) & 
                                boto3.dynamodb.conditions.Attr('stock_id').eq(stock_ids['RELIANCE'])
            )
            
            if not response.get('Items'):
                transaction_table.put_item(Item=reliance_txn)
                print(f"Added transaction: Trader1 buys RELIANCE")
                
                # Add to portfolio
                portfolio_table.put_item(Item={
                    'user_id': trader1['id'],
                    'stock_id': stock_ids['RELIANCE'],
                    'quantity': 10,
                    'average_price': Decimal('2500.00')
                })
                print(f"Added portfolio item: Trader1 owns RELIANCE")
            
            # Transaction for TCS
            tcs_txn = {
                'id': str(uuid.uuid4()),
                'user_id': trader1['id'],
                'stock_id': stock_ids['TCS'],
                'action': 'buy',
                'quantity': 5,
                'price': Decimal('3600.00'),
                'status': 'completed',
                'transaction_date': datetime.now().isoformat()
            }
            
            # Check if transaction exists
            response = transaction_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('user_id').eq(trader1['id']) & 
                                boto3.dynamodb.conditions.Attr('stock_id').eq(stock_ids['TCS'])
            )
            
            if not response.get('Items'):
                transaction_table.put_item(Item=tcs_txn)
                print(f"Added transaction: Trader1 buys TCS")
                
                # Add to portfolio
                portfolio_table.put_item(Item={
                    'user_id': trader1['id'],
                    'stock_id': stock_ids['TCS'],
                    'quantity': 5,
                    'average_price': Decimal('3600.00')
                })
                print(f"Added portfolio item: Trader1 owns TCS")
        
        # Trader 2 buys HDFCBANK
        if 'HDFCBANK' in stock_ids:
            # Transaction for HDFCBANK
            hdfc_txn = {
                'id': str(uuid.uuid4()),
                'user_id': trader2['id'],
                'stock_id': stock_ids['HDFCBANK'],
                'action': 'buy',
                'quantity': 15,
                'price': Decimal('1600.00'),
                'status': 'completed',
                'transaction_date': datetime.now().isoformat()
            }
            
            # Check if transaction exists
            response = transaction_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('user_id').eq(trader2['id']) & 
                                boto3.dynamodb.conditions.Attr('stock_id').eq(stock_ids['HDFCBANK'])
            )
            
            if not response.get('Items'):
                transaction_table.put_item(Item=hdfc_txn)
                print(f"Added transaction: Trader2 buys HDFCBANK")
                
                # Add to portfolio
                portfolio_table.put_item(Item={
                    'user_id': trader2['id'],
                    'stock_id': stock_ids['HDFCBANK'],
                    'quantity': 15,
                    'average_price': Decimal('1600.00')
                })
                print(f"Added portfolio item: Trader2 owns HDFCBANK")

# Execute the sample data loading function
add_sample_data()

print("DynamoDB setup completed successfully!")