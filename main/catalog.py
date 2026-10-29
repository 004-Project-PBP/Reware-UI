"""Catalog data shared by the landing page and account pages, until items get their own model."""

# image: optional, file under static/img/
ITEMS = [
    {"name": "Kemeja linen oversize", "brand": "Uniqlo", "price": "Rp85.000", "discount": 70,
     "image": "KemejaLinenOversize.png"},
    {"name": "Kaos boxy heavyweight", "brand": "H&M", "price": "Rp45.000", "discount": 62,
     "image": "kaosboxyheavyweight.png"},
    {"name": "Blouse satin krem", "brand": "Zara", "price": "Rp120.000", "discount": 58,
     "image": "blousesatinkrem.jpg"},
    {"name": "Polo rajut vintage", "brand": "Lacoste", "price": "Rp210.000", "discount": 65,
     "image": "sweaterpolorajut.png"},
    {"name": "Item 5", "brand": "Price 5", "price": "Rp210.000", "discount": 67},
    {"name": "Item 6", "brand": "Item 6", "price": "Rp210.000", "discount": 76},
]

# file under static/img/brands/, display size from the design
BRANDS = [
    {"name": "Levi's", "file": "levis.png", "width": 99, "height": 48},
    {"name": "Zara", "file": "zara.png", "width": 106, "height": 45},
    {"name": "Uniqlo", "file": "uniqlo.png", "width": 107, "height": 60},
    {"name": "Erigo", "file": "erigo.png", "width": 155, "height": 26},
    {"name": "H&M", "file": "hm.png", "width": 62, "height": 62},
    {"name": "Lacoste", "file": "lacoste.png", "width": 92, "height": 92},
    {"name": "Colorbox", "file": "colorbox.png", "width": 104, "height": 104},
    {"name": "et cetera", "file": "etcetera.png", "width": 92, "height": 81},
    {"name": "Urban&Co", "file": "urbanco.png", "width": 122, "height": 122},
]


def items_for_brands(brand_names):
    return [item for item in ITEMS if item["brand"] in brand_names]
