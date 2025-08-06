# Pour executer les codes passer par le terminal avec la commande : 
# python -m api.schema.input

from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class NewsArticle(BaseModel):
    source: str
    author: Optional[str]
    title: str
    description: Optional[str]
    content: Optional[str]
    published_at: datetime
    url: HttpUrl
    image_url: Optional[HttpUrl]
    
from typing import List

class NewsResponse(BaseModel):
    articles: List[NewsArticle]
    total_results: int