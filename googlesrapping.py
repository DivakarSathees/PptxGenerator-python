# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from bs4 import BeautifulSoup
# import time

# def scrape_google_images(query, num_images=10):
#     options = Options()
#     options.add_argument("--headless")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")

#     driver = webdriver.Chrome(options=options)
#     search_url = f"https://www.google.com/search?tbm=isch&q={query}"
#     print(f"Scraping URL: {search_url}")
#     driver.get(search_url)

#     # Scroll down to load images
#     for _ in range(3):
#         driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
#         time.sleep(2)

#     soup = BeautifulSoup(driver.page_source, "html.parser")
#     with open("debug_google_images.html", "w", encoding="utf-8") as f:
#         f.write(soup.prettify())
#     driver.quit()

#     image_urls = []
#     for img_tag in soup.find_all("img"):
#         src = img_tag.get("src")
#         if src and src.startswith("data:"):
#             is_valid = is_valid_image(src)
#             if is_valid:
#                 image_urls.append(src)
#                 print("Found valid image")
#             else:
#                 print(f"Image too small or invalid")
#         if len(image_urls) >= num_images:
#             break

#     return image_urls

# # create function to read the imageurl and check it is valid by checking the size 400 x 400
# def is_valid_image(url):
#     try:
#         from PIL import Image
#         from io import BytesIO
#         import base64

#         header, encoded = url.split(",", 1)
#         data = base64.b64decode(encoded)
#         image = Image.open(BytesIO(data))
#         width, height = image.size
#         print(f"Image size: {width}x{height}")
#         return width >= 200 and height >= 100
#     except Exception as e:
#         print(f"Error validating image: {e}")
#         return False


# # Example usage
# images = scrape_google_images("ai-nlp-presentation-workflow-diagram", num_images=100)
# for url in images:
#     with open("debug_image_urls.txt", "a", encoding="utf-8") as f:
#          f.write(url + "\n")
#     # print(url)


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import urllib.parse

def scrape_google_images(query, num_images=5):
    options = Options()
    # options.add_argument("--headless")  # keep visible for debugging
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    encoded_prompt = urllib.parse.quote(query)
    search_url = f"https://www.google.com/search?tbm=isch&q={encoded_prompt}"
    print(f"Scraping URL: {search_url}")
    driver.get(search_url)

    image_urls = []

    # Wait for thumbnails to load
    thumbnails = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h3.ob5Hkd img.YQ4gaf"))
    )
    print(f"Found {len(thumbnails)} thumbnails")

    for idx, thumb in enumerate(thumbnails[:num_images]):
        try:
            driver.execute_script("arguments[0].click();", thumb)
            time.sleep(1)

            # Wait for the large preview image
            img = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img.iPVvYb"))
            )

            src = img.get_attribute("src")
            if src and re.search(r"\.(jpg|jpeg|png|gif|webp)", src, re.IGNORECASE):
                if src not in image_urls:
                    image_urls.append(src)
                    print(f"✅ Found full image: {src[:100]}...")

        except Exception as e:
            print(f"⚠️ Error on thumbnail {idx}: {e}")
            continue

    driver.quit()
    return image_urls

# def scrape_google_images(query, num_images=10):
#     options = Options()
#     # options.add_argument("--headless")   # run headless (remove if you want browser visible)
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")

#     driver = webdriver.Chrome(options=options)
#     search_url = f"https://www.google.com/search?tbm=isch&q={query}"
#     print(f"Scraping URL: {search_url}")
#     driver.get(search_url)

#     # image_urls = set()

#     # Scroll to load more thumbnails
#     # for _ in range(3):
#     #     driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
#     #     time.sleep(2)

#     # Collect thumbnails
#     thumbnails = driver.find_elements(By.CSS_SELECTOR, "h3.ob5Hkd img.YQ4gaf")
#     print(f"Found {len(thumbnails)} thumbnails")

#     for idx, thumb in enumerate(thumbnails[:num_images]):
#         try:
#             time.sleep(1)
#             thumb.click()
#             time.sleep(1)

#             # Wait for the large image to appear in the right panel
#             img = WebDriverWait(driver, 5).until(
#                 EC.presence_of_element_located((By.CSS_SELECTOR, "img.iPVvYb"))
#             )

#             src = img.get_attribute("src")
#             print(f"Thumbnail {idx} src: {src[:100]}...")  # Print first 100 chars
#             if src and re.search(r"\.(jpg|jpeg|png|gif|webp)", src, re.IGNORECASE):
#                 image_urls = src
#                 print(f"Found full image: {src[:100]}...")  # Print first 100 chars

#             if image_urls:
#                 driver.quit()
#                 break

#         except Exception as e:
#             print(f"Error on thumbnail {idx}: {e}")
#             driver.quit()
#             continue

#     driver.quit()
#     return image_urls


# Example usage
# images = scrape_google_images("ai nlp presentation workflow diagram", num_images=10)
# with open("debug_full_image_urls.txt", "w", encoding="utf-8") as f:
#     for url in images:
#         f.write(url + "\n")
#         print(url)
