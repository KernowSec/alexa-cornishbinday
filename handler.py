# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils
import requests
import datetime
import json
import re

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

from ask_sdk_model.ui import AskForPermissionsConsentCard

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)



# Customisable bits
#get address

def getAddress(device_id, endpoint, token):

    address_api = "{}/v1/devices/{}/settings/address".format(endpoint, device_id)
    
    response = requests.get(address_api, headers={"Authorization": "Bearer {}".format(token)})
    print(response)
    print(response.status_code)
    print(response.json())
    return response



def getHouseUPRN(house_ident, postcode):
    
    #number or name?
    
    try:
        val = int(house_ident)
        isnumber = True
    except ValueError:
        isnumber = False
    
    pattern = re.compile(r'<option value=\"(\d{12})\">(.+?)<\/option>', re.DOTALL)

    url1 = 'https://www.cornwall.gov.uk/my-area/?Postcode={}'.format(postcode)
    
    response1 = requests.get(url1)
    
    matches = re.findall(pattern, response1.text)
    
    housenumberregex = re.compile(r'^(\d{1,5})..', re.DOTALL)
    if isnumber == True:
        for match in matches:
            matched_house_number = re.findall(housenumberregex, match[1])
            if house_ident == matched_house_number[0]:
                uprn = match[0]
                address = match[1]
                print("UPRN: {}".format(uprn))
                print("Address: {}".format(address))
                
                return uprn
    elif isnumber == False:
        length = len(house_ident)
        for match in matches:
            if house_ident.lower() == match[1][0:length].lower():
                uprn = match[0]
                address = match[1]
                print("UPRN: {}".format(uprn))
                print("Address: {}".format(address))

                return uprn
                
    else:
        print("Cant evaluate address, aborting...")
        system.exit()
        

def get_bin_day(uprn, postcode):
    
    pattern2 = re.compile(r'<span>(Household)</span>.+?<span>(.+?)</span>.+?<span>(.+?)</span.+?<span>(Recycling)</span>.+?<span>(.+?)</span>.+?<span>(.+?)</span>', re.DOTALL)

    url2 = 'https://www.cornwall.gov.uk/umbraco/Surface/Waste/MyCollectionDays?uprn={}&url=https%3A%2F%2Fwww.cornwall.gov.uk%2Fmy-area%2F%3FPostcode%3D{}%26Uprn%3D{}&subscribe=False'.format(uprn, postcode, uprn)

    response2 = requests.get(url2)
    
    matches = re.findall(pattern2, response2.text)

    for match in matches:
        if match[0] == 'Household':
            print(match[0])
            print(match[1], match[2])
            returnStringHousehold = "Your {} is on {} {}".format(match[0], match[1], match[2])
        if match[3] == 'Recycling':
            print(match[3])
            print(match[4],  match[5])
            returnStringRecycling = "Your {} is on {} {}".format(match[3], match[4], match[5])
        
    if returnStringHousehold != "" and returnStringRecycling != "":
        return returnStringHousehold + " and " + returnStringRecycling
    else:
        return "Error, cannot find your address. Are you sure you live in Cornwall?"



class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome, you can say when or summary to find out info about your bin day."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

#write handlers code below?

class SummaryIntentHandler(AbstractRequestHandler):
    """Handler for Summary Intent"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("SummaryIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #declare vars
        device_id = ask_utils.request_util.get_device_id(handler_input)
        print(device_id)
        
        token = ask_utils.request_util.get_api_access_token(handler_input)
        print(token)
        
        endpoint = "https://api.eu.amazonalexa.com"
        
        addr_response = getAddress(device_id, endpoint, token)
        
        if addr_response.status_code == 403:
            speak_output = "Error, please provide permissions for device address in settings"

            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .set_card(AskForPermissionsConsentCard(['read::alexa:device:all:address']))
                    # .ask("add a reprompt if you want to keep the session open for the user to respond")
                    .response
            )
        
        if addr_response.status_code == 200:
            
            isCornwall = False
            
            address = addr_response.json()
            
            if address['stateOrRegion'].lower() == "cornwall":
                isCornwall = True
                
            if not isCornwall:
                for element in address:
                    try:
                        #print(address[element])
                        if address[element].lower() != "cornwall":
                            isCornwall = False

                        if address[element].lower() ==  "cornwall":
                            isCornwall = True
                            break
                    except AttributeError:
                        pass
                    
                if not isCornwall:

                    return (
                    handler_input.response_builder
                        .speak(speak_output)
                        # .ask("add a reprompt if you want to keep the session open for the user to respond")
                        .response
                )
                
            
            line1 = address['addressLine1']
            postcode = address['postalCode']
            uprn = getHouseUPRN(line1, postcode)
            
            speak_output = get_bin_day(uprn, postcode)
            
            
            
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    # .ask("add a reprompt if you want to keep the session open for the user to respond")
                    .response
            )


###

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say summary or when, to find out when your bins and recycling are."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        LOGGER.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
#custom below
sb.add_request_handler(SummaryIntentHandler())
#
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
