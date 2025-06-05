from campus_rag.utils.llm import llm_chat_async
import logging

logger = logging.getLogger(__name__)


source_list = {
  "course": "南京大学的所有课程数据，包含课程名称、老师、教学内容、学分、教材等信息",
  "teacher": "软件学院的老师数据，包含老师的姓名、职称、研究方向等信息",
  "manual": "南京大学的学生手册数据，包含学校的规章制度、学籍管理等信息",
}


async def route_query(query: str) -> list[str]:
  """Route the query to the appropriate source based on the provided source type.
  Args:
    query: The original query.
    source: The source type to route the query to.
  Return:
    The response from the LLM for the routed query.
  """

  prompt_content = {
    "role": "user",
    "content": f"""
        ## Instruction ##
        我们现在有三个数据源：{", ".join(source_list)}，请根据各个数据源的说明，将用户的输入路由到对应的数据源，一个输入可以对应到单个或多个路由。
        ## User's Query ##
        {query}
        ## Output ##
        请输出路由列表，用逗号分隔，格式为 "source1, source2, ..."，其中 source1, source2 是数据源的名称。
        不要输出任何其他内容或解释信息！
        ## Example ##
        南京大学有哪些做自然语言处理的老师？
        > course, teacher

        有没有事少分高的二层次英语课？
        > course

        课程挂科了怎么办？
        > manual
        """,
  }

  response = await llm_chat_async([prompt_content])
  logger.debug(f"Route LLM response: {response}")
  sources = []
  for source in source_list.keys():
    if source in response:
      sources.append(source)
  return sources
