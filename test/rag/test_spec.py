import pytest
import typer
import os
from tqdm import tqdm
from campus_rag.constants.conversation import TEST_PREFIX
from campus_rag.utils.logging_config import setup_logger
from campus_rag.impl.rag.chat_pipeline import ChatPipeline

logger = setup_logger()


app = typer.Typer()
