"""
FAQ loader and search module.
Loads FAQs from data/faq_dataset.csv and provides filtering and search capabilities.
"""

import csv
import os


FAQ_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "faq_dataset.csv")

# Domain display configuration
DOMAIN_CONFIG = {
    "College": {"icon": "🎓", "color": "#818cf8", "label": "College FAQs"},
    "HR": {"icon": "👥", "color": "#f472b6", "label": "HR Support"},
    "Customer Support": {"icon": "🛒", "color": "#34d399", "label": "Customer Support"},
    "Product": {"icon": "📦", "color": "#fb923c", "label": "Product Assistance"},
}


def load_all_faqs() -> list[dict]:
    """Load all FAQs from the CSV file."""
    faqs = []
    try:
        with open(FAQ_CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                faqs.append({
                    "domain": row["domain"].strip(),
                    "question": row["question"].strip(),
                    "answer": row["answer"].strip().replace(";", ","),
                    "keywords": [k.strip() for k in row["keywords"].split(";")],
                })
    except FileNotFoundError:
        return []
    return faqs


def get_faqs_by_domain(domain: str) -> list[dict]:
    """Get FAQs filtered by domain name."""
    all_faqs = load_all_faqs()
    return [faq for faq in all_faqs if faq["domain"] == domain]


def search_faqs(query: str, domain: str = None) -> list[dict]:
    """Search FAQs by query string. Optionally filter by domain."""
    all_faqs = load_all_faqs()
    query_lower = query.lower()
    results = []

    for faq in all_faqs:
        if domain and faq["domain"] != domain:
            continue

        # Search in question, answer, and keywords
        if (
            query_lower in faq["question"].lower()
            or query_lower in faq["answer"].lower()
            or any(query_lower in kw.lower() for kw in faq["keywords"])
        ):
            results.append(faq)

    return results


def get_all_domains() -> list[str]:
    """Get list of unique domain names."""
    return list(DOMAIN_CONFIG.keys())


def get_domain_config(domain: str) -> dict:
    """Get display configuration for a domain."""
    return DOMAIN_CONFIG.get(domain, {"icon": "💬", "color": "#94a3b8", "label": domain})
