# -*- coding: utf-8 -*-
"""Video xmodule tests in mongo."""

from mock import patch, PropertyMock
import os
import tempfile
import textwrap
import json
from webob import Request

from xmodule.contentstore.content import StaticContent
from xmodule.modulestore import Location
from xmodule.contentstore.django import contentstore
from . import BaseTestXmodule
from .test_video_xml import SOURCE_XML
from cache_toolbox.core import del_cached_content
from xmodule.exceptions import NotFoundError


def _create_srt_file(content=None, lang='uk'):
    """
    Create srt file in filesystem.
    """
    content = content or textwrap.dedent("""
        0
        00:00:00,12 --> 00:00:00,100
        Привіт, edX вітає вас.
    """)
    srt_file = tempfile.NamedTemporaryFile(suffix=".srt")
    srt_file.content_type = 'application/x-subrip'
    srt_file.write(content)
    srt_file.seek(0)
    return srt_file

def _clear_assets(location):
    store = contentstore()

    content_location = StaticContent.compute_location(
        location.org, location.course, location.name
    )

    assets, __ = store.get_all_content_for_course(content_location)
    for asset in assets:
        asset_location = Location(asset["_id"])
        del_cached_content(asset_location)
        id = StaticContent.get_id_from_location(asset_location)
        store.delete(id)

def _get_subs_id(filename):
        basename = os.path.splitext(os.path.basename(filename))[0]
        return basename.replace('subs_', '').replace('.srt', '')

def _create_file(content=''):
    sjson_file = tempfile.NamedTemporaryFile(prefix="subs_", suffix=".srt.sjson")
    sjson_file.content_type = 'application/json'
    sjson_file.write(textwrap.dedent(content))
    sjson_file.seek(0)
    return sjson_file

def _upload_sjson_file(file, location, default_filename='subs_{}.srt.sjson'):
    filename = default_filename.format(_get_subs_id(file.name))
    _upload_file(file, location, filename)

def _upload_file(file, location, filename):
    mime_type = file.content_type
    content_location = StaticContent.compute_location(
        location.org, location.course, filename
    )
    content = StaticContent(content_location, filename, mime_type, file.read())
    contentstore().save(content)
    del_cached_content(content.location)


class TestVideo(BaseTestXmodule):
    """Integration tests: web client + mongo."""
    CATEGORY = "video"
    DATA = SOURCE_XML
    METADATA = {}

    def test_handle_ajax_dispatch(self):
        responses = {
            user.username: self.clients[user.username].post(
                self.get_url('whatever'),
                {},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            for user in self.users
        }

        self.assertEqual(
            set([
                response.status_code
                for _, response in responses.items()
                ]).pop(),
            404)

    def tearDown(self):
        _clear_assets(self.item_descriptor.location)


class TestVideoTranscriptTranslation(TestVideo):

    non_en_file = _create_srt_file()
    DATA = """
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
            <transcript language="uk" src="{}"/>
        </video>
    """.format(os.path.split(non_en_file.name)[1])

    MODEL_DATA = {
        'data': DATA
    }

    def test_language_is_not_supported(self):
        request = Request.blank('/download?language=ru')
        response = self.item_descriptor.transcript(request=request, dispatch='download')
        self.assertEqual(response.status, '404 Not Found')

    def test_download_transcript_not_exist(self):
        request = Request.blank('/download?language=en')
        response = self.item_descriptor.transcript(request=request, dispatch='download')
        self.assertEqual(response.status, '404 Not Found')

    @patch('xmodule.video_module.VideoModule.get_transcript', return_value='Subs!')
    def test_download_exist(self, __):
        request = Request.blank('/download?language=en')
        response = self.item_descriptor.transcript(request=request, dispatch='download')
        self.assertEqual(response.body, 'Subs!')

    def test_translation_fails(self):
        # No videoId
        request = Request.blank('/translation?language=ru')
        response = self.item_descriptor.transcript(request=request, dispatch='translation')
        self.assertEqual(response.status, '400 Bad Request')

        # Language is not in available languages
        request = Request.blank('/translation?language=ru&videoId=12345')
        response = self.item_descriptor.transcript(request=request, dispatch='translation')
        self.assertEqual(response.status, '404 Not Found')


    def test_translaton_en_success(self):
        subs = {"start": [10,], "end": [100,], "text": [ "Hi, welcome to Edx.",]}
        good_sjson = _create_file(json.dumps(subs))
        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        subs_id = _get_subs_id(good_sjson.name)

        # to get instance
        self.item_descriptor.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        item.sub = subs_id
        request = Request.blank('/translation?language=en&videoId={}'.format(subs_id))
        response = self.item_descriptor.transcript(request=request, dispatch='translation')
        self.assertDictEqual(json.loads(response.body), subs)

    def test_translaton_non_en_non_youtube_success(self):
        subs =  {
            u'end': [100],
            u'start': [12],
            u'text': [
            u'\u041f\u0440\u0438\u0432\u0456\u0442, edX \u0432\u0456\u0442\u0430\u0454 \u0432\u0430\u0441.'
        ]}
        self.non_en_file.seek(0)
        _upload_file(self.non_en_file, self.item_descriptor.location, os.path.split(self.non_en_file.name)[1])
        subs_id = _get_subs_id(self.non_en_file.name)

        # to get instance
        self.item_descriptor.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance
        # manually clean youtube_id_1_0, as it has default value
        item.youtube_id_1_0 = ""

        request = Request.blank('/translation?language=uk&videoId={}'.format(subs_id))
        response = self.item_descriptor.transcript(request=request, dispatch='translation')
        self.assertDictEqual(json.loads(response.body), subs)

    def test_translation_non_en_youtube(self):
        subs =  {
            u'end': [100],
            u'start': [12],
            u'text': [
            u'\u041f\u0440\u0438\u0432\u0456\u0442, edX \u0432\u0456\u0442\u0430\u0454 \u0432\u0430\u0441.'
        ]}
        self.non_en_file.seek(0)
        _upload_file(self.non_en_file, self.item_descriptor.location, os.path.split(self.non_en_file.name)[1])
        subs_id = _get_subs_id(self.non_en_file.name)
        # to get instance

        # youtube 1_0 request, will generate for all speeds for existing ids
        self.item_descriptor.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance
        item.youtube_id_1_0 = subs_id
        item.youtube_id_0_75 = '0_75'
        request = Request.blank('/translation?language=uk&videoId={}'.format(subs_id))
        response = self.item_descriptor.transcript(request=request, dispatch='translation')
        self.assertDictEqual(json.loads(response.body), subs)

        # 0_75 subs are exist
        request = Request.blank('/translation?language=uk&videoId={}'.format('0_75'))
        response = self.item_descriptor.transcript(request=request, dispatch='translation')
        calculated_0_75 = {
            u'end': [75],
            u'start': [9],
            u'text': [
            u'\u041f\u0440\u0438\u0432\u0456\u0442, edX \u0432\u0456\u0442\u0430\u0454 \u0432\u0430\u0441.'
        ]}
        self.assertDictEqual(json.loads(response.body), calculated_0_75)
        # 1_5 will be generated from 1_0
        item = self.item_descriptor.xmodule_runtime.xmodule_instance
        item.youtube_id_1_5 = '1_5'
        request = Request.blank('/translation?language=uk&videoId={}'.format('1_5'))
        response = self.item_descriptor.transcript(request=request, dispatch='translation')
        calculated_1_5 = {
            u'end': [150],
            u'start': [18],
            u'text': [
            u'\u041f\u0440\u0438\u0432\u0456\u0442, edX \u0432\u0456\u0442\u0430\u0454 \u0432\u0430\u0441.'
        ]}
        self.assertDictEqual(json.loads(response.body), calculated_1_5)


class TestVideoTranscriptsDownload(TestVideo):
    """
    Make sure that `get_transcript` method works correctly
    """

    DATA = """
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
        </video>
    """
    MODEL_DATA = {
        'data': DATA
    }
    METADATA = {}

    def test_good_transcript(self):
        self.item_descriptor.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        good_sjson = _create_file(content=textwrap.dedent("""\
                {
                  "start": [
                    270,
                    2720
                  ],
                  "end": [
                    2720,
                    5430
                  ],
                  "text": [
                    "Hi, welcome to Edx.",
                    "Let&#39;s start with what is on your screen right now."
                  ]
                }
            """))

        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        item.sub = _get_subs_id(good_sjson.name)
        text = item.get_transcript()
        expected_text = textwrap.dedent("""\
            0
            00:00:00,270 --> 00:00:02,720
            Hi, welcome to Edx.

            1
            00:00:02,720 --> 00:00:05,430
            Let&#39;s start with what is on your screen right now.

            """)

        self.assertEqual(text, expected_text)

    def test_not_found_error(self):
        self.item_descriptor.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        with self.assertRaises(NotFoundError):
            item.get_transcript()

    def test_value_error(self):
        self.item_descriptor.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        good_sjson = _create_file(content='bad content')

        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        item.sub = _get_subs_id(good_sjson.name)

        with self.assertRaises(ValueError):
            item.get_transcript()

    def test_key_error(self):
        self.item_descriptor.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        good_sjson = _create_file(content="""
                {
                  "start": [
                    270,
                    2720
                  ],
                  "end": [
                    2720,
                    5430
                  ]
                }
            """)

        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        item.sub = _get_subs_id(good_sjson.name)

        with self.assertRaises(KeyError):
            item.get_transcript()




