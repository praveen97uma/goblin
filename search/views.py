from mediagoblin.search import forms
from mediagoblin.search import indexer
from mediagoblin.db.models import MediaEntry

from whoosh.index import open_dir
from whoosh.qparser import QueryParser, MultifieldParser

from mediagoblin.tools.response import render_to_response, redirect

import logging


_log = logging.getLogger(__name__)


def search(request):
    
    form = forms.SearchForm(request.form)
    results = None
    context = {
        'form': form, 
        'results': None, 
        'query': None, 
        'search_response': False
    }

    if request.method == 'POST' and form.validate():
        query = form.query.data
        ix = open_dir(indexer.MEDIA_INDEX_DIR)
        with ix.searcher() as searcher:
            query_string = MultifieldParser(['title', 'description', 'slug'], ix.schema).parse(query)
            results = searcher.search(query_string)

            res = []
            if len(results)>0:
                for result in results:
                    media_id = result['media_id']
                    entry = MediaEntry.query.get(media_id)
                    res.append({
                        'slug': entry.slug,
                        'url': entry.url_for_self(request.urlgen),
                    })

            context.update({
                'results': res,
                'search_response': True,
                'query': query,
            })
            return render_to_response(request, 'mediagoblin/search/search.html', context)
    
    return render_to_response(
        request,
        'mediagoblin/search/search.html',
        context)


def gen_media_index(request):
    _log.info("Called view for creating an index")
    indexer.create_index()
    _log.info("Indexing of media entries finished.")
    return redirect(request,'mediagoblin.search.search')
