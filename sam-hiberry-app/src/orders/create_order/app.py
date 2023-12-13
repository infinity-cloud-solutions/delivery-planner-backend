import json
from datetime import datetime
import uuid

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize logging
logger = Logger()


def lambda_handler(event, context: LambdaContext):
    """
    """

    try:
        data = json.loads(event['body'])

        order = {
            "id": str(uuid.uuid4()),  
            "client_name": data.get("client_name"),
            "delivery_date": data.get("delivery_date"),  
            "delivery_time": data.get("delivery_time"),
            "address": data.get("address"),
            "latitude": float(data.get("latitude", 0)),
            "longitude": float(data.get("longitude", 0)),
            "phone_number": data.get("phone_number"),
            "cart_items": data.get("cart_items", []),  
            "total_amount": float(data.get("total_amount", 0)),
            "payment_method": data.get("payment_method"),
            "created_by": int(data.get("created_by", 0)),
            "created_at": data.get("created_at", datetime.now().isoformat()),
            "updated_by": int(data.get("updated_by", 0)),
            "updated_at": data.get("updated_at", datetime.now().isoformat()),
            #"errors": data.get("errors", []), 
            #"notes": data.get("notes"),
            #"status": data.get("status"),
            #"delivery_sequence": int(data.get("delivery_sequence", 0))
        }
        
        logger.info(f'Order received and created: {order}')
        return {
            'statusCode': 200,
            'body': json.dumps('Order received and created successfully.')
        }

    except Exception as e:
        logger.error(f'Error processing the order: {str(e)}')
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing the order: {str(e)}')
        }
