# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import urlparse
import os
import pytest

from mediagoblin.tests.tools import fixture_add_user
from mediagoblin import mg_globals
from mediagoblin.db.models import MediaEntry
from mediagoblin.tools import template
from mediagoblin.media_types.image import MEDIA_MANAGER as img_MEDIA_MANAGER
from mediagoblin.media_types.pdf.processing import check_prerequisites as pdf_check_prerequisites

from .resources import GOOD_JPG, GOOD_PNG, EVIL_FILE, EVIL_JPG, EVIL_PNG, \
    BIG_BLUE, GOOD_PDF, GPS_JPG

GOOD_TAG_STRING = u'yin,yang'
BAD_TAG_STRING = unicode('rage,' + 'f' * 26 + 'u' * 26)

FORM_CONTEXT = ['mediagoblin/submit/start.html', 'submit_form']
REQUEST_CONTEXT = ['mediagoblin/user_pages/user.html', 'request']


class TestSubmission:
    @pytest.fixture(autouse=True)
    def setup(self, test_app):
        self.test_app = test_app

        # TODO: Possibly abstract into a decorator like:
        # @as_authenticated_user('chris')
        test_user = fixture_add_user()

        self.test_user = test_user

        self.login()

    def login(self):
        self.test_app.post(
            '/auth/login/', {
                'username': u'chris',
                'password': 'toast'})

    def logout(self):
        self.test_app.get('/auth/logout/')

    def do_post(self, data, *context_keys, **kwargs):
        url = kwargs.pop('url', '/submit/')
        do_follow = kwargs.pop('do_follow', False)
        template.clear_test_template_context()
        response = self.test_app.post(url, data, **kwargs)
        if do_follow:
            response.follow()
        context_data = template.TEMPLATE_TEST_CONTEXT
        for key in context_keys:
            context_data = context_data[key]
        return response, context_data

    def upload_data(self, filename):
        return {'upload_files': [('file', filename)]}

    def check_comments(self, request, media_id, count):
        comments = request.db.MediaComment.find({'media_entry': media_id})
        assert count == len(list(comments))

    def test_missing_fields(self):
        # Test blank form
        # ---------------
        response, form = self.do_post({}, *FORM_CONTEXT)
        assert form.file.errors == [u'You must provide a file.']

        # Test blank file
        # ---------------
        response, form = self.do_post({'title': u'test title'}, *FORM_CONTEXT)
        assert form.file.errors == [u'You must provide a file.']

    def check_url(self, response, path):
        assert urlparse.urlsplit(response.location)[2] == path

    def check_normal_upload(self, title, filename):
        response, context = self.do_post({'title': title}, do_follow=True,
                                         **self.upload_data(filename))
        self.check_url(response, '/u/{0}/'.format(self.test_user.username))
        assert 'mediagoblin/user_pages/user.html' in context
        # Make sure the media view is at least reachable, logged in...
        url = '/u/{0}/m/{1}/'.format(self.test_user.username,
                                     title.lower().replace(' ', '-'))
        self.test_app.get(url)
        # ... and logged out too.
        self.logout()
        self.test_app.get(url)

    def test_normal_jpg(self):
        self.check_normal_upload(u'Normal upload 1', GOOD_JPG)

    def test_normal_png(self):
        self.check_normal_upload(u'Normal upload 2', GOOD_PNG)

    @pytest.mark.skipif("not pdf_check_prerequisites()")
    def test_normal_pdf(self):
        response, context = self.do_post({'title': u'Normal upload 3 (pdf)'},
                                         do_follow=True,
                                         **self.upload_data(GOOD_PDF))
        self.check_url(response, '/u/{0}/'.format(self.test_user.username))
        assert 'mediagoblin/user_pages/user.html' in context

    def check_media(self, request, find_data, count=None):
        media = MediaEntry.find(find_data)
        if count is not None:
            assert media.count() == count
            if count == 0:
                return
        return media[0]

    def test_tags(self):
        # Good tag string
        # --------
        response, request = self.do_post({'title': u'Balanced Goblin 2',
                                          'tags': GOOD_TAG_STRING},
                                         *REQUEST_CONTEXT, do_follow=True,
                                         **self.upload_data(GOOD_JPG))
        media = self.check_media(request, {'title': u'Balanced Goblin 2'}, 1)
        assert media.tags[0]['name'] == u'yin'
        assert media.tags[0]['slug'] == u'yin'

        assert media.tags[1]['name'] == u'yang'
        assert media.tags[1]['slug'] == u'yang'

        # Test tags that are too long
        # ---------------
        response, form = self.do_post({'title': u'Balanced Goblin 2',
                                       'tags': BAD_TAG_STRING},
                                      *FORM_CONTEXT,
                                      **self.upload_data(GOOD_JPG))
        assert form.tags.errors == [
                u'Tags must be shorter than 50 characters.  ' \
                    'Tags that are too long: ' \
                    'ffffffffffffffffffffffffffuuuuuuuuuuuuuuuuuuuuuuuuuu']

    def test_delete(self):
        response, request = self.do_post({'title': u'Balanced Goblin'},
                                         *REQUEST_CONTEXT, do_follow=True,
                                         **self.upload_data(GOOD_JPG))
        media = self.check_media(request, {'title': u'Balanced Goblin'}, 1)
        media_id = media.id

        # render and post to the edit page.
        edit_url = request.urlgen(
            'mediagoblin.edit.edit_media',
            user=self.test_user.username, media_id=media_id)
        self.test_app.get(edit_url)
        self.test_app.post(edit_url,
            {'title': u'Balanced Goblin',
             'slug': u"Balanced=Goblin",
             'tags': u''})
        media = self.check_media(request, {'title': u'Balanced Goblin'}, 1)
        assert media.slug == u"balanced-goblin"

        # Add a comment, so we can test for its deletion later.
        self.check_comments(request, media_id, 0)
        comment_url = request.urlgen(
            'mediagoblin.user_pages.media_post_comment',
            user=self.test_user.username, media_id=media_id)
        response = self.do_post({'comment_content': 'i love this test'},
                                url=comment_url, do_follow=True)[0]
        self.check_comments(request, media_id, 1)

        # Do not confirm deletion
        # ---------------------------------------------------
        delete_url = request.urlgen(
            'mediagoblin.user_pages.media_confirm_delete',
            user=self.test_user.username, media_id=media_id)
        # Empty data means don't confirm
        response = self.do_post({}, do_follow=True, url=delete_url)[0]
        media = self.check_media(request, {'title': u'Balanced Goblin'}, 1)
        media_id = media.id

        # Confirm deletion
        # ---------------------------------------------------
        response, request = self.do_post({'confirm': 'y'}, *REQUEST_CONTEXT,
                                         do_follow=True, url=delete_url)
        self.check_media(request, {'id': media_id}, 0)
        self.check_comments(request, media_id, 0)

    def test_evil_file(self):
        # Test non-suppoerted file with non-supported extension
        # -----------------------------------------------------
        response, form = self.do_post({'title': u'Malicious Upload 1'},
                                      *FORM_CONTEXT,
                                      **self.upload_data(EVIL_FILE))
        assert len(form.file.errors) == 1
        assert 'Sorry, I don\'t support that file type :(' == \
                str(form.file.errors[0])


    def test_get_media_manager(self):
        """Test if the get_media_manger function returns sensible things
        """
        response, request = self.do_post({'title': u'Balanced Goblin'},
                                         *REQUEST_CONTEXT, do_follow=True,
                                         **self.upload_data(GOOD_JPG))
        media = self.check_media(request, {'title': u'Balanced Goblin'}, 1)

        assert media.media_type == u'mediagoblin.media_types.image'
        assert isinstance(media.media_manager, img_MEDIA_MANAGER)
        assert media.media_manager.entry == media


    def test_sniffing(self):
        '''
        Test sniffing mechanism to assert that regular uploads work as intended
        '''
        template.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': u'UNIQUE_TITLE_PLS_DONT_CREATE_OTHER_MEDIA_WITH_THIS_TITLE'
                }, upload_files=[(
                    'file', GOOD_JPG)])

        response.follow()

        context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/user_pages/user.html']

        request = context['request']

        media = request.db.MediaEntry.find_one({
            u'title': u'UNIQUE_TITLE_PLS_DONT_CREATE_OTHER_MEDIA_WITH_THIS_TITLE'})

        assert media.media_type == 'mediagoblin.media_types.image'

    def check_false_image(self, title, filename):
        # NOTE: The following 2 tests will ultimately fail, but they
        #   *will* pass the initial form submission step.  Instead,
        #   they'll be caught as failures during the processing step.
        response, context = self.do_post({'title': title}, do_follow=True,
                                         **self.upload_data(filename))
        self.check_url(response, '/u/{0}/'.format(self.test_user.username))
        entry = mg_globals.database.MediaEntry.find_one({'title': title})
        assert entry.state == 'failed'
        assert entry.fail_error == u'mediagoblin.processing:BadMediaFail'

    def test_evil_jpg(self):
        # Test non-supported file with .jpg extension
        # -------------------------------------------
        self.check_false_image(u'Malicious Upload 2', EVIL_JPG)

    def test_evil_png(self):
        # Test non-supported file with .png extension
        # -------------------------------------------
        self.check_false_image(u'Malicious Upload 3', EVIL_PNG)

    def test_media_data(self):
        self.check_normal_upload(u"With GPS data", GPS_JPG)
        media = self.check_media(None, {"title": u"With GPS data"}, 1)
        assert media.media_data.gps_latitude == 59.336666666666666

    def test_processing(self):
        public_store_dir = mg_globals.global_config[
            'storage:publicstore']['base_dir']

        data = {'title': u'Big Blue'}
        response, request = self.do_post(data, *REQUEST_CONTEXT, do_follow=True,
                                         **self.upload_data(BIG_BLUE))
        media = self.check_media(request, data, 1)
        last_size = 1024 ** 3  # Needs to be larger than bigblue.png
        for key, basename in (('original', 'bigblue.png'),
                              ('medium', 'bigblue.medium.png'),
                              ('thumb', 'bigblue.thumbnail.png')):
            # Does the processed image have a good filename?
            filename = os.path.join(
                public_store_dir,
                *media.media_files[key])
            assert filename.endswith('_' + basename)
            # Is it smaller than the last processed image we looked at?
            size = os.stat(filename).st_size
            assert last_size > size
            last_size = size
