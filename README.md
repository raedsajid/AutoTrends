# PakWheels Car Scraper

A Python web scraper that extracts used car listings from PakWheels.com and saves them to a CSV file. This scraper specifically targets Toyota Corolla listings and extracts detailed information including specifications, features, pricing, and location data.

## 📋 Table of Contents

- [Overview](#overview)
- [What It Does](#what-it-does)
- [The Journey: Problems & Solutions](#the-journey-problems--solutions)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Usage](#usage)
- [Output Format](#output-format)
- [Technical Details](#technical-details)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This scraper was built to extract car listing data from PakWheels.com, one of Pakistan's largest automotive marketplaces. The project went through several iterations, starting with Selenium (which had reliability issues) and eventually settling on a lightweight `requests` + BeautifulSoup approach that leverages JSON-LD structured data.

---

## ✨ What It Does

The scraper:

1. **Visits listing pages** - Goes through multiple pages of Toyota Corolla listings
2. **Collects car URLs** - Extracts links to individual car detail pages
3. **Scrapes each listing** - Fetches detailed information from each car page
4. **Extracts data** - Pulls out specifications, features, pricing, and location
5. **Saves to CSV** - Writes all data to a structured CSV file for analysis

**Data Extracted:**
- Make and Model
- Year
- Mileage
- Fuel Type
- Transmission
- Engine Capacity
- Body Type
- Price
- City/Location
- 28 different car features (ABS, Air Bags, Air Conditioning, etc.)
- Listing URL

---

## 🚀 The Journey: Problems & Solutions

### Initial Approach: Selenium (The Problem)

**What we tried first:**
- Used Selenium WebDriver to automate a Chrome browser
- Waited for JavaScript to load content dynamically
- Attempted to handle modals and popups

**Why it failed:**
- ❌ **Slow**: Browser automation is resource-intensive
- ❌ **Unreliable**: Pages timed out, modals blocked content
- ❌ **Detection**: PakWheels could detect automated browsers
- ❌ **Empty CSV**: The scraper couldn't extract data reliably, resulting in empty files

**The specific issues:**
1. Safety modal appeared on every page, blocking content
2. JavaScript-heavy pages took too long to load
3. CSS selectors didn't match because content loaded dynamically
4. Timeouts occurred frequently

### Final Solution: Requests + JSON-LD (The Success)

**What we use now:**
- `requests` library for HTTP calls (lightweight, fast)
- BeautifulSoup for HTML parsing
- JSON-LD structured data extraction (embedded in HTML)

**Why it works:**
- ✅ **Fast**: Direct HTTP requests, no browser overhead
- ✅ **Reliable**: Structured data is always present in HTML
- ✅ **Simple**: Fewer dependencies, less code
- ✅ **Effective**: Successfully extracts all required data

**The key insight:**
PakWheels embeds structured data (JSON-LD) in their HTML for search engines. We can parse this directly without needing JavaScript execution!

---

## 🔧 How It Works

### High-Level Flow

```
1. Start
   ↓
2. Create HTTP session (pretend to be a browser)
   ↓
3. Visit listing page: "pakwheels.com/used-cars/toyota-corolla/688?page=1"
   ↓
4. Parse HTML to find all car detail page links (e.g., 33 links)
   ↓
5. For each car link:
   ├─ Fetch the car detail page HTML
   ├─ Extract JSON-LD structured data (car specs)
   ├─ Extract features from HTML
   ├─ Extract city from URL
   └─ Write row to CSV
   ↓
6. Move to next page
   ↓
7. Repeat until all pages processed
   ↓
8. Done! CSV file ready
```

### Detailed Process

#### Step 1: Setup (Lines 12-57)
```python
BASE_URL = "https://www.pakwheels.com"
LISTING_PATH = "/used-cars/toyota-corolla/688?page={page}"
```
- Defines the base URL and listing path template
- Sets up browser-like headers to avoid detection
- Lists all car features we want to track

#### Step 2: Create Session (Lines 75-78)
```python
def build_session():
    session = requests.Session()
    session.headers.update(HEADERS)  # Pretend to be Chrome browser
    return session
```
- Creates a reusable HTTP session
- Adds headers that make requests look like a real browser

#### Step 3: Collect Car URLs (Lines 192-210)
```python
def collect_listing_urls(session, page_number):
    # 1. Build URL: "pakwheels.com/used-cars/toyota-corolla/688?page=1"
    page_url = absolute_url(LISTING_PATH.format(page=page_number))
    
    # 2. Fetch HTML
    response = session.get(page_url)
    
    # 3. Parse HTML
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 4. Find all car links using CSS selector
    links = []
    for anchor in soup.select("a.car-name.ad-detail-path"):
        links.append(absolute_url(anchor.get("href")))
    
    return links
```
- Fetches the listing page HTML
- Uses CSS selector `"a.car-name.ad-detail-path"` to find all car links
- Returns a list of URLs to scrape

#### Step 4: Extract Data from Each Car Page (Lines 139-189)

**4a. Fetch the Page**
```python
response = session.get(car_url)
soup = BeautifulSoup(response.text, "html.parser")
```

**4b. Extract JSON-LD Data (Lines 96-127)**

PakWheels embeds structured data in `<script type="application/ld+json">` tags. Example:

```json
{
  "@type": "Product",
  "name": "Toyota Corolla 2016",
  "modelDate": 2016,
  "fuelType": "Petrol",
  "vehicleTransmission": "Manual",
  "mileageFromOdometer": "82,000 km",
  "vehicleEngine": {
    "engineDisplacement": "1300cc"
  },
  "bodyType": "Sedan",
  "offers": {
    "price": 3375000,
    "priceCurrency": "PKR"
  }
}
```

The function:
1. Finds all `<script type="application/ld+json">` tags
2. Parses the JSON data
3. Matches the product data for the current URL
4. Extracts: year, mileage, fuel type, transmission, engine, body type, price

**4c. Extract Features (Lines 130-136)**
```python
def parse_features(soup):
    features = []
    for li_tag in soup.select("ul.car-feature-list li"):
        features.append(li_tag.get_text(strip=True))
    return features
```
- Finds the feature list in HTML using CSS selector
- Extracts text from each feature item

**4d. Extract City from URL (Lines 87-93)**
```python
# URL: "toyota-corolla-2016-for-sale-in-karachi-10802484"
# Extracts "karachi" and formats as "Karachi"
```
- Parses the city name from the URL pattern

#### Step 5: Write to CSV (Lines 213-265)
```python
for page_number in range(1, total_pages + 1):
    car_urls = collect_listing_urls(session, page_number)
    
    for car_url in car_urls:
        detail = parse_listing_detail(session, car_url)
        
        # Build row with basic info
        row = [detail.title, detail.model_year, detail.mileage, ...]
        
        # Add feature flags (1 = has feature, 0 = doesn't)
        for feature in FEATURE_COLUMNS:
            row.append(1 if feature in detail.features else 0)
        
        csv_writer.writerow(row)
        
        # Be polite - wait between requests
        time.sleep(random.uniform(0.8, 1.6))
```

---

## 📦 Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Install Dependencies

```bash
pip install requests beautifulsoup4
```

Or install from requirements file (if you create one):

```bash
pip install -r requirements.txt
```

### Required Packages

- `requests` - For making HTTP requests
- `beautifulsoup4` - For parsing HTML
- `csv` - Built-in Python module (no installation needed)
- `json` - Built-in Python module (no installation needed)

---

## 💻 Usage

### Basic Usage

1. **Run the scraper:**
   ```bash
   python scrape_pakwheels.py
   ```

2. **Wait for completion:**
   - The script will print progress messages
   - It processes pages sequentially
   - Each car listing is logged as it's scraped

3. **Check the output:**
   - Data is saved to `scraped_data_output.csv`
   - Open in Excel, Google Sheets, or any CSV viewer

### Customization

You can modify the script to:

**Change number of pages:**
```python
# In scrape_pakwheels.py, line 14
DEFAULT_TOTAL_PAGES = 5  # Change from 2 to 5
```

**Change output filename:**
```python
# In scrape_pakwheels.py, line 15
DEFAULT_OUTPUT = "my_custom_filename.csv"
```

**Change car model:**
```python
# In scrape_pakwheels.py, line 13
LISTING_PATH = "/used-cars/honda-civic/XXX?page={page}"  # Change model
```

**Adjust delays:**
```python
# In scrape_pakwheels.py, line 261
time.sleep(random.uniform(0.8, 1.6))  # Adjust wait time between requests
```

---

## 📊 Output Format

The CSV file contains the following columns:

### Basic Information
1. **Make and Model** - Full car name (e.g., "Toyota Corolla 2016 for sale in Karachi")
2. **Year** - Model year (e.g., "2016")
3. **Mileage** - Kilometers driven (e.g., "82,000 km")
4. **Fuel Type** - Type of fuel (e.g., "Petrol", "Diesel")
5. **Transmission** - Transmission type (e.g., "Manual", "Automatic")
6. **Engine Capacity** - Engine size (e.g., "1300cc", "1800cc")
7. **Body Type** - Car body style (e.g., "Sedan")
8. **Price** - Price with currency (e.g., "PKR 3375000")
9. **City** - Location (e.g., "Karachi", "Lahore")
10. **Listing URL** - Direct link to the listing

### Feature Flags (28 features)
Each feature column contains:
- `1` = Car has this feature
- `0` = Car doesn't have this feature

Features tracked:
- ABS
- Air Bags
- Air Conditioning
- Alloy Rims
- AM/FM Radio
- CD Player
- Cassette Player
- Cool Box
- Cruise Control
- Climate Control
- DVD Player
- Front Speakers
- Front Camera
- Heated Seats
- Immobilizer Key
- Keyless Entry
- Navigation System
- Power Locks
- Power Mirrors
- Power Steering
- Power Windows
- Rear Seat Entertainment
- Rear AC Vents
- Rear Camera
- Rear Speakers
- Sun Roof
- Steering Switches
- USB and Auxillary Cable

### Example Row

```csv
Toyota Corolla 2016 for sale in Karachi,2016,"82,000 km",Petrol,Manual,1300cc,Sedan,"PKR 3375000",Karachi,https://www.pakwheels.com/used-cars/toyota-corolla-2016-for-sale-in-karachi-10802484,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1,1,1,0,0,0,0,0,0,0,0
```

---

## 🔍 Technical Details

### Why JSON-LD?

**JSON-LD (JavaScript Object Notation for Linked Data)** is a method of encoding structured data that websites embed in their HTML for search engines. It's part of Schema.org vocabulary.

**Benefits:**
- Always present in HTML (doesn't require JavaScript)
- Structured and consistent format
- Contains all key information in one place
- Easy to parse programmatically

### CSS Selectors Used

- `"a.car-name.ad-detail-path"` - Finds car listing links
- `"ul.car-feature-list li"` - Finds feature list items
- `"script[type='application/ld+json']"` - Finds JSON-LD data

### HTTP Headers

The scraper uses browser-like headers to avoid detection:

```python
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,...",
    "Referer": "https://www.google.com/",
}
```

### Rate Limiting

The scraper includes delays between requests:
- 0.8-1.6 seconds between individual car pages
- 1.5-3.0 seconds between listing pages

This prevents overwhelming the server and reduces the risk of being blocked.

---

## 🐛 Troubleshooting

### Problem: CSV file is empty

**Possible causes:**
1. No internet connection
2. PakWheels website structure changed
3. JSON-LD data format changed

**Solutions:**
- Check internet connection
- Verify the website is accessible
- Check if CSS selectors still work (inspect page source)
- Look for error messages in console output

### Problem: "Module not found" error

**Solution:**
```bash
pip install requests beautifulsoup4
```

### Problem: Timeout errors

**Solution:**
- Check internet connection
- Increase timeout value in code (line 141, 195)
- PakWheels might be slow - wait and retry

### Problem: Some listings show "N/A"

**Possible causes:**
1. Listing page doesn't have JSON-LD data
2. Data format is different for that listing
3. Missing information on the original page

**Solution:**
- This is normal - some listings may have incomplete data
- The scraper will still save the row with available information

### Problem: Getting blocked

**Symptoms:**
- 403 Forbidden errors
- Empty responses
- Connection refused

**Solutions:**
- Increase delays between requests
- Wait before retrying
- Check if PakWheels has updated their anti-scraping measures

---

## 📝 Code Structure

```
scrape_pakwheels.py
├── Constants (BASE_URL, HEADERS, FEATURE_COLUMNS)
├── ListingDetail dataclass (data structure)
├── build_session() - Creates HTTP session
├── absolute_url() - Converts relative to absolute URLs
├── extract_city_from_url() - Parses city from URL
├── parse_json_ld() - Extracts structured data
├── parse_features() - Extracts feature list
├── parse_listing_detail() - Main extraction function
├── collect_listing_urls() - Gets all car URLs from a page
└── scrape_pakwheels() - Main orchestration function
```

---

## ⚠️ Important Notes

### Legal & Ethical Considerations

- **Respect robots.txt**: Check PakWheels' robots.txt file
- **Rate Limiting**: The scraper includes delays to be respectful
- **Terms of Service**: Review PakWheels' terms before scraping
- **Personal Use**: This is for educational/personal use only
- **Don't Overload**: Don't scrape too aggressively

### Data Accuracy

- Data is extracted as-is from PakWheels
- Some listings may have incomplete information
- Prices and availability may change
- Always verify critical information

### Maintenance

- Websites change their structure over time
- CSS selectors may need updates
- JSON-LD format might change
- Regular testing recommended

---

## 🎓 Learning Resources

### Key Concepts Used

1. **Web Scraping**: Extracting data from websites
2. **HTTP Requests**: Communicating with web servers
3. **HTML Parsing**: Extracting data from HTML documents
4. **JSON-LD**: Structured data format
5. **CSS Selectors**: Finding elements in HTML
6. **CSV Writing**: Saving data in structured format

### Recommended Reading

- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests Library Documentation](https://requests.readthedocs.io/)
- [JSON-LD Specification](https://json-ld.org/)
- [Web Scraping Best Practices](https://www.scrapehero.com/web-scraping-best-practices/)

---

## 📄 License

This project is for educational purposes. Use responsibly and in accordance with PakWheels' terms of service.

---

## 🤝 Contributing

If you find issues or want to improve the scraper:

1. Test your changes thoroughly
2. Update this README if needed
3. Add comments to explain complex logic
4. Maintain the same code style

---

## 📧 Support

If you encounter issues:

1. Check the Troubleshooting section
2. Review error messages carefully
3. Verify the website structure hasn't changed
4. Test with a single page first

---


