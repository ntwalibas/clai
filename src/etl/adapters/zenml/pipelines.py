from zenml import pipeline

from etl.adapters.zenml.steps import clean_docs, fetch_docs, load_docs


@pipeline(settings={"orchestrator": {"synchronous": False}})
def docpage_etl(doc_configs: list[dict[str, str]]) -> str:
    sources = [page["source"] for page in doc_configs]
    raw_docs = fetch_docs(sources)
    cleaned_docs = clean_docs(raw_docs)
    docpages = load_docs(doc_configs, cleaned_docs)
    return docpages
