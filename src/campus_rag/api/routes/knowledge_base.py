from fastapi.routing import APIRouter
from src.campus_rag.impl.knowledge_base.selector import *
from src.campus_rag.domain.knowledge.po import *

router = APIRouter()


@router.get("/knowledge/all_name")
async def get_all_existing_knowledge_base_name() -> list[str]:
  return await get_all_collection_names()


@router.get("/knowledge/show_contents")
async def get_knowledge_base_contents_by_name(collection_name: str) -> list[dict]:
  return await get_collection_contents(collection_name)


@router.post("/knowledge/query")
async def get_topk_knowledge_by_query_only(query: TopKQueryModel) -> list[dict]:
  return await get_topk_results_by_query(
    query.query, query.collection_name, query.top_k
  )


@router.post("/knowledge/query_with_filter")
async def get_topk_knowledge_by_query_and_filter(
  query: TopKQueryModelWithFilter,
) -> list[dict]:
  course_filter = query.course_filter
  kwargs = {}
  if course_filter.course_name is not None:
    kwargs["course_name"] = course_filter.course_name
  if course_filter.course_number is not None:
    kwargs["course_number"] = course_filter.course_number
  if course_filter.type is not None:
    kwargs["course_type"] = course_filter.type
  if course_filter.campus is not None:
    kwargs["campus"] = course_filter.campus
  if course_filter.department is not None:
    kwargs["department"] = course_filter.department
  if course_filter.grade is not None:
    kwargs["grade"] = course_filter.grade
  if course_filter.credit is not None:
    kwargs["credit"] = course_filter.credit
  if course_filter.weekday is not None:
    inner_keys = []
    for i in range(3):
      res = [i, "time", "day_in_week"]
      inner_keys.append(res)
    inner_keys = [inner_keys]
    values = [course_filter.weekday]
    kwargs["inner_keys"] = inner_keys
    kwargs["values"] = values
  return await get_topk_results_by_query_and_filter(
    query.query, query.collection_name, query.top_k, **kwargs
  )
