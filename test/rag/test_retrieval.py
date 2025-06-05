import json
import pytest
import typer
import os
from tqdm import tqdm
from campus_rag.constants.conversation import TEST_PREFIX
from campus_rag.impl.rag.chat_pipeline import ChatPipeline
from campus_rag.utils.logging_config import setup_logger

logger = setup_logger()


app = typer.Typer()

test_question_root = "./data/test-data"
test_output_root = "./data/test-output"
file_list = ["question_manual.json", "question_course.json", "question_teacher.json"]


def load_json_file(filepath):
  with open(filepath, "r", encoding="utf-8") as f:
    return json.load(f)


def dump_json_file(filepath, data):
  with open(filepath, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)


def cal_statistic(test_data):
  total_length = len(test_data)
  hit_one = 0
  hit_all = 0
  top1_hit = 0
  top3_hit = 0

  for item in test_data:
    expected_chunks = set(item.get("expected_chunks", []))
    actual_chunk = set(item.get("actual_chunk", []))
    intersection = actual_chunk & expected_chunks

    if intersection:
      hit_one += 1
      if intersection == expected_chunks:
        hit_all += 1
      else:
        logger.warning(f"Question: {item['question']} Does not hit ALL chunks")
    else:
      logger.error(f"Question: {item['question']} Does not hit ANY chunk! ")

    if actual_chunk and item["actual_chunk"][0] in expected_chunks:
      top1_hit += 1
    if len(actual_chunk) >= 3 and any(
      chunk in expected_chunks for chunk in item["actual_chunk"][:3]
    ):
      top3_hit += 1

  hit_one_rate = hit_one / total_length if total_length else 0
  hit_all_rate = hit_all / total_length if total_length else 0
  top1_rate = top1_hit / total_length if total_length else 0
  top3_rate = top3_hit / total_length if total_length else 0
  return (
    hit_one_rate,
    hit_all_rate,
    top1_rate,
    top3_rate,
    hit_one,
    hit_all,
    top1_hit,
    top3_hit,
  )


def eval(filename):
  test_data = load_json_file(os.path.join(test_output_root, filename))
  (
    hit_one_rate,
    hit_all_rate,
    top1_rate,
    top3_rate,
    hit_one,
    hit_all,
    top1_hit,
    top3_hit,
  ) = cal_statistic(test_data)
  logger.info(f"File: {filename}")
  logger.info(f"  One Hit Rate: {hit_one_rate:.2f}")
  logger.info(f"  All Hit Rate: {hit_all_rate:.2f}")
  logger.info(f"  Top-1 hit rate: {top1_rate:.2f}")
  logger.info(f"  Top-3 hit rate: {top3_rate:.2f}")
  return len(test_data), hit_one, hit_all, top1_hit, top3_hit


async def retrieve(question: str, chat_pipeline: ChatPipeline) -> str:
  ares_generator = chat_pipeline.start(question, [])
  async for res in ares_generator:
    if TEST_PREFIX in res:
      chunks = await anext(ares_generator)
      break
  return chunks


async def calculate_actual_chunk(filename: str):
  from campus_rag.impl.rag.chat_pipeline import ChatPipeline

  chat_pipeline = ChatPipeline(test=True)
  test_data = load_json_file(os.path.join(test_question_root, filename))
  for item in tqdm(test_data, desc=f"Processing {filename}"):
    question = item.get("question", "")
    if not question:
      continue
    chunks = await retrieve(question, chat_pipeline)
    item["actual_chunk"] = [chunk["id"] for chunk in chunks if "id" in chunk]
    logger.info(f"Question: {question}, Retrieved Chunks: {item['actual_chunk']}")
  dump_json_file(os.path.join(test_output_root, filename), test_data)


@pytest.mark.asyncio
async def test_driver():
  total_len = 0
  total_hit_one = 0
  total_hit_all = 0
  total_top1_hit = 0
  total_top3_hit = 0

  for filename in file_list:
    # await calculate_actual_chunk(filename)
    length, hit_one, hit_all, top1_hit, top3_hit = eval(filename)
    total_len += length
    total_hit_one += hit_one
    total_hit_all += hit_all
    total_top1_hit += top1_hit
    total_top3_hit += top3_hit

  logger.info(f"Total Questions: {total_len}")
  logger.info(f"Total One Hit Rate: {total_hit_one / total_len:.2f}")
  logger.info(f"Total All Hit Rate: {total_hit_all / total_len:.2f}")
  logger.info(f"Total Top-1 Hit Rate: {total_top1_hit / total_len:.2f}")
  logger.info(f"Total Top-3 Hit Rate: {total_top3_hit / total_len:.2f}")


@pytest.mark.asyncio
async def test_diy():
  """Run this to test a single question"""
  from campus_rag.impl.rag.chat_pipeline import ChatPipeline

  chat_pipeline = ChatPipeline(test=True)
  questions = ["南京大学有哪些老师做NLP", "有没有事少分高的英语课？“"]
  chunks = await retrieve(questions[1], chat_pipeline)
  logger.info(f"Retrieved Chunks: {chunks}")
