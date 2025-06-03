from fastapi.routing import APIRouter
from campus_rag.impl.knowledge_base.selector import (
  get_topk_results_by_query,
  get_collection_contents,
  get_all_collection_names,
)
from campus_rag.domain.knowledge.po import (
  ContentsRequest,
  TopKQueryModel,
  UploadKnowledge,
  ModifyChunk,
)
from campus_rag.impl.knowledge_base.writer import (
  upload,
  get_chunk_by_id,
  get_chunk_ids_by_collection_name,
  modify_chunk_by_id,
)

router = APIRouter()


@router.get("/knowledge/all_name")
async def get_all_existing_knowledge_base_name() -> list[str]:
  return await get_all_collection_names()


@router.post("/knowledge/show_contents")
async def get_knowledge_base_contents_by_name(contents_request: ContentsRequest) -> list[dict]:
  # get contents by certain page: e.g. page-2 contents
  return await get_collection_contents(contents_request.collection_name, contents_request.page_id,
                                       contents_request.page_size)


@router.post("/knowledge/query")
async def get_topk_knowledge_by_query_only(query: TopKQueryModel) -> list[dict]:
  return await get_topk_results_by_query(
    query.query, query.collection_name, query.top_k
  )


# @router.post("/knowledge/query_with_filter")
# async def get_topk_knowledge_by_query_and_filter(
#   query: TopKQueryModelWithFilter,
# ) -> list[dict]:
#   course_filter = query.course_filter
#   kwargs = {}
#   if course_filter.course_name is not None:
#     kwargs["course_name"] = course_filter.course_name
#   if course_filter.course_number is not None:
#     kwargs["course_number"] = course_filter.course_number
#   if course_filter.type is not None:
#     kwargs["course_type"] = course_filter.type
#   if course_filter.campus is not None:
#     kwargs["campus"] = course_filter.campus
#   if course_filter.department is not None:
#     kwargs["department"] = course_filter.department
#   if course_filter.grade is not None:
#     kwargs["grade"] = course_filter.grade
#   if course_filter.credit is not None:
#     kwargs["credit"] = course_filter.credit
#   if course_filter.weekday is not None:
#     inner_keys = []
#     for i in range(3):
#       res = [i, "time", "day_in_week"]
#       inner_keys.append(res)
#     inner_keys = [inner_keys]
#     values = [course_filter.weekday]
#     kwargs["inner_keys"] = inner_keys
#     kwargs["values"] = values
#   return await get_topk_results_by_query_and_filter(
#     query.query, query.collection_name, query.top_k, **kwargs
#   )


@router.post("/knowledge/upload")
async def upload_knowledge(knowledge: UploadKnowledge) -> bool:
  # now if uploading a new knowledge base, it will cover the existing one with the same name
  return await upload(
    knowledge.collection_name,
    knowledge.knowledge,
    knowledge.chunk_keys,
    knowledge.max_value_size,
    knowledge.meta_field,
  )


@router.get("/knowledge/chunk_ids")
async def get_chunk_ids(collection_name: str) -> list[int]:
  # return all avaliable ids in Collection with collection_name
  # print(collection_name)
  return await get_chunk_ids_by_collection_name(collection_name)


@router.get("/knowledge/chunk_by_id")
async def get_chunk(collection_name: str, chunk_id: int) -> str:
  # get chunk content by chunk id
  return await get_chunk_by_id(collection_name, chunk_id)


@router.post("/knowledge/modify_chunk")
async def modify_chunk(modify_chunk: ModifyChunk) -> bool:
  return await modify_chunk_by_id(
    modify_chunk.collection_name, modify_chunk.chunk_id, modify_chunk.new_chunk
  )
