from bs4 import BeautifulSoup
import json
import re

# Load HTML file
with open("publication_copy.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

publications = []
current_year = None

def clean_text(text):
    """Clean text by removing extra whitespace and newlines"""
    return re.sub(r'\s+', ' ', text).strip()

def extract_authors_safely(li, title_tag):
    """Safely extract authors from the publication item"""
    authors = []
    
    # Find the first <br> after the title
    br = title_tag.find_next("br")
    if not br:
        return authors
    
    # Get the next sibling after <br> - this should contain authors
    current = br.next_sibling
    authors_content = ""
    
    # Collect all content until we hit the next <br> or <a> tag
    while current and current.name != "br" and current.name != "a":
        if hasattr(current, 'get_text'):
            authors_content += current.get_text()
        elif isinstance(current, str):
            authors_content += current
        current = current.next_sibling
    
    # Clean the authors content
    authors_content = clean_text(authors_content)
    
    # Remove trailing <br /> if present
    authors_content = re.sub(r'<br\s*/?>\s*$', '', authors_content)
    
    if authors_content:
        # Split by comma and "and"
        # First replace " and " with ", " to normalize separators
        authors_content = re.sub(r'\s+and\s+', ', ', authors_content)
        # Split by comma
        authors = [clean_text(author) for author in authors_content.split(',') if clean_text(author)]
        # Remove any remaining HTML artifacts
        authors = [re.sub(r'<[^>]+>', '', author).strip() for author in authors if author.strip()]
    
    return authors

# Iterate through all tags
for tag in soup.select("div.col > *"):
    if tag.name == "h4":
        current_year = clean_text(tag.get_text())
    elif tag.name == "ul":
        for li in tag.select("li"):
            bold = li.find("b")
            if not bold:
                continue

            # Extract title and clean it
            title = clean_text(bold.get_text())

            # Extract authors more safely
            authors = extract_authors_safely(li, bold)

            # Extract venue - look for the first link that contains conference/journal info
            venue = None
            venue_links = li.find_all("a", href=True)
            for a in venue_links:
                link_text = clean_text(a.get_text())
                # Skip links that are clearly not venues (paper, code, bib, etc.)
                if not any(skip in link_text.lower() for skip in ['paper', 'code', 'dataset', 'bib', 'slide', 'poster', 'video', 'appendix', 'blog', 'web', 'homepage']):
                    venue = link_text
                    break

            # Extract links
            links = {"paper": None, "code": None, "bib": None, "slides": None, "video": None, "web": None, "poster": None}
            for a in li.find_all("a", href=True):
                text = clean_text(a.get_text()).lower()
                href = a["href"]
                
                if "paper" in text:
                    links["paper"] = href
                elif "code" in text or "dataset" in text:
                    links["code"] = href
                elif "bib" in text:
                    links["bib"] = href
                elif "slide" in text:
                    links["slides"] = href
                elif "video" in text:
                    links["video"] = href
                elif "web" in text or "homepage" in text:
                    links["web"] = href
                elif "poster" in text:
                    links["poster"] = href

            # Only add if we have essential information
            if title and current_year:
                publications.append({
                    "year": current_year,
                    "title": title,
                    "authors": authors,
                    "venue": venue,
                    "links": links
                })

# Save to JSON
with open("publications.json", "w", encoding="utf-8") as out:
    json.dump(publications, out, indent=2, ensure_ascii=False)

print(f"Extracted {len(publications)} publications.")