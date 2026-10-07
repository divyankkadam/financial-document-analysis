from typing import TypedDict, Annotated, Optional
from operator import add


class GraphState(TypedDict):
    query:            str
    doc_id:           str           # primary selected doc
    file_path:        str

    all_doc_ids:      list          # every candidate after routing
    routed_docs:      list          # doc dicts the router picked
    routing_reason:   str           # why the router picked them

    parsed_text:      str
    doc_metadata:     dict
    chunks:           list
    embeddings_done:  bool

    retrieved_docs:   list
    filtered_docs:    list
    retrieval_score:  float

    sub_questions:    list
    draft_answer:     str
    final_answer:     str

    answer_quality:   str
    retry_count:      int
    confidence:       float

    log:              Annotated[list, add]
    eval_metrics:     dict

    