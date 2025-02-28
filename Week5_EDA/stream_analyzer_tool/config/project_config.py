#############################################################################
#  Copyright (c) 2021  : Synamedia Ltd
#
#  P R O P R I E T A R Y    &    C O N F I D E N T I A L
#
#  The copyright of this document is vested in Synamedia Ltd. without
#  whose prior written permission its contents must not be published,adapted
#  or reproduced in any form or disclosed or issued to any third party.
#  ##########################################################################
#
#  File Name    : project_config.py
#  Version      :
#  Type of file : python script
#  Description  : Configuration script
#
##############################################################################

global project_name
global enable_debugs
global allowed_ad_duration
global project_spec_json

project_name = "astro" # Ex: astro, osn, bein,...

allowed_ad_duration = [10,15,20,30,45,60] # standard AD duration in secs

enable_debugs = {
    "PAT": False,
    "PMT": False,
    "SCTE": True
}

project_spec_json = {
    "astro" : "config_astro.json",
    "osn" : "config_osn.json",
    "bein" : "config_bein.json"
}
