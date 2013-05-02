from whoosh.index import create_in
from whoosh.fields import *
from mediagoblin.db.models import MediaEntry
from whoosh.index import open_dir
from whoosh.qparser import QueryParser

import logging
import os

_log = logging.getLogger(__name__)

CURRENT_DIR = os.path.dirname(__file__)

MEDIA_INDEX_DIR = os.path.join(CURRENT_DIR, "media_index")

def get_all_media_entries():
    all_entries = MediaEntry.query.all()
    return all_entries

def create_index():
    schema = Schema(
        title=TEXT,
        description=TEXT,
        media_id=NUMERIC(stored=True),
        slug=TEXT)
    
    if not os.path.exists(MEDIA_INDEX_DIR):
        os.mkdir(MEDIA_INDEX_DIR)

    ix = create_in(MEDIA_INDEX_DIR, schema)
    media_entries = get_all_media_entries()
    
    writer = ix.writer()
    _log.info("Creation of Index started")
    for media in media_entries:
        writer.add_document(title=unicode(media.title), description=unicode(media.description),
                            media_id=media.id, slug=unicode(media.slug))
        _log.info("Adding document with slug %s"%(media.slug))
    writer.commit()
    _log.info("Index creation finished.")



def searcher(query):
    ix = open_dir(MEDIA_INDEX_DIR)
    parser = QueryParser("title", ix.schema)
    query_string = parser.parse(query)
    results = []
    results_obj = None
    with ix.searcher() as finder:
        results_obj = finder.search(query_string)
        _log.info("Length of the results %d"%(len(results_obj)))
      
    _log.info("Type of results obj is %s"%type(results_obj))
    #results = [dic for dic in results_obj if results_obj]
    _log.info("Type of results is %s"%(type(results)))
    _log.info(results_obj)
    return results_obj
