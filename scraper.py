import requests
from bs4 import BeautifulSoup
import os
import csv
from urllib.parse import urljoin, urlparse
import re #regex import for sanitizing pdf titles

##Checks for a ROBOTS.TXT
# def check_robots_txt(url):
#     """
#     Checks for the existence of a robots.txt file on a given website and reads its content.

#     Args:
#         url (str): The URL of the website to check.

#     Returns:
#         str: The content of the robots.txt file, or None if the file doesn't exist or an error occurs.
#     """
#     try:
#         parsed_url = urlparse(url)
#         robots_url = urljoin(f"{parsed_url.scheme}://{parsed_url.netloc}", "robots.txt")
#         response = requests.get(robots_url)

#         if response.status_code == 200:
#             return response.text
#         elif response.status_code == 404:
#             print("robots.txt not found.")
#             return None
#         else:
#             print(f"Error: robots.txt request returned status code {response.status_code}")
#             return None
#     except requests.exceptions.RequestException as e:
#         print(f"An error occurred: {e}")
#         return None


# URL of the webpage
URL = "https://doughennig.com/papers.aspx"

# # Check robots.txt
# robots_content = check_robots_txt(URL)
# if robots_content:
#     print("Content of robots.txt:")
#     print(robots_content)
# else:
#     print("Could not retrieve robots.txt or robots.txt does not exist.")


# Headers to mimic a browser visit
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Step 1: Get the webpage content
response = requests.get(URL, headers=HEADERS)
soup = BeautifulSoup(response.text, "html.parser")

# Step 2: Find all articles (each inside a <div class="card">)
articles = soup.find_all("div", class_="card")

# limit = 5  # Limit for testing
# count = 0  # Counter for testing

# Create a directory to save the PDFs if it doesn't exist
if not os.path.exists("pdfs"):
    os.makedirs("pdfs")
if not os.path.exists("zip files"):
    os.makedirs("zip files")

# Open CSV file for writing
with open("scraped_articles.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Title", "Description", "Published Date", "PDF URL", "Zip URL"])  # CSV Header

    for article in articles:
        # if count >= limit:
        #     break

        # Extract title from <h5 class="card-header">
        title_element = article.find("h5", class_="card-header")
        title = title_element.get_text(strip=True) if title_element else "No Title Found"

        # Extract all paragraph texts in <div class="card-body">
        body = article.find("div", class_="card-body")
        description = body.find_all("p")[0].get_text(strip=True) if body and len(body.find_all("p")) > 0 else "No Description Available"
        published_date = body.find_all("p")[1].get_text(strip=True) if body and len(body.find_all("p")) > 1 else "No Published Date Available"

        # Extract PDF link (White Paper link)
        pdf_link = None
        white_paper_link = body.find("a", string="White Paper")  # Find the link with text 'White Paper'
        if white_paper_link and "href" in white_paper_link.attrs:
            pdf_link = white_paper_link["href"]

        # Extract Zip link (second 'a' tag)
        zip_link = None
        links = body.find_all("a")
        if len(links) > 1:  # Ensure there is a second 'a' tag for the Zip file
            zip_link = links[1]["href"]

        # Download PDF
        if pdf_link:
            # Resolve full URL to PDF file
            full_pdf_url = urljoin(URL, pdf_link)  # Adjust URL if necessary
            pdf_response = requests.get(full_pdf_url, headers=HEADERS)

            if pdf_response.status_code == 200:
                # Check the content type in the headers (optional but useful)
                content_type = pdf_response.headers.get("Content-Type", "")
                if "application/pdf" in content_type.lower():
                    # Create a filename for the PDF based on the title (sanitize it)
                    sanitized_title = re.sub(r'[\\:/*?"<>|]', "_", title)
                    pdf_filename = os.path.join("pdfs", f"{sanitized_title}.pdf")
                    
                    # Write the PDF to the file
                    with open(pdf_filename, "wb") as pdf_file:
                        pdf_file.write(pdf_response.content)
                    print(f"PDF saved as {pdf_filename}")
                else:
                    print(f"Failed to download PDF for {title}. Content-Type: {content_type}")

        # Download Zip file (only if zip_link exists)
        if zip_link:
            # Resolve full URL to Zip file
            full_zip_url = urljoin(URL, zip_link)  # Adjust URL if necessary
            zip_response = requests.get(full_zip_url, headers=HEADERS)

            if zip_response.status_code == 200:
                # Check the content type in the headers (optional but useful)
                content_type = zip_response.headers.get("Content-Type", "")
                if "application/zip" in content_type.lower() or "application/x-zip-compressed" in content_type.lower():
                    # Create a filename for the Zip based on the title (sanitize it)
                    zip_filename = os.path.join("zip files", f"{sanitized_title}.zip")
                    
                    # Write the Zip file to the file
                    with open(zip_filename, "wb") as zip_file:
                        zip_file.write(zip_response.content)
                    print(f"Zip file saved as {zip_filename}")
                else:
                    print(f"Failed to download Zip for {title}. Content-Type: {content_type}")

        
        # Write to CSV
        writer.writerow([title, description, published_date, pdf_link, zip_link])

        # count += 1  # Increment count for testing

        # Debug Output
        print(f"Title: {title}\nDescription: {description}\nPublished Date: {published_date}\nPDF URL: {pdf_link}\n{'='*80}")

print("Scraping completed. Data saved to 'scraped_articles.csv' and PDFs downloaded to 'pdfs' folder.")
