from flask import Flask, request, render_template_string
import requests
import json
import os

app = Flask(_name_)

# API Gateway URL (Replace with your actual API Gateway URL)
API_URL = "https://bdh2pqhiv4qkaxhly6veqbvmoy0lqrtr.lambda-url.us-east-1.on.aws/"

@app.route('/')
def index():
    # The form to accept product and limit from user
    return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Flipkart Scraper</title>
            <style>
                body {
                    font-family: 'Arial', sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f4f7fc;
                    color: #333;
                }
                header {
                    background-color: #007bff;
                    color: white;
                    padding: 15px;
                    text-align: center;
                    font-size: 24px;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                form {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                }
                label {
                    font-size: 18px;
                    margin-bottom: 10px;
                    display: block;
                }
                input[type="text"], input[type="number"] {
                    width: 100%;
                    padding: 10px;
                    margin: 10px 0;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    box-sizing: border-box;
                }
                button {
                    padding: 10px 20px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 16px;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #0056b3;
                }
                h1 {
                    text-align: center;
                    color: #333;
                }
                ul {
                    list-style-type: none;
                    padding: 0;
                }
                li {
                    background: white;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 8px;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                }
                a {
                    text-decoration: none;
                    color: #007bff;
                }
                a:hover {
                    text-decoration: underline;
                }
                .back-link {
                    display: block;
                    text-align: center;
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <header>Flipkart Product Scraper</header>
            <div class="container">
                <form action="/scrape" method="POST">
                    <label for="product">Product:</label>
                    <input type="text" id="product" name="product" required>
                    <label for="limit">Limit (Top N Products):</label>
                    <input type="number" id="limit" name="limit" value="3" required>
                    <button type="submit">Get Products</button>
                </form>
            </div>
        </body>
        </html>
    """)

@app.route('/scrape', methods=['POST'])
def scrape():
    # Get user input from form
    product = request.form['product']
    limit = int(request.form['limit'])

    # Prepare the data to send to API Gateway
    payload = {
        "product": product,
        "limit": limit
    }

    headers = {"Content-Type": "application/json"}
    
    # Send the POST request to API Gateway
    response = requests.post(API_URL, json=payload, headers=headers)

    if response.status_code == 200:
        result = response.json()
        return render_template_string("""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Scraped Products</title>
                <style>
                    body {
                        font-family: 'Arial', sans-serif;
                        margin: 0;
                        padding: 0;
                        background-color: #f4f7fc;
                        color: #333;
                    }
                    header {
                        background-color: #007bff;
                        color: white;
                        padding: 15px;
                        text-align: center;
                        font-size: 24px;
                    }
                    .container {
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    ul {
                        list-style-type: none;
                        padding: 0;
                    }
                    li {
                        background: white;
                        padding: 15px;
                        margin: 10px 0;
                        border-radius: 8px;
                        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                    }
                    a {
                        text-decoration: none;
                        color: #007bff;
                    }
                    a:hover {
                        text-decoration: underline;
                    }
                    .back-link {
                        display: block;
                        text-align: center;
                        margin-top: 20px;
                    }
                </style>
            </head>
            <body>
                <header>Scraped Products</header>
                <div class="container">
                    <ul>
                        {% for product in result['results'] %}
                            <li>
                                <a href="{{ product['url'] }}" target="_blank">{{ product['name'] }}</a><br>
                                Price: {{ product.get('price', 'Not available') }}<br>
                                Rating: {{ product.get('ratingValue', 'Not available') }}
                            </li>
                        {% endfor %}
                    </ul>
                    <a class="back-link" href="/">Back to Home</a>
                </div>
            </body>
            </html>
        """, result=result)
    else:
        return f"Error: {response.status_code}"

if _name_ == "_main_":
    app.run(host='0.0.0.0', port=5000)
