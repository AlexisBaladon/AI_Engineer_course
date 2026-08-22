"""Crawl Nau64 and build the CSV document database used by NauAI.

The script replaces the ingestion notebook with a repeatable command-line
pipeline. It preserves the CSV schema consumed by both deployment modes:

* ``ingestion/`` is read by the monolithic EC2 ``app.py`` service.
* ``retrieval/data/`` is read by the microservice retrieval service.

Example:
    python ingestion/run_ingestion.py --max-pages 10
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import random
import re
import shutil
import sys
import tempfile
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

LOGGER = logging.getLogger("nauai.ingestion")
ROOT_DIR = Path(__file__).resolve().parent.parent
INGESTION_DIR = ROOT_DIR / "ingestion"
RETRIEVAL_DATA_DIR = ROOT_DIR / "retrieval" / "data"

USER_AGENT = (
    "Mozilla/5.0 (compatible; NauAIKnowledgeBaseUpdater/1.0; "
    "+https://nau64.com)"
)
EMBEDDING_MODEL = "text-embedding-3-large"


@dataclass(frozen=True)
class PipelinePaths:
    crawled: Path
    cleaned: Path
    chunked: Path
    ingestion_embeddings: Path
    ingestion_images: Path
    retrieval_embeddings: Path
    retrieval_images: Path


def get_paths() -> PipelinePaths:
    return PipelinePaths(
        crawled=INGESTION_DIR / "crawled_data.csv",
        cleaned=INGESTION_DIR / "cleaned_crawled_data.csv",
        chunked=INGESTION_DIR / "chunked_data.csv",
        ingestion_embeddings=INGESTION_DIR / "embedded_chunked_data.csv",
        ingestion_images=INGESTION_DIR / "website_images.csv",
        retrieval_embeddings=RETRIEVAL_DATA_DIR / "embedded_chunked_data.csv",
        retrieval_images=RETRIEVAL_DATA_DIR / "website_images.csv",
    )


def normalize_url(url: str) -> str:
    """Normalize a crawl URL by removing its fragment and trailing whitespace."""
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))


def configure_csv_field_size_limit() -> None:
    """Allow raw HTML fields larger than Python's conservative CSV default."""
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            LOGGER.debug("CSV field size limit set to %s bytes.", limit)
            return
        except OverflowError:
            # Some platforms cannot pass sys.maxsize to the C CSV parser.
            limit //= 10


def is_paginated_archive(url: str) -> bool:
    """Return whether a URL is a WordPress-style archive page (``/page/<n>/``)."""
    return bool(re.fullmatch(r"/page/\d+/?", urlsplit(normalize_url(url)).path))


def create_http_session():
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    return session


def crawl_site(
    start_url: str,
    max_depth: int,
    max_pages: int,
    max_urls: int,
    min_delay: float,
    max_delay: float,
    timeout: float,
) -> dict[str, str]:
    """Crawl the root site and WordPress-style paginated archive pages."""
    start_url = normalize_url(start_url)
    root_domain = urlsplit(start_url).netloc
    pages: dict[str, str] = {}
    session = create_http_session()
    import requests
    from bs4 import BeautifulSoup

    def visit(url: str, depth: int, force: bool = False, allow_archive: bool = False) -> None:
        url = normalize_url(url)
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or parsed.netloc != root_domain:
            return
        if is_paginated_archive(url) and not allow_archive:
            LOGGER.debug("Deferring paginated archive to the pagination pass: %s", url)
            return
        if not force and url in pages:
            return
        if len(pages) >= max_urls and url not in pages:
            LOGGER.warning("Reached --max-urls=%s; skipping remaining links.", max_urls)
            return

        if max_delay > 0:
            time.sleep(random.uniform(min_delay, max_delay))

        try:
            LOGGER.info("Crawling depth %s: %s", depth, url)
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            LOGGER.warning("Could not crawl %s: %s", url, exc)
            return

        pages[url] = response.text
        if depth >= max_depth:
            return

        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True):
            visit(urljoin(url, link["href"]), depth + 1)

    visit(start_url, depth=0)
    for page_number in range(1, max_pages + 1):
        visit(
            urljoin(start_url, f"/page/{page_number}/"),
            depth=0,
            force=True,
            allow_archive=True,
        )

    return pages


def write_crawled_pages(pages: dict[str, str], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=("url", "raw_text"))
        writer.writeheader()
        for url, html in sorted(pages.items()):
            writer.writerow({"url": url, "raw_text": html})


def extract_main_text(html: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main")
    if main is None:
        return ""
    text = main.get_text()
    text = re.sub(r"\n*\s*(?=\[Event )", "\n\n", text)
    return text.replace("«", "").replace("»", "")


def clean_pages(input_path: Path, output_path: Path) -> int:
    seen_urls: set[str] = set()
    count = 0
    with (
        input_path.open("r", newline="", encoding="utf-8") as input_file,
        output_path.open("w", newline="", encoding="utf-8") as output_file,
    ):
        reader = csv.DictReader(input_file)
        writer = csv.DictWriter(
            output_file,
            fieldnames=("url", "raw_text", "cleaned_html"),
        )
        writer.writeheader()
        for row in reader:
            url = normalize_url(row["url"])
            if url in seen_urls:
                continue
            seen_urls.add(url)
            writer.writerow(
                {
                    "url": url,
                    "raw_text": row["raw_text"],
                    "cleaned_html": extract_main_text(row["raw_text"]),
                }
            )
            count += 1
    return count


def extract_images(input_path: Path, output_path: Path) -> int:
    from bs4 import BeautifulSoup

    count = 0
    with (
        input_path.open("r", newline="", encoding="utf-8") as input_file,
        output_path.open("w", newline="", encoding="utf-8") as output_file,
    ):
        reader = csv.DictReader(input_file)
        writer = csv.DictWriter(output_file, fieldnames=("page_url", "image_url", "alt"))
        writer.writeheader()
        for row in reader:
            main = BeautifulSoup(row["raw_text"], "html.parser").find("main")
            if main is None:
                continue
            for image in main.find_all("img"):
                source = image.get("src")
                if source:
                    writer.writerow(
                        {
                            "page_url": row["url"],
                            "image_url": urljoin(row["url"], source),
                            "alt": image.get("alt", ""),
                        }
                    )
                    count += 1
    return count


def create_chunks(input_path: Path, output_path: Path, breakpoint_percentile: int) -> int:
    """Create the same semantic chunks used by the original notebook."""
    from llama_index.core.node_parser import SemanticSplitterNodeParser
    from llama_index.core.schema import Document
    from llama_index.embeddings.openai import OpenAIEmbedding

    splitter = SemanticSplitterNodeParser(
        embed_model=OpenAIEmbedding(model=EMBEDDING_MODEL),
        breakpoint_percentile_threshold=breakpoint_percentile,
    )
    count = 0
    with (
        input_path.open("r", newline="", encoding="utf-8") as input_file,
        output_path.open("w", newline="", encoding="utf-8") as output_file,
    ):
        reader = csv.DictReader(input_file)
        writer = csv.DictWriter(output_file, fieldnames=("url", "chunk_id", "chunk_text"))
        writer.writeheader()
        for row in reader:
            text = row["cleaned_html"].strip()
            if not text:
                continue
            nodes = splitter.get_nodes_from_documents([Document(text=text)])
            for chunk_id, node in enumerate(nodes):
                writer.writerow({"url": row["url"], "chunk_id": chunk_id, "chunk_text": node.text})
                count += 1
    return count


def batched(items: Iterable[dict[str, str]], size: int) -> Iterable[list[dict[str, str]]]:
    batch: list[dict[str, str]] = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def request_embeddings(client, texts: list[str]) -> list[list[float]]:
    for attempt in range(1, 4):
        try:
            response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
            return [item.embedding for item in response.data]
        except Exception as exc:  # OpenAI exceptions vary across SDK versions.
            if attempt == 3:
                raise
            delay = 2**attempt
            LOGGER.warning("Embedding request failed (%s); retrying in %ss.", exc, delay)
            time.sleep(delay)
    raise RuntimeError("Embedding retries unexpectedly exhausted.")


def create_embeddings(input_path: Path, output_path: Path, batch_size: int) -> int:
    from openai import OpenAI

    client = OpenAI()
    count = 0
    with (
        input_path.open("r", newline="", encoding="utf-8") as input_file,
        output_path.open("w", newline="", encoding="utf-8") as output_file,
    ):
        reader = csv.DictReader(input_file)
        writer = csv.DictWriter(output_file, fieldnames=("url", "chunk_id", "chunk_text", "embedding"))
        writer.writeheader()
        for batch in batched(reader, batch_size):
            embeddings = request_embeddings(client, [row["chunk_text"] for row in batch])
            for row, embedding in zip(batch, embeddings, strict=True):
                row["embedding"] = json.dumps(embedding)
                writer.writerow(row)
                count += 1
            LOGGER.info("Embedded %s chunks.", count)
    return count


def copy_runtime_outputs(paths: PipelinePaths, embedding_source: Path, image_source: Path) -> None:
    RETRIEVAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(embedding_source, paths.ingestion_embeddings)
    shutil.copy2(embedding_source, paths.retrieval_embeddings)
    shutil.copy2(image_source, paths.ingestion_images)
    shutil.copy2(image_source, paths.retrieval_images)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-url", default="https://nau64.com")
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--max-urls", type=int, default=500)
    parser.add_argument("--min-delay", type=float, default=0.5)
    parser.add_argument("--max-delay", type=float, default=1.5)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--breakpoint-percentile", type=int, default=97)
    parser.add_argument("--skip-crawl", action="store_true", help="Reuse ingestion/crawled_data.csv.")
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Stop after writing crawl and cleaned intermediate files; do not call OpenAI or update runtime CSVs.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate configuration and print the plan without crawling or calling OpenAI.")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.max_depth < 0 or args.max_pages < 0 or args.max_urls < 1:
        raise ValueError("--max-depth and --max-pages must be non-negative; --max-urls must be positive.")
    if args.min_delay < 0 or args.max_delay < args.min_delay:
        raise ValueError("Delays must be non-negative and --max-delay must be at least --min-delay.")
    if args.batch_size < 1 or not 0 <= args.breakpoint_percentile <= 100:
        raise ValueError("--batch-size must be positive and --breakpoint-percentile must be between 0 and 100.")


def main() -> int:
    args = parse_args()
    validate_args(args)
    configure_csv_field_size_limit()
    paths = get_paths()

    if args.dry_run:
        LOGGER.info("Dry run: no crawl, OpenAI request, or file write will occur.")
        LOGGER.info("Would crawl %s (depth=%s, archive pages=%s, max URLs=%s).", args.start_url, args.max_depth, args.max_pages, args.max_urls)
        LOGGER.info("Would update %s and %s.", paths.ingestion_embeddings, paths.retrieval_embeddings)
        LOGGER.info("Would update %s and %s.", paths.ingestion_images, paths.retrieval_images)
        return 0

    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise RuntimeError("Install ingestion dependencies with: pip install -r ingestion/requirements.txt") from exc

    load_dotenv(ROOT_DIR / ".env")

    if not args.skip_embeddings and not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for semantic chunking and final embeddings.")
    if args.skip_crawl and not paths.crawled.exists():
        raise FileNotFoundError(f"--skip-crawl requires an existing file: {paths.crawled}")

    with tempfile.TemporaryDirectory(prefix="nauai-ingestion-") as temporary_directory:
        temporary_directory = Path(temporary_directory)
        crawled_path = temporary_directory / "crawled_data.csv"
        cleaned_path = temporary_directory / "cleaned_crawled_data.csv"
        chunked_path = temporary_directory / "chunked_data.csv"
        images_path = temporary_directory / "website_images.csv"
        embeddings_path = temporary_directory / "embedded_chunked_data.csv"

        if args.skip_crawl:
            shutil.copy2(paths.crawled, crawled_path)
            LOGGER.info("Reusing %s.", paths.crawled)
        else:
            pages = crawl_site(
                args.start_url, args.max_depth, args.max_pages, args.max_urls,
                args.min_delay, args.max_delay, args.timeout,
            )
            if not pages:
                raise RuntimeError("The crawl returned no pages; existing database CSVs were left unchanged.")
            write_crawled_pages(pages, crawled_path)
            LOGGER.info("Crawled %s pages.", len(pages))

        cleaned_count = clean_pages(crawled_path, cleaned_path)
        image_count = extract_images(crawled_path, images_path)
        if cleaned_count == 0:
            raise RuntimeError("No pages were available after cleaning; existing database CSVs were left unchanged.")
        LOGGER.info("Cleaned %s pages and found %s images.", cleaned_count, image_count)

        if args.skip_embeddings:
            shutil.copy2(crawled_path, paths.crawled)
            shutil.copy2(cleaned_path, paths.cleaned)
            LOGGER.info("Skipped semantic chunking and final embeddings; runtime CSVs were not changed.")
            return 0

        chunk_count = create_chunks(cleaned_path, chunked_path, args.breakpoint_percentile)
        if chunk_count == 0:
            raise RuntimeError("Semantic chunking produced no chunks; existing runtime CSVs were left unchanged.")
        embedding_count = create_embeddings(chunked_path, embeddings_path, args.batch_size)
        if embedding_count != chunk_count:
            raise RuntimeError("Embedding count did not match chunk count; existing runtime CSVs were left unchanged.")
        LOGGER.info("Created %s chunks and %s embeddings.", chunk_count, embedding_count)

        shutil.copy2(crawled_path, paths.crawled)
        shutil.copy2(cleaned_path, paths.cleaned)
        shutil.copy2(chunked_path, paths.chunked)
        copy_runtime_outputs(paths, embeddings_path, images_path)

    LOGGER.info("Ingestion completed successfully.")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        raise SystemExit(main())
    except Exception as error:
        LOGGER.error("Ingestion failed: %s", error)
        raise SystemExit(1) from error
