# import requests

# def search_images(prompt, api_key, cx, num_results=10):
#     url = "https://www.googleapis.com/customsearch/v1"
#     params = {
#         "q": prompt,
#         "cx": cx,
#         "searchType": "image",
#         "num": num_results,
#         "safe": "medium",  # adjust to 'high' for strict safe search
#     }
#     headers = {"User-Agent": "Mozilla/5.0"}

#     response = requests.get(url, params=params, headers=headers)
#     response.raise_for_status()  # raise error if request fails
#     results = response.json()

#     image_links = [item["link"] for item in results.get("items", [])]
#     return image_links

# # Replace these with your keys
# API_KEY = "AIzaSyCImKcQl9Y2duzutwbrvO6J_6OS0znAsfQ"
# CX = "521cc18bf16f647da"

# prompt = "Java vs C# programming infographic"

# image_urls = search_images(prompt, API_KEY, CX, num_results=10)

# print("Found image URLs:")
# for url in image_urls:
#     print(url)


import requests
import urllib.parse

def search_images(prompt, api_key, cx, num_results=10):
    encoded_prompt = urllib.parse.quote(prompt)
    # https://www.googleapis.com/customsearch/v1?q=Java%20vs%20C%23%20programming%20infographic&cx=521cc18bf16f647da&searchType=image&key=AIzaSyCImKcQl9Y2duzutwbrvO6J_6OS0znAsfQ
    url = f"https://www.googleapis.com/customsearch/v1?q={encoded_prompt}&cx={cx}&searchType=image&key={api_key}"
    print(url)
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    results = response.json()

    image_links = [item["link"] for item in results.get("items", [])]
    return image_links

API_KEY = "AIzaSyCImKcQl9Y2duzutwbrvO6J_6OS0znAsfQ"
CX = "521cc18bf16f647da"
prompt = "Java programming language logo"

image_urls = search_images(prompt, API_KEY, CX, num_results=10)
for url in image_urls:
    print(url)
