import csv
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import json
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.pakwheels.com"
LISTING_PATH = "/used-cars/toyota-corolla/688?page={page}"
DEFAULT_TOTAL_PAGES = 2
DEFAULT_OUTPUT = "scraped_data_output.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}

FEATURE_COLUMNS = [
    "ABS",
    "Air Bags",
    "Air Conditioning",
    "Alloy Rims",
    "AM/FM Radio",
    "CD Player",
    "Cassette Player",
    "Cool Box",
    "Cruise Control",
    "Climate Control",
    "DVD Player",
    "Front Speakers",
    "Front Camera",
    "Heated Seats",
    "Immobilizer Key",
    "Keyless Entry",
    "Navigation System",
    "Power Locks",
    "Power Mirrors",
    "Power Steering",
    "Power Windows",
    "Rear Seat Entertainment",
    "Rear AC Vents",
    "Rear Camera",
    "Rear Speakers",
    "Sun Roof",
    "Steering Switches",
    "USB and Auxillary Cable",
]


@dataclass
class ListingDetail:
    title: str
    model_year: str
    mileage: str
    fuel_type: str
    transmission: str
    engine_capacity: str
    body_type: str
    price: str
    city: str
    features: List[str]
    url: str


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def absolute_url(path: str) -> str:
    if path.startswith("http"):
        return path
    return f"{BASE_URL}{path}"


def extract_city_from_url(url: str) -> str:
    if "-for-sale-in-" not in url:
        return "N/A"
    city_part = url.split("-for-sale-in-", 1)[-1]
    city_slug = city_part.split("-")[0]
    # Replace hyphens with spaces and capitalize words
    return " ".join(word.capitalize() for word in city_slug.split("_"))


def parse_json_ld(soup: BeautifulSoup, ad_url: str) -> Tuple[Optional[Dict], Optional[Dict]]:
    selected_product: Optional[Dict] = None
    selected_offer: Optional[Dict] = None
    for script_tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if not script_tag.string:
            continue
        try:
            json_data = json.loads(script_tag.string)
        except Exception:
            continue

        candidates = json_data if isinstance(json_data, list) else [json_data]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            offers = candidate.get("offers")
            if not offers:
                continue
            offer_list = offers if isinstance(offers, list) else [offers]
            for offer in offer_list:
                if not isinstance(offer, dict):
                    continue
                offer_url = offer.get("url") or ""
                if ad_url in offer_url:
                    selected_product = candidate
                    selected_offer = offer
                    break
            if selected_product:
                break
        if selected_product:
            break
    return selected_product, selected_offer


def parse_features(soup: BeautifulSoup) -> List[str]:
    feature_items = []
    for li_tag in soup.select("ul.car-feature-list li"):
        text = li_tag.get_text(strip=True)
        if text:
            feature_items.append(text)
    return feature_items


def parse_listing_detail(session: requests.Session, url: str) -> Optional[ListingDetail]:
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"   [ERROR] Failed to fetch detail page {url}: {exc}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    product_data, offer_data = parse_json_ld(soup, url)

    if not product_data:
        print(f"   [WARN] Could not locate JSON-LD data for {url}")
        return None

    title = product_data.get("name", "N/A")
    model_year = str(product_data.get("modelDate", "N/A"))
    mileage = product_data.get("mileageFromOdometer", "N/A")
    fuel_type = product_data.get("fuelType", "N/A")
    transmission = product_data.get("vehicleTransmission", "N/A")

    engine_capacity = "N/A"
    engine_spec = product_data.get("vehicleEngine")
    if isinstance(engine_spec, dict):
        engine_capacity = engine_spec.get("engineDisplacement", "N/A")

    body_type = product_data.get("bodyType", "N/A")

    price = "N/A"
    if offer_data:
        price_value = offer_data.get("price")
        currency = offer_data.get("priceCurrency", "")
        if price_value is not None:
            price = f"{currency} {price_value}".strip()

    city = extract_city_from_url(url)
    features = parse_features(soup)

    return ListingDetail(
        title=title,
        model_year=model_year,
        mileage=mileage,
        fuel_type=fuel_type,
        transmission=transmission,
        engine_capacity=engine_capacity,
        body_type=body_type,
        price=price,
        city=city,
        features=features,
        url=url,
    )


def collect_listing_urls(session: requests.Session, page_number: int) -> List[str]:
    page_url = absolute_url(LISTING_PATH.format(page=page_number))
    try:
        response = session.get(page_url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"[ERROR] Failed to fetch listing page {page_url}: {exc}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    for anchor in soup.select("a.car-name.ad-detail-path"):
        href = anchor.get("href")
        if not href:
            continue
        links.append(absolute_url(href))
    deduped_links = list(dict.fromkeys(links))
    print(f"[INFO] Page {page_number}: found {len(deduped_links)} listings")
    return deduped_links


def scrape_pakwheels(total_pages: int, output_csv: str) -> None:
    session = build_session()

    with open(output_csv, mode="w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        header = [
            "Make and Model",
            "Year",
            "Mileage",
            "Fuel Type",
            "Transmission",
            "Engine Capacity",
            "Body Type",
            "Price",
            "City",
            "Listing URL",
        ] + FEATURE_COLUMNS
        csv_writer.writerow(header)

        for page_number in range(1, total_pages + 1):
            page_links = collect_listing_urls(session, page_number)
            if not page_links:
                continue

            for link in page_links:
                detail = parse_listing_detail(session, link)
                if not detail:
                    continue

                row = [
                    detail.title,
                    detail.model_year,
                    detail.mileage,
                    detail.fuel_type,
                    detail.transmission,
                    detail.engine_capacity,
                    detail.body_type,
                    detail.price,
                    detail.city,
                    detail.url,
                ]

                feature_set = set(detail.features)
                for feature in FEATURE_COLUMNS:
                    row.append(1 if feature in feature_set else 0)

                csv_writer.writerow(row)
                print(f"   [OK] Scraped: {detail.title}")
                time.sleep(random.uniform(0.8, 1.6))

            time.sleep(random.uniform(1.5, 3.0))

    print(f"\n[INFO] Scraped data saved to {output_csv}")


if __name__ == "__main__":
    scrape_pakwheels(DEFAULT_TOTAL_PAGES, DEFAULT_OUTPUT)
