import pdfplumber

KEYWORDS = [
    "invoice",
    "invoice number",
    "receipt",
    "bill",
    "date",
    "due date",
    "total",
    "amount",
    "subtotal",
    "tax",
    "discount",
    "bank",
    "account",
    "ifsc",
    "payment",
    "terms",
    "bill to",
    "ship to",
    "supplier",
    "seller",
    "merchant",
    "issued by",
]


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> list[str]:
    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunks.append(text[start:end])

        if end >= text_length:
            break

        start = end - overlap

    return chunks


def rank_chunks(chunks: list[str]) -> list[str]:
    scored = []

    n = len(chunks)

    for i, chunk in enumerate(chunks):

        lower_chunk = chunk.lower()

        keyword_score = sum(lower_chunk.count(k) for k in KEYWORDS)

        position_score = 0
        if i == 0:
            position_score += 5
        if i == n - 1:
            position_score += 3

        total_score = keyword_score + position_score

        scored.append((total_score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [chunk for score, chunk in scored]


def extract_text_from_pdf(file):

    full_text = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)

    return "\n".join(full_text)
