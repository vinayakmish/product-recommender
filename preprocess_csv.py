"""
Preprocess train.csv → data.sql
================================
Reads the large train.csv, samples ~250 diverse products,
categorizes them by keyword analysis of titles,
and generates a Spring Boot data.sql seed file with
products, users, and synthetic transactions.
"""

import csv
import random
import re
import html
import itertools
from collections import defaultdict

# ── Configuration ──────────────────────────────────────────────────────
CSV_PATH = "train.csv"
OUTPUT_SQL = "backend/src/main/resources/data.sql"
SAMPLE_SIZE = 250          # total products to keep
MAX_ROWS_SCAN = 200_000    # how many CSV rows to scan (not all 1.6GB)
MIN_TITLE_LEN = 15         # skip very short titles
MAX_TITLE_LEN = 120        # truncate very long titles
NUM_TRANSACTIONS = 60      # synthetic transactions to generate
NUM_USERS = 8

# ── Category keyword mapping ─────────────────────────────────────────
# Order matters: first match wins
CATEGORY_RULES = [
    ("Electronics", [
        "headphone", "earphone", "earbud", "speaker", "bluetooth", "usb",
        "charger", "cable", "adapter", "power bank", "battery", "led light",
        "projector", "microphone", "amplifier", "smart watch", "smartwatch",
        "tablet", "phone", "mobile", "laptop", "keyboard", "mouse pad",
        "webcam", "camera", "drone", "monitor", "television", "tv ",
        "remote control", "hdmi", "memory card", "pendrive", "flash drive",
        "router", "wifi", "wireless", "sensor", "arduino", "raspberry",
        "electric", "electronic", "digital", "smart home", "alexa",
    ]),
    ("Books", [
        "book", "novel", "paperback", "hardcover", "edition", "memoir",
        "autobiography", "biography", "guide to", "handbook", "textbook",
        "encyclopedia", "dictionary", "atlas", "journal", "diary",
        "beginners", "cookbook", "recipe book", "coloring book",
        "workbook", " stories", "tale", " poems", "chronicles",
        " vol ", "volume ", "chapter",
    ]),
    ("Clothing", [
        "t-shirt", "tshirt", "shirt", "jeans", "pants", "trouser",
        "jacket", "hoodie", "sweater", "dress", "skirt", "legging",
        "shorts", "underwear", "bra ", "socks", "cotton", "polyester",
        "denim", "kurta", "kurti", "saree", "sari", "salwar",
        "pyjama", "pajama", "nightwear", "sleepwear", "blazer",
        "coat ", "cardigan", "vest ", "blouse", "top ", "wear",
        "apparel", "garment", "men's ", "women's ", "boy's", "girl's",
    ]),
    ("Shoes & Footwear", [
        "shoe", "sneaker", "sandal", "slipper", "boot", "loafer",
        "heel", "flat", "footwear", "flip flop", "crocs", "moccasin",
        "oxford", "derby", "trainer",
    ]),
    ("Home & Kitchen", [
        "curtain", "pillow", "cushion", "bedsheet", "blanket", "towel",
        "mat ", "rug ", "carpet", "vase", "candle", "lamp", "light ",
        "decor", "decoration", "wall art", "frame", "mirror",
        "kitchen", "utensil", "cookware", "pan ", "pot ", "kettle",
        "bottle", "container", "storage", "organizer", "shelf",
        "hanger", "hook", "basket", "bin ", "trash", "mop", "broom",
        "vacuum", "iron ", "blender", "mixer", "toaster", "oven",
        "plate", "bowl", "cup ", "mug ", "glass ", "cutlery",
        "spoon", "fork", "knife ", "chopping", "cutting board",
        "tablecloth", "napkin", "coaster", "plant pot", "planter",
        "garden", "flower", "wallpaper", "sticker", "furniture",
        "table", "chair", "sofa", "bed ", "mattress", "shower",
        "bathroom", "soap dispenser", " home ",
    ]),
    ("Beauty & Personal Care", [
        "serum", "cream", "lotion", "moistur", "sunscreen", "face wash",
        "shampoo", "conditioner", "hair oil", "hair color", "perfume",
        "fragrance", "deodorant", "lip ", "lipstick", "mascara",
        "foundation", "concealer", "eyeshadow", "eyeliner", "nail",
        "makeup", "cosmetic", "beauty", "skincare", "skin care",
        "facial", "body wash", "soap", "essential oil", "aroma",
        "diffuser", "grooming", "trimmer", "razor", "shaver",
        "toothbrush", "toothpaste", "mouthwash", "comb", "brush",
    ]),
    ("Sports & Fitness", [
        "yoga", "gym", "fitness", "exercise", "workout", "sport",
        "running", "cycling", "swimming", "football", "cricket",
        "basketball", "tennis", "badminton", "dumbbell", "weight",
        "resistance band", "jump rope", "treadmill", "bicycle",
        "helmet", "gloves", "knee pad", "elbow pad", "water bottle",
        "shaker", "protein", "supplement", "camping", "hiking",
        "trekking", "backpack", "sleeping bag", "tent ", "fishing",
        "ball ", "bat ", "racket", "goggles", "cap ",
    ]),
    ("Toys & Games", [
        "toy ", "toys", "game ", "games", "puzzle", "lego", "doll",
        "action figure", "board game", "card game", "nerf", "playset",
        "stuffed", "plush", "teddy", "building block", "remote car",
        "rc car",
    ]),
    ("Office & Stationery", [
        "pen ", "pencil", "notebook", "notepad", "sticky note",
        "stapler", "paper", "folder", "file ", "binder", "marker",
        "highlighter", "eraser", "sharpener", "ruler", "calculator",
        "whiteboard", "blackboard", "desk ", "office", "stationery",
        "tape ", "glue ", "scissor", "envelope", "stamp",
        "laptop stand", "monitor stand", "desk lamp",
    ]),
    ("Automotive", [
        "car ", "vehicle", "automotive", "motor", "engine",
        "tire", "tyre", "steering", "dashboard", "seat cover",
        "horn", "bike ", "motorcycle", "scooter", "bicycle",
        "gps ", "navigation",
    ]),
    ("Pet Supplies", [
        "pet ", "dog ", "cat ", "puppy", "kitten", "fish tank",
        "aquarium", "bird ", "parrot", "hamster", "rabbit",
        "leash", "collar", "pet food", "dog food", "cat food",
        "pet toy", "litter", "grooming",
    ]),
    ("Grocery & Food", [
        "tea ", "coffee", "chocolate", "honey", "spice", "masala",
        "snack", "biscuit", "cookie", "chips", "nuts ", "almond",
        "cashew", "organic", "oil ", "ghee", "sugar", "salt",
        "rice ", "flour", "pasta", "noodle", "sauce", "jam",
        "pickle", "juice", "drink", " food", "protein bar",
    ]),
    ("Health & Wellness", [
        "vitamin", "supplement", "medicine", "health", "medical",
        "thermometer", "oximeter", "mask ", "sanitizer", "first aid",
        "bandage", "blood pressure", "wellness", "immunity", "ayurved",
        "herbal",
    ]),
    ("Bags & Luggage", [
        "bag ", "bags", "backpack", "luggage", "suitcase", "wallet",
        "purse", "handbag", "clutch", "pouch", "tote ",
        "travel bag", "laptop bag", "school bag", "messenger",
    ]),
    ("Jewelry & Watches", [
        "ring ", "earring", "necklace", "bracelet", "bangle",
        "pendant", "chain", "jewel", "gold ", "silver ", "diamond",
        "watch ", "watches", "wristwatch", "analog", "chronograph",
    ]),
    ("Musical Instruments", [
        "guitar", "piano", "keyboard", "drum", "violin", "flute",
        "harmonica", "ukulele", "microphone", "capo", "tuner",
        "music", "instrument", "amplifier",
    ]),
]


def categorize(title: str) -> str:
    """Assign a category based on keywords in the product title."""
    title_lower = title.lower()
    for category, keywords in CATEGORY_RULES:
        for kw in keywords:
            if kw in title_lower:
                return category
    return "General"


def clean_title(raw: str) -> str:
    """Clean and truncate product title."""
    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", "", raw)
    # Decode HTML entities
    cleaned = html.unescape(cleaned)
    # Remove non-printable characters
    cleaned = re.sub(r"[^\x20-\x7E]", "", cleaned)
    # Collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Truncate
    if len(cleaned) > MAX_TITLE_LEN:
        cleaned = cleaned[: MAX_TITLE_LEN - 1].rsplit(" ", 1)[0] + "…"
    return cleaned


def clean_description(bullet_points: str, description: str) -> str:
    """Extract a clean description from bullet points or HTML description."""
    # Prefer bullet points as they're cleaner
    text = bullet_points or description or ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    # Remove non-printable
    text = re.sub(r"[^\x20-\x7E.,;:!?'\"-]", " ", text)
    # Clean up brackets from bullet point arrays
    text = text.strip("[]")
    # Split by comma and take first 2-3 bullet points
    parts = [p.strip() for p in text.split(",") if len(p.strip()) > 10]
    desc = ". ".join(parts[:3])
    if len(desc) > 500:
        desc = desc[:497] + "..."
    return desc


def price_from_length(length_str: str) -> float:
    """Convert PRODUCT_LENGTH to a reasonable USD price."""
    try:
        val = float(length_str)
        # The PRODUCT_LENGTH values seem to be in some unit
        # Typical range: 100-2000+, so let's scale to reasonable USD prices  
        # Map roughly to $5 - $200 range
        price = max(4.99, min(val / 10.0, 299.99))
        return round(price, 2)
    except (ValueError, TypeError):
        return round(random.uniform(9.99, 49.99), 2)


def escape_sql(s: str) -> str:
    """Escape single quotes for SQL insertion."""
    return s.replace("'", "''")


def main():
    print(f"📖 Reading {CSV_PATH} (scanning up to {MAX_ROWS_SCAN:,} rows)...")

    # Read and sample products
    raw_products = []
    category_buckets = defaultdict(list)

    with open(CSV_PATH, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader)
        print(f"   Columns: {header}")

        for i, row in enumerate(reader):
            if i >= MAX_ROWS_SCAN:
                break

            if len(row) < 6:
                continue

            product_id, title, bullet_points, description, type_id, product_length = row[:6]

            if not title or len(title.strip()) < MIN_TITLE_LEN:
                continue

            clean = clean_title(title)
            if len(clean) < MIN_TITLE_LEN:
                continue

            cat = categorize(clean)
            desc = clean_description(bullet_points, description)
            price = price_from_length(product_length)

            product = {
                "id": int(product_id),
                "name": clean,
                "category": cat,
                "price": price,
                "description": desc,
                "type_id": type_id,
            }

            category_buckets[cat].append(product)

        print(f"   Scanned {i+1:,} rows")

    # Sample evenly across categories
    print(f"\n📊 Category distribution (before sampling):")
    for cat in sorted(category_buckets.keys()):
        print(f"   {cat}: {len(category_buckets[cat]):,} products")

    sampled = []
    cats = sorted(category_buckets.keys())
    # Exclude "General" from primary sampling if we have enough specific categories
    specific_cats = [c for c in cats if c != "General"]
    if len(specific_cats) >= 8:
        per_cat = max(10, SAMPLE_SIZE // len(specific_cats))
        for cat in specific_cats:
            items = category_buckets[cat]
            n = min(per_cat, len(items))
            sampled.extend(random.sample(items, n))
        # Fill remaining with General if needed
        remaining = SAMPLE_SIZE - len(sampled)
        if remaining > 0 and category_buckets.get("General"):
            gen = category_buckets["General"]
            sampled.extend(random.sample(gen, min(remaining, len(gen))))
    else:
        per_cat = max(5, SAMPLE_SIZE // len(cats))
        for cat in cats:
            items = category_buckets[cat]
            n = min(per_cat, len(items))
            sampled.extend(random.sample(items, n))

    # Trim to exact sample size
    if len(sampled) > SAMPLE_SIZE:
        sampled = random.sample(sampled, SAMPLE_SIZE)

    # Re-assign sequential IDs for cleanliness
    random.shuffle(sampled)
    for idx, p in enumerate(sampled, start=1):
        p["new_id"] = idx

    print(f"\n✅ Sampled {len(sampled)} products:")
    cat_counts = defaultdict(int)
    for p in sampled:
        cat_counts[p["category"]] += 1
    for cat in sorted(cat_counts):
        print(f"   {cat}: {cat_counts[cat]}")

    # ── Generate SQL ──────────────────────────────────────────────────
    lines = []
    lines.append("-- =============================================================")
    lines.append("-- Auto-generated from train.csv")
    lines.append(f"-- {len(sampled)} products sampled across {len(cat_counts)} categories")
    lines.append("-- =============================================================\n")

    # Products
    lines.append("-- Products")
    for p in sampled:
        name = escape_sql(p["name"])
        cat = escape_sql(p["category"])
        desc = escape_sql(p["description"])[:500] if p["description"] else ""
        lines.append(
            f"MERGE INTO products (id, name, category, price, description, image_url) KEY(id) VALUES "
            f"({p['new_id']}, '{name}', '{cat}', {p['price']}, "
            f"'{desc}', NULL);"
        )

    lines.append("")

    # Users
    lines.append("-- Users")
    user_names = ["alice", "bob", "charlie", "diana", "eve", "frank", "grace", "henry"]
    for uid, uname in enumerate(user_names, 1):
        lines.append(f"MERGE INTO users (id, username, email) KEY(id) VALUES ({uid}, '{uname}', '{uname}@example.com');")

    lines.append("")

    # Synthetic transactions
    lines.append("-- Transactions")
    # Group products by category for realistic co-purchase patterns
    cat_products = defaultdict(list)
    for p in sampled:
        cat_products[p["category"]].append(p["new_id"])

    transactions = []
    for tid in range(1, NUM_TRANSACTIONS + 1):
        uid = random.randint(1, NUM_USERS)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        hour = random.randint(8, 20)
        lines.append(
            f"MERGE INTO transactions (id, user_id, created_at) KEY(id) VALUES "
            f"({tid}, {uid}, '2025-{month:02d}-{day:02d} {hour:02d}:00:00');"
        )

        # Pick 2-4 products, mostly from same category (realistic)
        primary_cat = random.choice(list(cat_products.keys()))
        n_items = random.randint(2, 4)
        items = []

        # 70% chance items are from same category
        same_cat_items = cat_products[primary_cat]
        n_same = min(max(1, int(n_items * 0.7)), len(same_cat_items))
        items.extend(random.sample(same_cat_items, n_same))

        # Fill rest from random categories (cross-category purchases)
        remaining = n_items - len(items)
        if remaining > 0:
            other_cats = [c for c in cat_products if c != primary_cat and cat_products[c]]
            if other_cats:
                cross_cat = random.choice(other_cats)
                cross_items = [pid for pid in cat_products[cross_cat] if pid not in items]
                items.extend(random.sample(cross_items, min(remaining, len(cross_items))))

        transactions.append(items)

    lines.append("")
    lines.append("-- Transaction Items")
    lines.append("DELETE FROM transaction_items;")
    lines.append("")

    for tid, items in enumerate(transactions, 1):
        for pid in items:
            lines.append(f"INSERT INTO transaction_items (transaction_id, product_id) VALUES ({tid}, {pid});")

    lines.append("")

    # Write SQL file
    sql_content = "\n".join(lines)
    with open(OUTPUT_SQL, "w", encoding="utf-8") as f:
        f.write(sql_content)

    print(f"\n💾 Generated {OUTPUT_SQL}")
    print(f"   {len(sampled)} products, {NUM_USERS} users, {len(transactions)} transactions")
    print(f"   SQL file size: {len(sql_content):,} bytes")
    print("\n🎉 Done! Restart your Spring Boot backend to load the new data.")


if __name__ == "__main__":
    random.seed(42)  # reproducible sampling
    main()
