from __future__ import print_function
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
import random
from random import randint 


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    # speech_output = os.environ["GREETING_MSG"]
    speech_output = "Welcome to mansplaining facts skill"
    reprompt_text = "To hear available stats, ask what stats are available"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = os.environ["EXIT_MSG"]
    # Setting this to true ends the session and exits the skill.
    should_end_session = False
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def query_dynamodb_stat(table, stat):
    try:
        response = table.get_item(
            Key={'name': stat}
        )
    except KeyError:
        return -1
    except Exception:
        return -1
    return response['Item']['count']

def get_mansplaining_fact(table, intent, session):
    print("Into get_mansplaining_fact")
    session_attributes = {}
    reprompt_text = "Sorry, I didn't understand. Please ask again"
    try:
        print("table is ", table)

        # Get the count of mansplaining facts
        response = table.query(
            KeyConditionExpression=Key('fact-type').eq('MansplainingFact')
        )
        items = response['Items']

        count = 0
        count = len(items);
        print("Number of mansplaining facts ", count)

        # Select a random fact
        random_fact_number = randint(1, count)
        response = table.get_item(
            Key={'fact-type': 'MansplainingFact', 'fact-number': str(random_fact_number)}
        )

        print("response is ", response)
    except Exception as e:
        # speech_output = os.environ["EXCEPTION_MSG"]
        print("Exception occured. ", e)
        speech_output = "I'm sorry, I did not understand the request. Please ask again."
        should_end_session = False

    fact = response['Item']['analysis']
    category = response['Item']['meeting-category']
    if fact:
        speech_output = "Analysis of a meeting in the " + category + " category reveals that " + fact
        should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(table, session_started_request, session):
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(table, launch_request, session):
    return get_welcome_response()


def on_intent(table, intent_request, session):
    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    print("intent_name : ", intent_name)

    # Dispatch to your skill's intent handlers
    if intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    elif intent_name.upper() == "GETFACTSINTENT":
        return get_mansplaining_fact(table, intent, session)
    else:
        reprompt_text = "Sorry, I didn't understand. Please try again."
        should_end_session = False


def on_session_ended(table, session_ended_request, session):
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])


# --------------- Main handler ------------------

def lambda_handler(event, context):
    print(event)

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    indexEndRegion = context.invoked_function_arn[15:30].find(":") + 15
    region = context.invoked_function_arn[15:indexEndRegion]
    dynamodb = boto3.resource('dynamodb', region_name=region,
                              endpoint_url="https://dynamodb." + region + ".amazonaws.com")

    table = os.environ['MansplainingDynamoDB']
    stats_table = dynamodb.Table(table)

    try:
        if event['session']['new']:
            on_session_started(stats_table, {'requestId': event['request']['requestId']}, event['session'])
    except KeyError:
        print("Message")
    if event['request']['type'] == "LaunchRequest":
        print("launching")
        return on_launch(stats_table, event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        print("calling an intent")
        return on_intent(stats_table, event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        print("Session End Requested")
        return on_session_ended(stats_table, event['request'], event['session'])