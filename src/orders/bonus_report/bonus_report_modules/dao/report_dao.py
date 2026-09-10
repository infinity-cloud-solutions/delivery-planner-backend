from typing import Any, Dict, List

import boto3
from aws_lambda_powertools import Logger
from boto3.dynamodb.conditions import Attr, Key

# OrderSource.SHOPIFY = 0; using the literal to avoid a cross-module import
_SHOPIFY_SOURCE = 0

# Fixed UTC-6 offset used when writing created_at, consistent with order_mapper.py
_MX_OFFSET = "-06:00"


class ReportDAO:
    """Queries the Orders table GSI to retrieve orders for a creation period."""

    def __init__(self, table_name: str, index_name: str, dynamodb_resource=None):
        self.logger = Logger()
        resource = dynamodb_resource or boto3.resource(
            "dynamodb", region_name="us-east-1"
        )
        self.table = resource.Table(table_name)
        self.index_name = index_name

    def query_orders_by_creation_period(
        self,
        created_month: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """Return all non-Shopify orders whose created_date_mx falls within [start_date, end_date]."""
        start_at = f"{start_date}T00:00:00{_MX_OFFSET}"
        end_at = f"{end_date}T23:59:59{_MX_OFFSET}"
        key_expr = Key("created_month").eq(created_month) & Key("created_at").between(
            start_at, end_at
        )
        filter_expr = Attr("source").ne(_SHOPIFY_SOURCE)

        items: List[Dict[str, Any]] = []
        kwargs: Dict[str, Any] = {
            "IndexName": self.index_name,
            "KeyConditionExpression": key_expr,
            "FilterExpression": filter_expr,
        }

        while True:
            response = self.table.query(**kwargs)
            items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            kwargs["ExclusiveStartKey"] = last_key

        self.logger.info(
            f"Fetched {len(items)} orders for {created_month} [{start_date} → {end_date}]"
        )
        return items
