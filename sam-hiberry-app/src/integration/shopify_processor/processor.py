# Shopify identifier
SHOPIFY_ID = 0

def process_shopify_event(shopify_data: dict) -> dict:
    """
    Process the Shopify event data and prepare the order data.

    Parameters:
    shopify_data (dict): The payload from Shopify webhook event.

    Returns:
    dict: Prepared order data for the 'CreateOrderFunction'.
    """

    # Retrieve customer info
    first_name = shopify_data.get("customer", {}).get("first_name")
    last_name = shopify_data.get("customer", {}).get("last_name")
    phone = shopify_data.get("customer", {}).get("phone")
    client_name = f"{first_name} {last_name}"

    # Retrieve shipping info
    shipping_address = shopify_data.get("shipping_address", {}).get("address1")

    # Retrieve latitude and longitude ,shipping_address with priority over billing_address
    latitude = None
    longitude = None

    for key in ["shipping_address", "billing_address"]:
        address = shopify_data.get(key, {})
        latitude = address.get("latitude")
        longitude = address.get("longitude")
        if latitude is not None and longitude is not None:
            break   
        
    # Retrieve cart info and payment 
    total_amount = float(shopify_data.get("total_price", 0))
    payment_method =  ','.join(shopify_data.get("payment_gateway_names", []))
    
    # Retrieve simplified cart items
    cart_items = []
    for item in shopify_data.get("line_items", []):
        simplified_item = {
            "name": item.get("name"),
            "price": item.get("price"),
            "quantity": item.get("quantity")
        }
        cart_items.append(simplified_item)

    # Map Shopify data to the required fields
    order_data = {
        "client_name": client_name,
        "phone_number": phone,
        "address": shipping_address,
        "latitude": latitude,
        "longitude": longitude,
        # TODO Review hiberry metafields !
        "delivery_date": None,
        # TODO Review hiberry metafields !
        "delivery_time": None,
        "cart_items": cart_items,
        "total_amount": total_amount,
        "payment_method": payment_method,
        "created_by": SHOPIFY_ID,
        # TODO check timestamp format!
        "created_at": shopify_data.get("created_at"),
        "updated_by": SHOPIFY_ID,
        "updated_at": shopify_data.get("updated_at"),
        "notes": shopify_data.get("note"),
    }

    return order_data
