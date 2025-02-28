import requests
import logging
import json
import subprocess
import os
from pymediainfo import MediaInfo
import sys
import xml.etree.ElementTree as ET
import xml.dom.minidom
import argparse
import time
import pprint
import random
import random
from collections import defaultdict
from datetime import datetime, timezone


# Global instance
discovery_url_object = None
SHOW_MEDIA_INFO_DETAILS = False
REPORTING_ENABLED = False
creative_id_list = []
prefetch_repeat_count = 1
decision_repeat_count = 1
enable_check_services = False
ts_files_folder_name = 'ts_files_folder'

ERROR_CODES = [
    100,  # XML parsing error.
    101,  # VAST schema validation error.
    102,  # VAST version of response not supported.
    200,  # Trafficking error. Video player received an ad type that it was not expecting and/or cannot display.
    201,  # Video player expecting different linearity.
    202,  # Video player expecting different duration.
    203,  # Video player expecting different size.
    300,  # General Wrapper error.
    301,  # Timeout of VAST URI provided in Wrapper element, or of VAST URI provided in a subsequent Wrapper element.
    302,  # Wrapper limit reached, as defined by the video player. Too many Wrapper responses have been received with no inLine response.
    303,  # No VAST response after one or more Wrappers.
    400,  # General Linear error.
    401,  # File not found. Unable to find Linear/MediaFile from URI.
    402,  # Timeout of MediaFile URI.
    403,  # Could not find MediaFile that is supported by this video player, based on the attributes of the MediaFile element.
    404,  # Problem displaying MediaFile. Video player found a MediaFile with supported type but couldn't display it.
    405,  # Mezzanine is required, but not provided.
    500,  # General NonLinearAds error.
    501,  # Unable to display NonLinearAd because creative dimensions do not align with creative display area (i.e., creative dimension too large).
    600,  # General CompanionAds error.
    601,  # Unable to display CompanionAd.
    602,  # Unable to fetch CompanionAd.
    603,  # Could not find CompanionAd with supported type.
    900,  # Undefined error.
    901,  # General VPAID error.
]

class DiscoveryURLs:
    def __init__(self, card_id, device_id):
        self.decisionRequestURL = None
        self.preFetchUrl = None
        self.channelListUrl = None
        self.subscriberInfoUrl = None
        self.errorReportUrl = None
        self.debugUrl = None

        self.card_id = card_id
        self.sub_id = -1
        self.device_id = device_id
        if device_id is None:
            self.device_id = card_id

    def set_subscriberID(self, sub_id):
        self.sub_id = sub_id

    def set_urls(self, data):
        try:
            self.decisionRequestURL = data["decisionServer"]["decisionRequestURL"]
            self.preFetchUrl = data["decisionServer"]["preFetchUrl"]
            self.channelListUrl = data["channelList"]["channelListUrl"]
            self.subscriberInfoUrl = data["subscriberInfo"]["subscriberInfoUrl"]
            self.errorReportUrl = data["reporting"]["errorReportUrl"]
            self.debugUrl = data["reporting"]["debugUrl"]
        except KeyError as e:
            logging.error(f"Key error when setting URLs: {e}")

    def get_decisionRequestURL(self):
        return self.decisionRequestURL.replace("[SUBSCRIBERID]", str(self.sub_id)).replace("[DEVICEID]", str(self.device_id))

    def get_preFetchUrl(self):
        return self.preFetchUrl.replace("[SUBSCRIBERID]", str(self.sub_id)).replace("[DEVICEID]", str(self.device_id))

    def get_channelListUrl(self):
        return self.channelListUrl

    def get_subscriberInfoUrl(self):
        if "[CARDID]" in self.subscriberInfoUrl:
            return self.subscriberInfoUrl.replace("[CARDID]", str(self.card_id))
        return self.subscriberInfoUrl

    def get_errorReportUrl(self):
        return self.errorReportUrl

    def get_debugUrl(self):
        return self.debugUrl



def fetch_url_data(url, xmlType=False):
    try:
        response = requests.get(url)
        
        # Log request headers
        logging.debug("Request Headers:")
        for key, value in response.request.headers.items():
            logging.debug(f"{key}: {value}")
        
        response.raise_for_status()  # Raise an HTTPError for bad responses
        
        # Log response status code
        logging.debug("Response Status Code: %d", response.status_code)
        
        # Log response headers
        logging.debug("Response Headers:")
        for key, value in response.headers.items():
            logging.debug(f"{key}: {value}")
        
        # Log raw response data
        logging.debug("Raw Response Data:")
        logging.debug(response.text)

        if not xmlType:
            # Parse and pretty-print the JSON response
            response_json = response.json()
            pretty_response_json = json.dumps(response_json, indent=4)
            logging.info(f"Response JSON:\n{pretty_response_json}")
            return response_json
        else:
            dom = xml.dom.minidom.parseString(response.text)
            pretty_xml_as_string = dom.toprettyxml(indent=" ")
            logging.info(f"Response JSON:\n{pretty_xml_as_string}")
            return response.text

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return 


def performReport(xml_string):
    # Parse the XML string
    namespaces = {'vast': 'http://www.iab.com/VAST'}
    root = ET.fromstring(xml_string)
    
    # Extract the duration of the ad
    duration_str = root.find('.//vast:Linear/vast:Duration', namespaces).text
    h, m, s = map(float, duration_str.split(':'))
    total_duration_seconds = h * 3600 + m * 60 + s
    
    # Extract impression and tracking event URLs
    impressions = [impression.text for impression in root.findall('.//vast:Impression', namespaces)]
    tracking_events = {event.get('event'): event.text for event in root.findall('.//vast:TrackingEvents/vast:Tracking', namespaces)}
    errors = [error.text for error in root.findall('.//vast:Error', namespaces)]

    tracking_events = defaultdict(list)
    for event in root.findall('.//vast:TrackingEvents/vast:Tracking', namespaces):
        event_type = event.get('event')
        event_url = event.text.strip()  # Strip any extra whitespace
        tracking_events[event_type].append(event_url)

    tracking_events = dict(tracking_events)

    # Reporting times
    start_time = 0
    first_quartile_time = total_duration_seconds * 0.25
    midpoint_time = total_duration_seconds * 0.5
    third_quartile_time = total_duration_seconds * 0.75
    complete_time = total_duration_seconds

    # Function to perform HTTP GET request
    def report_event(url, event_name):
        try:
            logging.info(f"{event_name} url: {url}")
            response = requests.get(url)
            response.raise_for_status()
            logging.info(f"status code: {response.status_code}")
            logging.info(f"response text: {response.text}")
            logging.info("")
        except requests.RequestException as e:
            logging.error(f"Request Failed reason: {e}")
            logging.info("")


    # Report impressions
    logging.info("")
    logging.info("(+) Reporting Impressions: ")
    for url in impressions:
        report_event(url, "impression")

    # Sleep for each event's duration and then report
    logging.info("")
    logging.info("(+) Reporting TrackingEvents: ")
    time.sleep(start_time)
    start_events = tracking_events["start"]
    for url in start_events:
        report_event(url, "start")

    time.sleep(first_quartile_time - start_time)
    firstQuartile_events = tracking_events["firstQuartile"]
    for url in firstQuartile_events:
        report_event(url, "firstQuartile")

    time.sleep(midpoint_time - first_quartile_time)
    midpoint_events = tracking_events["midpoint"]
    for url in midpoint_events:
        report_event(url, "midpoint")


    time.sleep(third_quartile_time - midpoint_time)
    thirdQuartile_events = tracking_events["thirdQuartile"]
    for url in thirdQuartile_events:
        report_event(url, "thirdQuartile")


    time.sleep(complete_time - third_quartile_time)
    complete_events = tracking_events["complete"]
    for url in complete_events:
        report_event(url, "complete")


    # Report errors
    logging.info("")
    logging.info("(+) Reporting Errors: ")
    for url in errors:
        error_code = random.choice(ERROR_CODES)
        logging.info(f"error code used : {str(error_code)}")
        error_report_url = url.replace('[ERRORCODE]', str(error_code))
        report_event(error_report_url, "error")

    logging.info("All events reported")



def parse_vast_xml(xml_string):


    global creative_id_list

    
    # Parse the XML string
    namespaces = {'vast': 'http://www.iab.com/VAST'}
    root = ET.fromstring(xml_string)


    # Extract details
    vast_version = root.get('version')
    logging.info(f"VAST Version: {vast_version}")
    
    for ad in root.findall('vast:Ad', namespaces):
        ad_id = ad.get('id')
        sequence = ad.get('sequence')
        logging.info(f"Ad ID: {ad_id}, Sequence: {sequence}")
        
        for inline in ad.findall('vast:InLine', namespaces):
            ad_system = inline.find('vast:AdSystem', namespaces).text
            ad_system_version = inline.find('vast:AdSystem', namespaces).get('version', 'N/A')
            ad_title = inline.find('vast:AdTitle', namespaces).text
            ad_serving_id = inline.find('vast:AdServingId', namespaces).text
            logging.info(f"Ad System: {ad_system} (version: {ad_system_version})")
            logging.info(f"Ad Title: {ad_title}")
            logging.info(f"Ad Serving ID: {ad_serving_id}")
            
            for impression in inline.findall('vast:Impression', namespaces):
                logging.info(f"Impression: {impression.text}")
            
            for error in inline.findall('vast:Error', namespaces):
                logging.info(f"Error URL: {error.text}")
                
            advertiser = inline.find('vast:Advertiser', namespaces).text
            logging.info(f"Advertiser: {advertiser}")
            
            for creative in inline.findall('vast:Creatives/vast:Creative', namespaces):
                creative_id = creative.get('adId')
                universal_ad_id = creative.find('vast:UniversalAdId', namespaces).text
                logging.info(f"Creative ID: {creative_id}")
                logging.info(f"Universal Ad ID: {universal_ad_id}")
                
                for linear in creative.findall('vast:Linear', namespaces):
                    duration = linear.find('vast:Duration', namespaces).text
                    logging.info(f"Duration: {duration}")
                    
                    for tracking_event in linear.findall('vast:TrackingEvents/vast:Tracking', namespaces):
                        event = tracking_event.get('event')
                        url = tracking_event.text
                        logging.info(f"Tracking Event: {event}, URL: {url}")
                    
                    for mezzanine in linear.findall('vast:MediaFiles/vast:Mezzanine', namespaces):
                        mezzanine_url = mezzanine.text
                        logging.info(f"Mezzanine URL: {mezzanine_url}")
                    
                    for media_file in linear.findall('vast:MediaFiles/vast:MediaFile', namespaces):
                        media_file_id = media_file.get('id')
                        delivery = media_file.get('delivery')
                        width = media_file.get('width')
                        height = media_file.get('height')
                        media_type = media_file.get('type')
                        bitrate = media_file.get('bitrate')
                        scalable = media_file.get('scalable')
                        maintain_aspect_ratio = media_file.get('maintainAspectRatio')
                        url = media_file.text
                        logging.info(f"Media File ID: {media_file_id}")
                        logging.info(f"Delivery: {delivery}")
                        logging.info(f"Dimensions: {width}x{height}")
                        logging.info(f"Type: {media_type}")
                        logging.info(f"Bitrate: {bitrate}")
                        logging.info(f"Scalable: {scalable}")
                        logging.info(f"Maintain Aspect Ratio: {maintain_aspect_ratio}")
                        logging.info(f"URL: {url}")

                if creative_id not in creative_id_list:
                    logging.error(f"Creative ID given in the decision is not downloaded yet")
                    #pprint.pprint(creative_id_list)






def check_discovery_sections(data):
    expected_structure = {
        "decisionServer": {
            "decisionRequestURL": str,
            "preFetchUrl": str,
            "preFetchRefreshRate": int
        },
        "channelList": {
            "channelListUrl": str,
            "channelsRefreshRate": int
        },
        "subscriberInfo": {
            "subscriberInfoUrl": str,
            "subscriberRefreshRate": int
        },
        "reporting": {
            "errorReportUrl": str,
            "debugUrl": str
        }
    }
    
    missing_sections = [section for section in expected_structure if section not in data]
    if missing_sections:
        logging.warning(f"Missing sections: {', '.join(missing_sections)}")
    else:
        logging.info("All expected sections are present.")
        
    for section, members in expected_structure.items():
        if section in data:
            missing_members = [member for member, arg_type in members.items() if member not in data[section] or not isinstance(data[section][member], arg_type)]
            if missing_members:
                logging.warning(f"Missing or invalid members in section '{section}': {', '.join(missing_members)}")
            else:
                logging.info(f"All expected members are present and valid in section '{section}'.")

                # Check macros in decisionServer - decisionRequestURL and preFetchUrl
                if section == "decisionServer":
                    url = data[section].get("decisionRequestURL", "")
                    macros = ["SESSIONID", "SUBSCRIBERID", "DEVICEID", "CHANNELID", "BREAKDURATION", "TRANSACTIONID"]
                    missing_macros = [macro for macro in macros if f"[{macro}]" not in url]
                    if missing_macros:
                        logging.warning(f"Missing macros in decisionRequestURL: {', '.join(missing_macros)}")
                    else:
                        logging.info("All expected macros are present in decisionRequestURL.")
                    
                    pre_fetch_url = data[section].get("preFetchUrl", "")
                    pre_fetch_missing_macros = [macro for macro in ["SUBSCRIBERID", "DEVICEID"] if f"[{macro}]" not in pre_fetch_url]
                    if pre_fetch_missing_macros:
                        logging.warning(f"Missing macros in preFetchUrl: {', '.join(pre_fetch_missing_macros)}")
                    else:
                        logging.info("All expected macros are present in preFetchUrl.")

                # Check macros in subscriberInfo - subscriberInfoUrl
                elif section == "subscriberInfo":
                    subscriber_info_url = data[section].get("subscriberInfoUrl", "")
                    macros = ["CARDID"]  
                    missing_macros = [macro for macro in macros if f"[{macro}]" not in subscriber_info_url]
                    if missing_macros:
                        logging.warning(f"Missing macros in subscriberInfoUrl: {', '.join(missing_macros)}")
                    else:
                        logging.info("All expected macros are present in subscriberInfoUrl.")

def check_channel_list_response(data):
    
    if not isinstance(data, dict):
        logging.error("Channel list response is not a dictionary.")
        return
    
    if "streamToAdResolution" not in data:
        logging.error("Missing 'streamToAdResolution' in response.")
        logging.error("Skipping for now..")
    else:
        logging.info("'streamToAdResolution' found in response.")
        # Validate streamToAdResolution
        stream_to_ad_resolution = data["streamToAdResolution"]
        if not isinstance(stream_to_ad_resolution, dict):
            logging.error("'streamToAdResolution' is not a dictionary.")
        else:
            for key, value in stream_to_ad_resolution.items():
                if not isinstance(value, list):
                    logging.warning(f"Expected list for key '{key}' in 'streamToAdResolution', got {type(value).__name__}.")

    if "channels" not in data:
        logging.error("Missing 'channels' in response.")
        return
    else:
        logging.info("'channels' found in response.")
        # Validate channels
        channels = data["channels"]
        if not isinstance(channels, list):
            logging.error("'channels' is not a list.")
            return

        num_channels = len(channels)
        logging.info("Num of Channels returned: %d", num_channels)
        
        for channel in channels:
            if "channelId" not in channel:
                logging.error(f"Missing 'channelId' in a channel. Channel details: {json.dumps(channel, indent=4)}")
                continue
            else:
                logging.info(f"Channel ID: {channel['channelId']}")

            if "deliveries" not in channel:
                logging.error("Missing 'deliveries' in a channel.")
                continue
            else:
                deliveries = channel["deliveries"]
                if not isinstance(deliveries, list):
                    logging.error(f"'deliveries' for channel '{channel.get('channelId', 'unknown')}' is not a list.")
                    continue
                else:
                    for delivery in deliveries:
                        if "deliveryType" not in delivery:
                            logging.error(f"Missing 'deliveryType' in a delivery for channel '{channel.get('channelId', 'unknown')}'.")
                            continue
                        else:
                            logging.info(f"deliveryType: {delivery['deliveryType']}")

                        if "deliveryIdentifiers" not in delivery:
                            logging.error(f"Missing 'deliveryIdentifiers' in a delivery for channel '{channel.get('channelId', 'unknown')}'.")
                            continue
                        
                        delivery_identifiers = delivery["deliveryIdentifiers"]
                        expected_keys = ["onId", "tsId", "serviceId"]
                        all_present = True

                        for key in expected_keys:
                            if key not in delivery_identifiers:
                                logging.error(f"Missing '{key}' in 'deliveryIdentifiers' for channel '{channel.get('channelId', 'unknown')}'.")
                                all_present = False
                            else:
                                logging.info(f"Key '{key}' with value '{delivery_identifiers[key]}' is present in 'deliveryIdentifiers' for channel '{channel['channelId']}'")

                        if all_present:
                            onId = delivery_identifiers["onId"]
                            tsId = delivery_identifiers["tsId"]
                            serviceId = delivery_identifiers["serviceId"]
                            logging.info(f"All expected keys are present in 'deliveryIdentifiers' for channel '{channel['channelId']}': onId={onId}, tsId={tsId}, serviceId={serviceId}")


def check_subs_info_response(data):
    if not isinstance(data, dict):
        logging.error("Subscriber info response is not a dictionary.")
        return
    
    expected_keys = ["subscriberId", "irisEnabled"]
    for key in expected_keys:
        if key not in data:
            logging.error(f"Missing '{key}' in subscriber info response.")
        else:
            logging.info(f"Key '{key}' is present in subscriber info response with value '{data[key]}'.")

    # Additional checks if needed
    if "subscriberId" in data and not isinstance(data["subscriberId"], str):
        logging.error("Expected 'subscriberId' to be a string.")



    if "irisEnabled" in data and not isinstance(data["irisEnabled"], bool):
        logging.error("Expected 'irisEnabled' to be a boolean.")


def download_file(url, local_filename, full_file_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(full_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Downloaded file '{local_filename}' from URL '{url}'.")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download file '{local_filename}' from URL '{url}': {e}")
        return False


def get_media_info(file_path):
    try:
        media_info = MediaInfo.parse(file_path)
        
        if not media_info:
            raise ValueError("Failed to parse media info")

        details = {}

        # General info
        general = media_info.general_tracks[0] if media_info.general_tracks else None
        if general:
            general_info = {
                "Complete name": getattr(general, 'complete_name', None),
                "Format": getattr(general, 'format', None),
                "File size": general.other_file_size[0] if hasattr(general, 'other_file_size') and general.other_file_size else None,
                "Duration": general.other_duration[0] if hasattr(general, 'other_duration') and general.other_duration else None,
                "Overall bit rate mode": getattr(general, 'overall_bit_rate_mode', None),
                "Overall bit rate": general.other_overall_bit_rate[0] if hasattr(general, 'other_overall_bit_rate') and general.other_overall_bit_rate else None,
            }
            details["General"] = {k: v for k, v in general_info.items() if v is not None}
        else:
            details["General"] = {}

        # Track-specific info
        details["Tracks"] = []
        audio_count = 0
        for track in media_info.tracks:
            if track.track_type == "Video":

                '''
                #enable it fo find out all the info in the track
                print("Track info:")
                track_attributes = track.__dict__
                for attr_name, attr_value in track_attributes.items():
                    print(f"{attr_name}: {attr_value}")
                print()
                '''


                track_info = {
                    "Channel": getattr(track, 'stream_identifier', None),
                    "Format": getattr(track, 'format', None),
                    "Format/Info": getattr(track, 'format_info', None),
                    "Format profile": getattr(track, 'format_profile', None),
                    "Format settings": getattr(track, 'format_settings', None),
                    "Format settings, CABAC": getattr(track, 'format_settings_cabac', None),
                    "Format settings, Reference frames": getattr(track, 'format_settings_reference_frames', None),
                    "Format settings, GOP": getattr(track, 'format_settings_gop', None),
                    "Codec ID": getattr(track, 'codec_id', None),
                    "Duration": track.other_duration[0] if hasattr(track, 'other_duration') and track.other_duration else None,
                    "Width": getattr(track, 'width', None),
                    "Height": getattr(track, 'height', None),
                    "Display aspect ratio": getattr(track, 'display_aspect_ratio', None),
                    "Active Format Description": getattr(track, 'active_format_description', None),
                    "Frame rate": track.other_frame_rate[0] if hasattr(track, 'other_frame_rate') and track.other_frame_rate else None,
                    "Standard": getattr(track, 'standard', None),
                    "Color space": getattr(track, 'color_space', None),
                    "Chroma subsampling": getattr(track, 'chroma_subsampling', None),
                    "Bit depth": getattr(track, 'bit_depth', None),
                    "Scan type": getattr(track, 'scan_type', None),
                    "Scan type, store method": getattr(track, 'scan_type_store_method', None),
                    "Scan order": getattr(track, 'scan_order', None),
                    "Color range": getattr(track, 'color_range', None),
                    "Color primaries": getattr(track, 'color_primaries', None),
                    "Transfer characteristics": getattr(track, 'transfer_characteristics', None),
                    "Matrix coefficients": getattr(track, 'matrix_coefficients', None),
                }
                track_info = {k: v for k, v in track_info.items() if v is not None}
                details["Tracks"].append(("Video", track_info))
            elif track.track_type == "Audio":
                audio_count += 1
                track_info = {
                    "ID": getattr(track, 'stream_identifier', None) or f"257 (0x{100 + audio_count:02X})",
                    "Menu ID": getattr(track, 'menu_id', None) or "1 (0x1)",
                    "Format": getattr(track, 'format', None),
                    "Format/Info": getattr(track, 'format_info', None),
                    "Codec ID": getattr(track, 'codec_id', None),
                    "Duration": track.other_duration[0] if hasattr(track, 'other_duration') and track.other_duration else None,
                    "Bit rate": track.other_bit_rate[0] if hasattr(track, 'other_bit_rate') and track.other_bit_rate else None,
                    "Channel(s)": getattr(track, 'channel_s', None),
                    "Channel layout": getattr(track, 'channel_layout', None),
                    "Sampling rate": getattr(track, 'sampling_rate', None),
                    "Frame rate": getattr(track, 'frame_rate', None),
                    "Compression mode": getattr(track, 'compression_mode', None),
                    "Delay relative to video": track.other_delay_relative_to_video[0] if hasattr(track, 'other_delay_relative_to_video') and track.other_delay_relative_to_video else None,
                    "Stream size": track.other_stream_size[0] if hasattr(track, 'other_stream_size') and track.other_stream_size else None,
                    "Language": getattr(track, 'language', None),
                    "Service kind": getattr(track, 'service_kind', None),
                    "Dialog Normalization": getattr(track, 'dialog_normalization', None),
                }
                track_info = {k: v for k, v in track_info.items() if v is not None}
                details["Tracks"].append((f"Audio #{audio_count}", track_info))
            elif track.track_type == "Menu":
                track_info = {
                    "ID": getattr(track, 'stream_identifier', None),
                    "Menu ID": getattr(track, 'menu_id', None),
                    "Format": getattr(track, 'format', None),
                    "Duration": track.other_duration[0] if hasattr(track, 'other_duration') and track.other_duration else None,
                    "List": getattr(track, 'list', None),
                    "Language": getattr(track, 'language', None),
                    "Service name": getattr(track, 'service_name', None),
                    "Service provider": getattr(track, 'service_provider', None),
                    "Service type": getattr(track, 'service_type', None),
                }
                track_info = {k: v for k, v in track_info.items() if v is not None}
                details["Tracks"].append(("Menu", track_info))

        return details

    except Exception as e:
        logging.error(f"Error retrieving media info: {e}")
        return None




def check_prefetch_response(data):
    global SHOW_MEDIA_INFO_DETAILS
    global creative_id_list


    if not isinstance(data, dict):
        logging.error("Prefetch response is not a dictionary.")
        return
    
    if "creatives" not in data:
        logging.error("Missing 'creatives' in prefetch response.")
        return
    
    creatives = data["creatives"]
    if not isinstance(creatives, list):
        logging.error("'creatives' is not a list.")
        return


    
    for creative in creatives:

        if "creativeId" not in creative:
            logging.error(f"Missing 'creativeId' in a creative. Creative details: {json.dumps(creative, indent=4)}")
            continue
        else:
            logging.info(f"Creative ID: {creative['creativeId']}")

        if "duration" not in creative:
            logging.error(f"Missing 'duration' in a creative. Creative ID: {creative['creativeId']}")
            continue
        else:
            logging.info(f"Duration: {creative['duration']}")

        if "instances" not in creative:
            logging.error(f"Missing 'instances' in a creative. Creative ID: {creative['creativeId']}")
            continue
        
        instances = creative["instances"]
        if not isinstance(instances, list):
            logging.error(f"'instances' for creative '{creative['creativeId']}' is not a list.")
            continue
        
        for instance in instances:
            if "mediaType" not in instance:
                logging.error(f"Missing 'mediaType' in an instance for creative '{creative['creativeId']}'.")
                continue
            else:
                logging.info(f"Media Type: {instance['mediaType']}")

            if "url" not in instance:
                logging.error(f"Missing 'url' in an instance for creative '{creative['creativeId']}'.")
                continue
            else:
                logging.info(f"URL: {instance['url']}")


            if SHOW_MEDIA_INFO_DETAILS:

                local_filename = str(creative['creativeId']) + '_' + instance['url'].split('/')[-1]

                script_dir = os.path.dirname(os.path.abspath(__file__))
                ts_files_dir = os.path.join(script_dir, ts_files_folder_name)
                os.makedirs(ts_files_dir, exist_ok=True)

                full_file_path = os.path.join(ts_files_dir, local_filename)
                
                if download_file(instance['url'], local_filename, full_file_path):
                    #media_info = get_media_info(local_filename)
                    media_info = get_media_info(full_file_path)

                    if media_info:
                        # Log General Info
                        logging.info("General")
                        for key, value in media_info["General"].items():
                            logging.info(f"{key:<40}: {value}")
                        logging.info("")

                        # Log Track Info
                        for track_type, track in media_info["Tracks"]:
                            logging.info(f"{track_type}")
                            for key, value in track.items():
                                logging.info(f"{key:<40}: {value}")
                            logging.info("----")
                    else:
                        logging.error("Failed to retrieve media info")

        if creative['creativeId'] not in creative_id_list:
            creative_id_list.append(creative['creativeId'])




def main(endpoint, card_id, device_id):

    # Global instance
    global discovery_url_object
    global prefetch_repeat_count
    global decision_repeat_count
    global discovery_url_object


    discovery_url_object = DiscoveryURLs(card_id, device_id)

    logging.info("-----------------------------")
    logging.info(" Checking Discovery service ")
    logging.info("-----------------------------")

    
    if endpoint == "prod":
        tenant_id = 'osmwqc5f'
        discovery_url = f"https://client-discovery-apb.iris.synamedia.com/{tenant_id}/discovery.json"
    elif endpoint == "int":
        tenant_id = 'ora90src'
        discovery_url = f"https://client-discovery-eu3.infinite-insights-net.com/{tenant_id}/discovery.json"
    elif endpoint == "demo":
        tenant_id = 'kxddtl5a'
        discovery_url = f"https://client-discovery-eu3.infinite-insights-net.com/{tenant_id}/discovery.json"
    elif endpoint == "eu5":
        tenant_id = 'kxddtl5a'
        discovery_url = f"https://client-discovery-eu5.infinite-insights-net.com/{tenant_id}/discovery.json"
    else:
        logging.error("Invalid endpoint specified. Use 'prod' or 'int' or 'demo' or 'eu5'.")
        return

    logging.info("(+) Discovery URL: '%s'", discovery_url)
    discovery_sections_data = fetch_url_data(discovery_url)

    if enable_check_services:
        if discovery_sections_data:
            logging.info("(+) Check Discovery service return params:")
            check_discovery_sections(discovery_sections_data)
            discovery_url_object.set_urls(discovery_sections_data)
            logging.info(f"Decision Request URL: {discovery_url_object.get_decisionRequestURL()}")
            logging.info(f"Pre-Fetch URL: {discovery_url_object.get_preFetchUrl()}")
            logging.info(f"Channel List URL: {discovery_url_object.get_channelListUrl()}")
            logging.info(f"Subscriber Info URL: {discovery_url_object.get_subscriberInfoUrl()}")
            logging.info(f"Error Report URL: {discovery_url_object.get_errorReportUrl()}")
            logging.info(f"Debug URL: {discovery_url_object.get_debugUrl()}")
    else:
        if discovery_sections_data:
            discovery_url_object.set_urls(discovery_sections_data)


    logging.info("")
    logging.info("-----------------------------")
    logging.info(" Checking Identity/Subscriber Service ")
    logging.info("-----------------------------")
    subs_info_url = discovery_url_object.get_subscriberInfoUrl()
    #subs_info_url = "http://iris-vast.iris.synamedia.com/vast_ad_simulator_new/subscribers/cardId_190.json"
    logging.info("(+) Subscriber Service URL: '%s'", subs_info_url)
    subs_info_data = fetch_url_data(subs_info_url)
    try:
        discovery_url_object.set_subscriberID(subs_info_data["subscriberId"])
    except:
        pass

    if enable_check_services:
        if subs_info_data:
            logging.info("(+) Check Subscriber service return params:")
            check_subs_info_response(subs_info_data)



    logging.info("")
    logging.info("-----------------------------")
    logging.info(" Checking Channel List service ")
    logging.info("-----------------------------")
    channel_list_url = discovery_url_object.get_channelListUrl()
    logging.info("(+) Channel List URL: '%s'", channel_list_url)
    channel_list_data = fetch_url_data(channel_list_url)

    if enable_check_services:
        if channel_list_data:
            logging.info("(+) Check Channel List service return params:")
            check_channel_list_response(channel_list_data)


    sessionID = 7654
    channelID = "Spare_4512"
    duration = '00:00:30'
    durations = ['00:00:10', '00:00:15', '00:00:20', '00:00:30', '00:00:45', '00:01:00']
    breakTime = 5000
    breakMaxAds = 2
    transactionID = 1

    for i in range(prefetch_repeat_count):

        logging.info("")
        logging.info("-----------------------------")
        logging.info(" Checking Prefetch service ")
        logging.info("-----------------------------")
        preFetch_url = discovery_url_object.get_preFetchUrl()
        logging.info("(+) Prefetch URL: '%s'", preFetch_url)
        prefetch_data = fetch_url_data(preFetch_url)
        logging.info("Num of Creatives returned: %d", len(prefetch_data["creatives"]))

        if enable_check_services or SHOW_MEDIA_INFO_DETAILS:
            if prefetch_data:
                logging.info("(+) Check Prefetch service return params:")
                check_prefetch_response(prefetch_data)


        for j in range(decision_repeat_count):

            #utc_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            utc_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

            logging.info("")
            logging.info(f"UTC Time: {utc_time}")
            logging.info("-----------------------------")
            logging.info(" Checking Ad Decision service ")
            logging.info("-----------------------------")
            decisionRequest_url = discovery_url_object.get_decisionRequestURL()

            new_decisionRequest_url = decisionRequest_url.replace('[SESSIONID]', str(sessionID))
            new_decisionRequest_url = new_decisionRequest_url.replace('[CHANNELID]', str(channelID))
            new_decisionRequest_url = new_decisionRequest_url.replace('[BREAKDURATION]', duration)
            #new_decisionRequest_url = new_decisionRequest_url.replace('[BREAKDURATION]', random.choice(durations))
            
            new_decisionRequest_url = new_decisionRequest_url.replace('[TRANSACTIONID]', str(transactionID))
            new_decisionRequest_url = new_decisionRequest_url.replace('[BREAKTIME]', str(breakTime))
            new_decisionRequest_url = new_decisionRequest_url.replace('[BREAKMAXADS]', str(breakMaxAds))
            logging.info("(+) Decision Request URL: '%s'", new_decisionRequest_url)
            decisionRequest_data = fetch_url_data(new_decisionRequest_url, True)

            if enable_check_services:
                if decisionRequest_data:
                    parse_vast_xml(decisionRequest_data)

            if REPORTING_ENABLED:
                performReport(decisionRequest_data)

            if ( (j+1) != decision_repeat_count):
                time.sleep(2)
                transactionID = transactionID + 1



        if ( (i+1) != prefetch_repeat_count):
            time.sleep(5)
            sessionID = sessionID + 1

    print(ts_files_folder_name)
    



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Discovery Service Checker', 
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-ep', '--endpoint', nargs='?', default='int', choices=['prod', 'int', 'demo', 'eu5'], 
                        help='Specify the endpoint as either "prod" or "int" or "demo" or "eu5" (default is "eu3")')
    parser.add_argument('-c', '--cardID', required=True, 
                        help='Specify the card ID (mandatory)')
    parser.add_argument('-d', '--deviceID', 
                        help='Specify the device ID (optional)')
    parser.add_argument('-s', '--show_media_info_details', action='store_true', 
                        help='Set to show media info details (default is False)')
    parser.add_argument('-l', '--loglevel', default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level (default is INFO)')
    
    args = parser.parse_args()

    logging_level = getattr(logging, args.loglevel.upper(), logging.INFO)
    logging.basicConfig(level=logging_level, format='%(asctime)s - %(levelname)s - %(message)s')

    SHOW_MEDIA_INFO_DETAILS = args.show_media_info_details

    try:
        main(args.endpoint, args.cardID, args.deviceID)
    except Exception as e:
        print(f"Error occurred while running checkServices.py: {e}")
        sys.exit(1)
