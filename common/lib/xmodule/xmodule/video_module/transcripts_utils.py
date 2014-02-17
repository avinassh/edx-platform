"""
Utility functions for transcripts.
++++++++++++++++++++++++++++++++++
"""
import os
import copy
import json
import requests
import logging
from pysrt import SubRipTime, SubRipItem, SubRipFile
from lxml import etree

from xmodule.exceptions import NotFoundError
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.modulestore import Location

log = logging.getLogger(__name__)

class TranscriptException(Exception):
    pass

class TranscriptsGenerationException(Exception):
    pass


class GetTranscriptsFromYouTubeException(Exception):
    pass


class TranscriptsRequestValidationException(Exception):
    pass


def generate_subs(speed, source_speed, source_subs):
    """
    Generate transcripts from one speed to another speed.

    Args:
    `speed`: float, for this speed subtitles will be generated,
    `source_speed`: float, speed of source_subs
    `source_subs`: dict, existing subtitles for speed `source_speed`.

    Returns:
    `subs`: dict, actual subtitles.
    """
    if speed == source_speed:
        return source_subs

    coefficient = 1.0 * speed / source_speed
    subs = {
        'start': [
            int(round(timestamp * coefficient)) for
            timestamp in source_subs['start']
        ],
        'end': [
            int(round(timestamp * coefficient)) for
            timestamp in source_subs['end']
        ],
        'text': source_subs['text']}
    return subs


def save_subs_to_store(subs, subs_id, item, language='en'):
    """
    Save transcripts into `StaticContent`.

    Args:
    `subs_id`: str, subtitles id
    `item`: video module instance
    `language`: two chars str ('uk'), language of translation of transcripts

    Returns: location of saved subtitles.
    """
    filedata = json.dumps(subs, indent=2)
    mime_type = 'application/json'
    if language == 'en':
        filename = 'subs_{0}.srt.sjson'.format(subs_id)
    else:
        filename = '{0}_subs_{1}.srt.sjson'.format(language, subs_id)

    content_location = StaticContent.compute_location(
        item.location.org, item.location.course, filename
    )
    content = StaticContent(content_location, filename, mime_type, filedata)
    contentstore().save(content)
    from cache_toolbox.core import del_cached_content
    del_cached_content(content_location)
    return content_location


def get_transcripts_from_youtube(youtube_id, settings, i18n):
    """
    Gets transcripts from youtube for youtube_id.

    Parses only utf-8 encoded transcripts.
    Other encodings are not supported at the moment.

    Returns (status, transcripts): bool, dict.
    """
    _ = i18n.ugettext
    utf8_parser = etree.XMLParser(encoding='utf-8')

    youtube_api = copy.deepcopy(settings.YOUTUBE_API)
    youtube_api['params']['v'] = youtube_id
    data = requests.get(youtube_api['url'], params=youtube_api['params'])

    if data.status_code != 200 or not data.text:
        msg = _("Can't receive transcripts from Youtube for {youtube_id}. Status code: {statuc_code}.").format(
            youtube_id=youtube_id,
            statuc_code=data.status_code
        )
        raise GetTranscriptsFromYouTubeException(msg)

    sub_starts, sub_ends, sub_texts = [], [], []
    xmltree = etree.fromstring(data.content, parser=utf8_parser)
    for element in xmltree:
        if element.tag == "text":
            start = float(element.get("start"))
            duration = float(element.get("dur", 0))  # dur is not mandatory
            text = element.text
            end = start + duration

            if text:
                # Start and end should be ints representing the millisecond timestamp.
                sub_starts.append(int(start * 1000))
                sub_ends.append(int((end + 0.0001) * 1000))
                sub_texts.append(text.replace('\n', ' '))

    return {'start': sub_starts, 'end': sub_ends, 'text': sub_texts}


def download_youtube_subs(youtube_subs, item, settings, i18n):
    """
    Download transcripts from Youtube and save them to assets.

    Args:
    youtube_subs: dictionary of `speed: youtube_id` key:value pairs.
    item: video module instance.

    Returns: None, if transcripts were successfully downloaded and saved.
    Otherwise raises GetTranscriptsFromYouTubeException.
    """
    _ = i18n.ugettext
    highest_speed = highest_speed_subs = None
    missed_speeds = []
    # Iterate from lowest to highest speed and try to do download transcripts
    # from the Youtube service.
    for speed, youtube_id in sorted(youtube_subs.iteritems()):
        if not youtube_id:
            continue
        try:
            subs = get_transcripts_from_youtube(youtube_id, settings, i18n)
            if not subs:  # if empty subs are returned
                raise GetTranscriptsFromYouTubeException
        except GetTranscriptsFromYouTubeException:
            missed_speeds.append(speed)
            continue

        save_subs_to_store(subs, youtube_id, item)

        log.info(
            "Transcripts for YouTube id %s (speed %s)"
            "are downloaded and saved.", youtube_id, speed
        )

        highest_speed = speed
        highest_speed_subs = subs

    if not highest_speed:
        raise GetTranscriptsFromYouTubeException(_("Can't find any transcripts on the Youtube service."))

    # When we exit from the previous loop, `highest_speed` and `highest_speed_subs`
    # are the transcripts data for the highest speed available on the
    # Youtube service. We use the highest speed as main speed for the
    # generation other transcripts, cause during calculation timestamps
    # for lower speeds we just use multiplication instead of division.
    for speed in missed_speeds:  # Generate transcripts for missed speeds.
        save_subs_to_store(
            generate_subs(speed, highest_speed, highest_speed_subs),
            youtube_subs[speed],
            item
        )

        log.info(
            "Transcripts for YouTube id %s (speed %s)"
            "are generated from YouTube id %s (speed %s) and saved",
            youtube_subs[speed], speed,
            youtube_subs[highest_speed],
            highest_speed
        )


def remove_subs_from_store(subs_id, item, lang):
    """
    Remove from store, if transcripts content exists.
    """
    if lang != 'en':
        filename = '{0}_subs_{1}.srt.sjson'.format(lang, subs_id)
    else:
        filename = 'subs_{0}.srt.sjson'.format(subs_id)
    content_location = StaticContent.compute_location(
        item.location.org, item.location.course, filename
    )
    try:
        content = contentstore().find(content_location)
        contentstore().delete(content.get_id())
        from cache_toolbox.core import del_cached_content
        del_cached_content(content.location)
        log.info("Removed subs %s from store", subs_id)
    except NotFoundError:
        pass


def generate_subs_from_source(speed_subs, subs_type, subs_filedata, item, language='en'):
    """Generate transcripts from source files (like SubRip format, etc.)
    and save them to assets for `item` module.
    We expect, that speed of source subs equal to 1

    :param speed_subs: dictionary {speed: sub_id, ...}
    :param subs_type: type of source subs: "srt", ...
    :param subs_filedata:unicode, content of source subs.
    :param item: module object.
    :param language: str, language of translation of transcripts
    :returns: True, if all subs are generated and saved successfully.
    """
    _ = item.runtime.service(item, "i18n").ugettext  # FIXME CHECK TODO
    if subs_type != 'srt':
        raise TranscriptsGenerationException(_("We support only SubRip (*.srt) transcripts format."))
    try:
        srt_subs_obj = SubRipFile.from_string(subs_filedata)
    except Exception as e:
        msg = _("Something wrong with SubRip transcripts file during parsing. Inner message is {error_message}").format(
            error_message=e.message
        )
        raise TranscriptsGenerationException(msg)
    if not srt_subs_obj:
        raise TranscriptsGenerationException(_("Something wrong with SubRip transcripts file during parsing."))

    sub_starts = []
    sub_ends = []
    sub_texts = []

    for sub in srt_subs_obj:
        sub_starts.append(sub.start.ordinal)
        sub_ends.append(sub.end.ordinal)
        sub_texts.append(sub.text.replace('\n', ' '))

    subs = {
        'start': sub_starts,
        'end': sub_ends,
        'text': sub_texts}

    for speed, subs_id in speed_subs.iteritems():
        save_subs_to_store(
            generate_subs(speed, 1, subs),
            subs_id,
            item,
            language
        )

    return subs


def generate_srt_from_sjson(sjson_subs, speed):
    """Generate transcripts with speed = 1.0 from sjson to SubRip (*.srt).

    :param sjson_subs: "sjson" subs.
    :param speed: speed of `sjson_subs`.
    :returns: "srt" subs.
    """

    output = ''

    equal_len = len(sjson_subs['start']) == len(sjson_subs['end']) == len(sjson_subs['text'])
    if not equal_len:
        return output

    sjson_speed_1 = generate_subs(speed, 1, sjson_subs)

    for i in range(len(sjson_speed_1['start'])):
        item = SubRipItem(
            index=i,
            start=SubRipTime(milliseconds=sjson_speed_1['start'][i]),
            end=SubRipTime(milliseconds=sjson_speed_1['end'][i]),
            text=sjson_speed_1['text'][i]
        )
        output += (unicode(item))
        output += '\n'
    return output


def save_module(item, user):
    """
    Proceed with additional save operations.
    """
    item.save()
    from contentstore.utils import get_modulestore
    store = get_modulestore(Location(item.id))
    store.update_item(item, user.id if user else None)


def copy_or_rename_transcript(new_name, old_name, item, delete_old=False, user=None):
    """
    Renames `old_name` transcript file in storage to `new_name`.

    If `old_name` is not found in storage, raises `NotFoundError`.
    If `delete_old` is True, removes `old_name` files from storage.
    """
    filename = 'subs_{0}.srt.sjson'.format(old_name)
    content_location = StaticContent.compute_location(
        item.location.org, item.location.course, filename
    )
    transcripts = contentstore().find(content_location).data
    save_subs_to_store(json.loads(transcripts), new_name, item)
    item.sub = new_name
    save_module(item, user)
    if delete_old:
        remove_subs_from_store(old_name, item)


def get_html5_ids(html5_sources):
    """
    Helper method to parse out an HTML5 source into the ideas
    NOTE: This assumes that '/' are not in the filename
    """
    html5_ids = [x.split('/')[-1].rsplit('.', 1)[0] for x in html5_sources]
    return html5_ids


def manage_video_subtitles_save(old_item, new_item, user):
    """
    Does some specific things, that can be done only on save.

    Video player item has some video fields: HTML5 ones and Youtube one.

    If value of `sub` field of `new_item` is cleared, transcripts should be removed.

    # 1.
    If value of `sub` field of `new_item` is different from values of video fields of `new_item`,
    and `new_item.sub` file is present, then code in this function creates copies of
    `new_item.sub` file with new names. That names are equal to values of video fields of `new_item`
    After that `sub` field of `new_item` is changed to one of values of video fields.
    This whole action ensures that after user changes video fields, proper `sub` files, corresponding
    to new values of video fields, will be presented in system.

    # 2.
    If some of SRT file names are updated, we need to
        a) regenerate sjson subtitles for all video ids from new SRTs
        b) delete sjson translation for those languages, which were removed from transcripts.
        c) if default language was in removed subtitles, it should be changed to 'en'
    Note: we are not deleting old SRT files to give user more flexibility.

    """

    # 1.
    html5_ids = get_html5_ids(new_item.html5_sources)
    possible_video_id_list = [new_item.youtube_id_1_0] + html5_ids
    sub_name = new_item.sub
    for video_id in possible_video_id_list:
        if not video_id:
            continue
        if not sub_name:
            remove_subs_from_store(video_id, new_item)
            continue
        # copy_or_rename_transcript changes item.sub of module
        try:
            # updates item.sub with `video_id`, if it is successful.
            copy_or_rename_transcript(video_id, sub_name, new_item, user=user)
        except NotFoundError:
            # subtitles file `sub_name` is not presented in the system. Nothing to copy or rename.
            log.debug(
                "Copying %s file content to %s name is failed, "
                "original file does not exist.",
                sub_name, video_id
            )

        # 2.
        old_langs, new_langs = set(old_item.transcripts), set(new_item.transcripts)

        if self.transcript_language not in new_langs: # 2c
            self.transcript_language = 'en'
            save_module(new_item, user)

        for lang in old_langs.different(new_langs): # 2b
                for video_id in possible_video_id_list:
                    if video_id:
                        remove_subs_from_store(video_id, new_item, lang)

        for lang in new_langs.intersection(old_langs): # 2a
            if old_item.transcripts[lang] != new_item.transcripts[lang]:
                generate_sjson_for_all_speeds(
                    new_item,
                    new_item.transcripts[lang],
                    youtube_speed_dict(item)
                    )


def youtube_speed_dict(item):
    """
    Returns {speed: youtube_ids, ...} dict for existing youtube_ids
    """
        yt_ids = [item.youtube_id_0_75, item.youtube_id_1_0, item.youtube_id_1_25, item.youtube_id_1_5]
        yt_speeds = [0.75, 1.00, 1.25, 1.50]
        youtube_ids = {p[0]: p[1] for p in zip(yt_ids, yt_speeds) if p[0]}
        return youtube_ids

def subs_filename(subs_id, lang='en'):
    """
    Generate proper filename for storage.
    """
    if lang == 'en':
        return 'subs_{0}.srt.sjson'.format(subs_id)
    else:
        return '{0}_subs_{1}.srt.sjson'.format(lang, subs_id)


def asset_location(location, filename):
    """
    Return asset location.

    `location` is module location.
    """
    return StaticContent.compute_location(
        location.org, location.course, filename
    )


def asset(location, subs_id, lang='en'):
    """
    Get asset from contentstore, asset location is build from subs_id and lang.

    `location` is module location.
    """
    return contentstore().find(
        asset_location(
            location,
            subs_filename(subs_id, lang)
        )
    )


def generate_sjson_for_all_speeds(item, user_filename, result_subs_dict):
    """
    Generates sjson from srt.

    `item` is module object.
    """
    try:
        srt_transcripts = contentstore().find(asset_location(item.location, user_filename))
    except NotFoundError as e:
        raise TranscriptException("{}: Can't find uploaded transcripts: {}".format(e.message, user_filename))

    generate_subs_from_source(
        result_subs_dict,
        os.path.splitext(user_filename)[1][1:],
        srt_transcripts.data.decode('utf8'),
        item,
        item.transcript_language
    )

def get_or_create_sjson(item):
    """
    Get sjson if already exists, otherwise generate it.

    Generate sjson with subs_id name, from user uploaded srt.
    Subs_id is extracted from srt filename, which was set by user.

    Raises:
        TranscriptException: when srt subtitles do not exist,
        and exceptions from generate_subs_from_source.

    `item` is module object.
    """
    user_filename = item.transcripts[item.transcript_language]
    user_subs_id = os.path.splitext(user_filename)[0]
    source_subs_id, result_subs_dict = user_subs_id, {1.0: user_subs_id}
    try:
        sjson_transcript = asset(item.location, source_subs_id, item.transcript_language).data
    except (NotFoundError):  # generating sjson from srt
        generate_sjson_for_all_speeds(item, user_filename, result_subs_dict)
    sjson_transcript = asset(item.location, source_subs_id, item.transcript_language).data
    return sjson_transcript
