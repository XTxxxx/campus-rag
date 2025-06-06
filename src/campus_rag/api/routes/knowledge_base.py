from fastapi import Depends
from fastapi.routing import APIRouter
from huggingface_hub import User
from campus_rag.impl.knowledge_base.selector import (
  get_topk_results_by_query,
  get_collection_contents,
  get_all_collection_names,
  get_all_sources,
)
from campus_rag.domain.knowledge.po import (
  ContentsRequest,
  TopKQueryModel,
  UploadKnowledge,
  ModifyRequest,
)
from campus_rag.impl.knowledge_base.writer import upload, modify, delete_knowledge_by_id
from campus_rag.impl.user.user import get_current_admin_user

router = APIRouter()


@router.get("/knowledge/all_sources", response_model=list[str])
async def get_all_existing_knowledge_base_sources(
  user: User = Depends(get_current_admin_user),
) -> list[str]:
  return await get_all_sources()


@router.post("/knowledge/show_contents", response_model=list[dict])
async def get_knowledge_base_contents_by_source(
  contents_request: ContentsRequest,
  user: User = Depends(get_current_admin_user),
) -> list[dict]:
  # get contents by certain page: e.g. page-2 contents
  return await get_collection_contents(
    contents_request.sources,
    contents_request.page_id,
    contents_request.page_size,
  )


@router.post("/knowledge/query", response_model=list[dict])
async def get_topk_knowledge_by_query_only(
  query: TopKQueryModel,
  user: User = Depends(get_current_admin_user),
) -> list[dict]:
  return await get_topk_results_by_query(query.query, query.sources, query.top_k)


@router.post("/knowledge/upload", response_model=bool)
async def upload_knowledge(
  knowledge: UploadKnowledge, user: User = Depends(get_current_admin_user)
) -> bool:
  # now if uploading a new knowledge base, it will cover the existing one with the same name
  return await upload(
    knowledge.sources,
    knowledge.knowledge,
  )


@router.delete("/knowledge/delete", response_model=bool)
async def delete_knowledge(request_id: str, user: User = Depends(get_current_admin_user)):
  return await delete_knowledge_by_id(request_id)


@router.post("/knowledge/modify", response_model=bool)
async def modify_chunk(
  mr: ModifyRequest, user: User = Depends(get_current_admin_user)
) -> bool:
  return await modify(mr.request_id, mr.context, mr.chunk, mr.cleaned_chunk)
