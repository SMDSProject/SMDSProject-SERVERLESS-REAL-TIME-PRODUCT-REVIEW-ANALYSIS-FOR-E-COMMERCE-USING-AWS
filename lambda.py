import json
import requests
from bs4 import BeautifulSoup
import boto3
from datetime import datetime
import os

def lambda_handler(event, context):
    print("🔹 Received event:", event)

    # Get ScraperAPI Key from env
    SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY", "f4c48108d21c4d933feb8cf7e3c5785a")


    try:
        body = json.loads(event.get("body", "{}"))
    except Exception as e:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid request body"})}


    product = body.get("product", "laptop")
    limit = int(body.get("limit", 3))  # Default limit is 3 if not provided
    #try:
    #    product = event.get('product')
    #    print(product)
    #    limit = int(event.get('limit'))  # Default limit is 3 if not provided
    #    print(limit)
    #except Exception as e:
    #    return {"statusCode": 400, "body": json.dumps({"error": "Invalid request body"})}

    

    original_url = f"https://www.flipkart.com/search?q={product.replace(' ', '+')}"
    scrape_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={original_url}&render=true&premium=true"

    # Send the request to ScraperAPI
    response = requests.get(scrape_url)
    print(response.text)  # Print a preview of the full page response for debugging

    # If the response is not successful, return an error
    if response.status_code != 200 or "captcha" in response.text.lower():
        print(" Blocked or invalid page")
        return {
            "statusCode": 403,
            "body": json.dumps({"error": "Blocked by Flipkart or invalid HTML"})
        }

    # Parse the full HTML with BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    #  Find the script tag that contains the product JSON (ld+json)
    script_tag = soup.find("script", {"type": "application/ld+json", "id": "jsonLD"})
    if not script_tag:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Could not find Flipkart JSONLD data"})
        }

    try:
        embedded_json = json.loads(script_tag.string)
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Failed to parse Flipkart JSONLD: {str(e)}"})
        }

    #  Extract product list from the 'itemListElement' in JSON and limit the results
    try:
        products = embedded_json['itemListElement'][:20]  # Apply limit here
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Failed to extract product list: {str(e)}"})
        }

    # Function to fetch price and rating for each product URL
    def fetch_product_details(product_url):
        """
        Given a product URL, fetch the price and rating from the product page's ld+json
        """
        print(f"🔹 Fetching details for URL: {product_url}")
        scrape_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={product_url}&render=true&premium=true"
        
        response = requests.get(scrape_url)
        print(response.text)
        if response.status_code != 200:
            print(f" Error fetching product details for {product_url}")
            return None
        
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the <script> tag containing ld+json
        script_tag = soup.find("script", {"type": "application/ld+json", "id": "jsonLD"})
        if not script_tag:
            print(" JSONLD script tag not found!")
            return None

        try:
            embedded_json = json.loads(script_tag.string)
        except Exception as e:
            print(f" Error parsing JSONLD: {e}")
            return None

        price = None
        rating_value = None

        for data in embedded_json:
            if data.get('@type') == 'Product':
                if 'offers' in data:
                    price = data['offers'].get('price', 'Not available')
                if 'aggregateRating' in data:
                    rating_value = data['aggregateRating'].get('ratingValue', 'Not available')

        return {"price": price, "ratingValue": rating_value}

    # Process the products and fetch additional data
    results = []
    for p in products:
        try:
            name = p.get('name', 'Unknown')
            url = p.get('url', '')
            if url:
                stars = "Not rated"  # There may not be star ratings in this data
                breakdown = "Not available"  # No breakdown available in this data

                # Fetch price and rating for each product URL
                details = fetch_product_details(url)
                if details:
                    price = details.get("price", "Not available")
                    rating_value = details.get("ratingValue", "Not available")
                else:
                    price = "Not available"
                    rating_value = "Not available"

                # Add product details and link to results
                results.append({
                    "name": name,
                    "url": url,
                    "price": price,
                    "ratingValue": rating_value
                })
        except Exception as e:
            print(f" Error parsing product: {str(e)}")
            continue

    print(f" Parsed {len(results)} products")

    #  Sort results by rating (if available and numeric)
    def safe_rating(product):
        try:
            return float(product.get("ratingValue", 0))
        except:
            return 0

    results.sort(key=safe_rating, reverse=True)  # Highest rated first
    results = results[:limit]  # Take top N highest rated products


    #  Upload to S3
    s3 = boto3.client('s3')
    bucket_name = os.environ.get('BUCKET_NAME', 'product-results')
    key = f'flipkart-results/{product.replace(" ", "_")}-{datetime.utcnow().isoformat()}.json'

    s3.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=json.dumps(results),
        ContentType='application/json'
    )

    #  Read back from S3
    s3_response = s3.get_object(Bucket=bucket_name, Key=key)
    stored_results = json.loads(s3_response['Body'].read().decode('utf-8'))

    return {
        "statusCode": 200,
        "body": json.dumps({
            "product": product,
            "results": stored_results
        })
    }
