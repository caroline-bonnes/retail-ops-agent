from google.cloud import bigquery


def create_mock_dataset():
    client = bigquery.Client()
    project = client.project
    dataset_id = f"{project}.retail_ops"

    # Construct a QueryJobConfig or create dataset directly
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"

    dataset = client.create_dataset(dataset, timeout=30, exists_ok=True)
    print(f"Created dataset {client.project}.{dataset.dataset_id}")

    # Define tables
    tables = {
        "stores": [
            bigquery.SchemaField("store_id", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("city", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("manager", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("phone", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("open_date", "DATE", mode="NULLABLE"),
        ],
        "inventory": [
            bigquery.SchemaField("store_id", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("department", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("product_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("stock_count", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("reorder_point", "INT64", mode="REQUIRED"),
        ],
        "sales": [
            bigquery.SchemaField("transaction_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("store_id", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("transaction_time", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("product_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("quantity", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("unit_price", "NUMERIC", mode="REQUIRED"),
            bigquery.SchemaField("total_amount", "NUMERIC", mode="REQUIRED"),
        ],
        "customer_satisfaction": [
            bigquery.SchemaField("store_id", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("rating", "FLOAT64", mode="REQUIRED"),
            bigquery.SchemaField("reviews_count", "INT64", mode="REQUIRED"),
        ],
    }

    for table_name, schema in tables.items():
        table_id = f"{dataset_id}.{table_name}"
        table = bigquery.Table(table_id, schema=schema)
        try:
            table = client.create_table(table, exists_ok=True)
            print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")
        except Exception as e:
            print(f"Failed to create table {table_name}: {e}")

    # Populate tables
    # 1. Stores
    stores_data = [
        {
            "store_id": 101,
            "city": "San Francisco",
            "manager": "Alice Smith",
            "phone": "555-0101",
            "open_date": "2015-06-01",
        },
        {
            "store_id": 102,
            "city": "New York",
            "manager": "Bob Jones",
            "phone": "555-0102",
            "open_date": "2018-04-12",
        },
        {
            "store_id": 103,
            "city": "Los Angeles",
            "manager": "Charlie Brown",
            "phone": "555-0103",
            "open_date": "2020-11-20",
        },
        {
            "store_id": 104,
            "city": "Chicago",
            "manager": "Diana Prince",
            "phone": "555-0104",
            "open_date": "2021-02-15",
        },
        {
            "store_id": 105,
            "city": "Seattle",
            "manager": "Evan Wright",
            "phone": "555-0105",
            "open_date": "2019-09-30",
        },
    ]
    client.insert_rows_json(f"{dataset_id}.stores", stores_data)
    print("Populated stores table")

    # 2. Inventory
    inventory_data = [
        {
            "store_id": 101,
            "department": "Electronics",
            "product_name": "Smart TV 55",
            "stock_count": 25,
            "reorder_point": 10,
        },
        {
            "store_id": 101,
            "department": "Electronics",
            "product_name": "Wireless Headphones",
            "stock_count": 8,
            "reorder_point": 15,
        },  # Needs reorder
        {
            "store_id": 101,
            "department": "Home & Kitchen",
            "product_name": "Blender Pro",
            "stock_count": 14,
            "reorder_point": 5,
        },
        {
            "store_id": 102,
            "department": "Electronics",
            "product_name": "Smart TV 55",
            "stock_count": 12,
            "reorder_point": 10,
        },
        {
            "store_id": 102,
            "department": "Electronics",
            "product_name": "Wireless Headphones",
            "stock_count": 30,
            "reorder_point": 15,
        },
        {
            "store_id": 103,
            "department": "Electronics",
            "product_name": "Smart TV 55",
            "stock_count": 3,
            "reorder_point": 10,
        },  # Needs reorder
        {
            "store_id": 103,
            "department": "Home & Kitchen",
            "product_name": "Air Fryer XL",
            "stock_count": 2,
            "reorder_point": 5,
        },  # Needs reorder
        {
            "store_id": 104,
            "department": "Clothing",
            "product_name": "Winter Jacket",
            "stock_count": 45,
            "reorder_point": 20,
        },
        {
            "store_id": 105,
            "department": "Electronics",
            "product_name": "Smart TV 55",
            "stock_count": 5,
            "reorder_point": 10,
        },  # Needs reorder
        {
            "store_id": 105,
            "department": "Clothing",
            "product_name": "Winter Jacket",
            "stock_count": 4,
            "reorder_point": 15,
        },  # Needs reorder
    ]
    client.insert_rows_json(f"{dataset_id}.inventory", inventory_data)
    print("Populated inventory table")

    # 3. Sales
    sales_data = [
        {
            "transaction_id": "T10001",
            "store_id": 101,
            "transaction_time": "2026-08-15T10:30:00Z",
            "product_name": "Smart TV 55",
            "quantity": 1,
            "unit_price": 499.99,
            "total_amount": 499.99,
        },
        {
            "transaction_id": "T10002",
            "store_id": 101,
            "transaction_time": "2026-08-15T11:15:00Z",
            "product_name": "Wireless Headphones",
            "quantity": 2,
            "unit_price": 89.99,
            "total_amount": 179.98,
        },
        {
            "transaction_id": "T10003",
            "store_id": 102,
            "transaction_time": "2026-08-15T12:00:00Z",
            "product_name": "Smart TV 55",
            "quantity": 1,
            "unit_price": 499.99,
            "total_amount": 499.99,
        },
        {
            "transaction_id": "T10004",
            "store_id": 103,
            "transaction_time": "2026-08-16T14:45:00Z",
            "product_name": "Air Fryer XL",
            "quantity": 1,
            "unit_price": 129.99,
            "total_amount": 129.99,
        },
        {
            "transaction_id": "T10005",
            "store_id": 104,
            "transaction_time": "2026-08-16T16:20:00Z",
            "product_name": "Winter Jacket",
            "quantity": 3,
            "unit_price": 79.99,
            "total_amount": 239.97,
        },
        {
            "transaction_id": "T10006",
            "store_id": 101,
            "transaction_time": "2026-08-17T09:00:00Z",
            "product_name": "Blender Pro",
            "quantity": 1,
            "unit_price": 59.99,
            "total_amount": 59.99,
        },
        {
            "transaction_id": "T10007",
            "store_id": 105,
            "transaction_time": "2026-08-17T15:10:00Z",
            "product_name": "Smart TV 55",
            "quantity": 2,
            "unit_price": 499.99,
            "total_amount": 999.98,
        },
    ]
    client.insert_rows_json(f"{dataset_id}.sales", sales_data)
    print("Populated sales table")

    # 4. Customer Satisfaction
    satisfaction_data = [
        {"store_id": 101, "date": "2026-08-15", "rating": 4.6, "reviews_count": 25},
        {"store_id": 101, "date": "2026-08-16", "rating": 4.8, "reviews_count": 30},
        {"store_id": 102, "date": "2026-08-15", "rating": 4.2, "reviews_count": 18},
        {"store_id": 103, "date": "2026-08-16", "rating": 3.9, "reviews_count": 12},
        {"store_id": 104, "date": "2026-08-16", "rating": 4.5, "reviews_count": 22},
        {"store_id": 105, "date": "2026-08-17", "rating": 4.7, "reviews_count": 15},
    ]
    client.insert_rows_json(f"{dataset_id}.customer_satisfaction", satisfaction_data)
    print("Populated customer_satisfaction table")


if __name__ == "__main__":
    create_mock_dataset()
