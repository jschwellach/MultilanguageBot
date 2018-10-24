#!/usr/bin/python
# coding=utf-8

import json
import boto3
import random

BOT_NAME = "OrderFlowers"
BOT_ALIAS = "LATEST"

def translateBot(local_message, userid):
	"""
	Calls the Lex bot, with bidirectional translation to/from the language of the message. 
	"""
	print("translating local_message: " + local_message)
	comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')
	language = comprehend.detect_dominant_language(Text=local_message)["Languages"][0]["LanguageCode"]
	translate = boto3.client(service_name='translate', region_name='us-east-1')
	translated_message = translate.translate_text(Text=local_message, SourceLanguageCode=language, TargetLanguageCode="en")
	lex = boto3.client(service_name='lex-runtime', region_name='us-east-1')
	en_response = lex.post_text(botName=BOT_NAME, botAlias=BOT_ALIAS, userId=userid, inputText=translated_message['TranslatedText'])
	# check presence of "message" field to see if there is a dialog or if its the final confirmation. 
	if "message" in en_response:
		en_response = en_response.get("message")
		local_response = translate.translate_text(Text=en_response, SourceLanguageCode="en", TargetLanguageCode=language).get('TranslatedText')
		return {
			"local_message": local_message,
			"en_message": translated_message['TranslatedText'],
			"en_response": en_response,
			"local_response": local_response,
			"local_language": language
		}
	else:
		return { 
			"confirmation": en_response 
		}

def lambda_handler(event, context):
    botResponse = translateBot( intent=event["intent"], userid=event["userid"] )
    return {
        "statusCode": 200,
        "body": botResponse
    }

def run_test():
	userid = "user" + str(random.randint(1,9999)).zfill(4)

	local_message = "我想订花"	
	botResponse = translateBot(local_message=local_message, userid=userid)
	print(json.dumps(botResponse, ensure_ascii=False, encoding="UTF8"))
	assert botResponse["en_response"] == "What type of flowers would you like to order?"

	local_message = "玫瑰花"
	botResponse = translateBot(local_message=local_message, userid=userid)
	print(json.dumps(botResponse, ensure_ascii=False, encoding="UTF8"))
	assert "What day do you want" in botResponse["en_response"] 

	local_message = "星期五"
	botResponse = translateBot(local_message=local_message, userid=userid)
	print(json.dumps(botResponse, ensure_ascii=False, encoding="UTF8"))
	assert "what time" in botResponse["en_response"] 

	local_message = "早晨九点"
	botResponse = translateBot(local_message=local_message, userid=userid)
	print(json.dumps(botResponse, ensure_ascii=False, encoding="UTF8"))
	assert "Does this sound okay" in botResponse["en_response"]

	local_message = "好的"
	botResponse = translateBot(local_message=local_message, userid=userid)
	print(json.dumps(botResponse, ensure_ascii=False, encoding="UTF8"))
	assert botResponse["confirmation"]["slots"]["FlowerType"] == "Rose"

if __name__ == '__main__':
	run_test()