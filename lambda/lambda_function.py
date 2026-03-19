from src.ingest.ingest_job import main

def lambda_handler(event, context):
    main()
    
    return {
        "statusCode": 200,
        "body": "Ingestion completed"
    }