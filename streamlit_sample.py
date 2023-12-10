import streamlit as st
import numpy as np
import openai
from datetime import datetime, date
import time

openai.api_key = "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"

def gpt3_completion(prompt, engine='text-davinci-003', temp=0.0, top_p=1.0, tokens=400, freq_pen=0.0, pres_pen=0.0, stop=['USER:', 'ASKUNA:']):
    max_retry = 5
    retry = 0
    prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
    while True:
        try:
            response = openai.Completion.create(
                engine=engine,
                prompt=prompt,
                temperature=temp,
                max_tokens=tokens,
                top_p=top_p,
                frequency_penalty=freq_pen,
                presence_penalty=pres_pen,
                stop=stop)
            text = response['choices'][0]['text'].strip()
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return "GPT3 error: %s" % oops
            print('Error communicating with OpenAI:', oops)


private_data='''"Scope3":{"FUEL GENRATION": {"CNG":[{"CO2e":carbon_factor_value":0.09487 kg  per litres, "Country":"UK"}],
                                    "Propane":[{"CO2e":carbon_factor_value":0.18046 kg per litres, "Country":"UK"}],
                                    "butane  (100% mineral petrol)":[{"CO2e":carbon_factor_value":0.60283 kg per litres, "Country":"UK"}],
                                    "Renewable Petrol litres":[{"CO2e":carbon_factor_value":0.57907 kg per litres, "Country":"UK"}],
                                    "Diesel (100% mineral diesel)":[{"CO2e":carbon_factor_value":0.62874 kg per litres, "Country":"UK"}],
                                    "LPG ":[{"CO2e":carbon_factor_value":0.18383 kg per litres, "Country":"UK"}],
                                    "LNG":[{"CO2e":carbon_factor_value":0.39925 kg per litres, "Country":"UK"}],
                                    "Petrol (average biofuel blend)":[{"CO2e":carbon_factor_value":0.61328 kg per litres, "Country":"UK"}],
                                    "Butane":[{"CO2e":carbon_factor_value":0.19686 kg per litres, "Country":"UK"}],
                                    "Processed fuel oils - distillate oil":[{"CO2e":carbon_factor_value":0.70791 kg per litres, "Country":"UK"}],
                                    "Diesel (average biofuel blend)":[{"CO2e":carbon_factor_value":0.60986 kg per litres, "Country":"UK"}],
                                    "Fuel Oil":[{"CO2e":carbon_factor_value":0.69723 kg per litres, "Country":"UK"}],
                                    "Gas Oil":[{"CO2e":carbon_factor_value":0.63253 kg per litres, "Country":"UK"}],
                                    "Other Petroleum Gas":[{"CO2e":carbon_factor_value":0.11154 kg per litres, "Country":"UK"}],
                                    "Marine fuel oil":[{"CO2e":carbon_factor_value":0.69723 kg per litres, "Country":"UK"}],
                                    "Marine gas  oil":[{"CO2e":carbon_factor_value":0.63253 kg per litres, "Country":"UK"}],
                                    "Processed fuel oils - residual oil":[{"CO2e":carbon_factor_value":0.82185 kg per litres, "Country":"UK"}],
                                    "Aviation Turbine Fuel":[{"CO2e":carbon_factor_value":0.52686kg per litres, "Country":"UK"}],
                                    "Aviation Spirit litres ":[{"CO2e":carbon_factor_value":0.59512 kg per litres, "Country":"UK"}],
                                    "Bio Petrol":[{"CO2e":carbon_factor_value":0.2981 kg per litres, "Country":"UK"}],
                                    "Bioethanol":[{"CO2e":carbon_factor_value":0.54488 kg per litres, "Country":"UK"}],
                                    "Biopropane":[{"CO2e":carbon_factor_value":0.2907 kg per litres, "Country":"UK"}],
                                    "Bio Petrol":[{"CO2e":carbon_factor_value":0.52807 kg per litres, "Country":"UK"}],
                                    "Burning Oil":[{"CO2e":carbon_factor_value":0.2981 kg per litres, "Country":"UK"}]},


                "TRAVEL":{ "CAR":[{"CO2e":carbon_factor_value":0.05477 kg per km, "Country":"UK"}]},
                        { "Black cab":[{"CO2e":carbon_factor_value":0.30624 kg per km, "Country":"UK"}]},
                        { "Regular taxi":[{"CO2e":carbon_factor_value":0.20826 kg per km, "Country":"UK"}]},
                        { "EV_CAR":[{"CO2e":carbon_factor_value":0.19338 kg per kwh, "Country":"UK"}]}'''

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()
    
intro = open_file('finalbot_intro_prompt.txt').replace('<<PRIAVATE_DATASET>>', private_data)
intro = intro.encode(encoding='ASCII',errors='ignore').decode()

DBconv_dict =  {}

dbconv_track =  {'start_time':datetime, 'conversation':[]}

DBconv_dict["user_id"] = dbconv_track

DBconv_dict["user_id"]['start_time'] =  datetime.fromtimestamp(time.time())          
DBconv_dict["user_id"]['end_time']= datetime.fromtimestamp(time.time())
DBconv_dict["user_id"]['date_t']= date.today()
DBconv_dict["user_id"]['update_count'] = 0

uDict = {
    "user_id": {
        "count": 0,
        "conv_count": 0,
        "conversation": []
    }
}

def triggertheflow(message):
    uDict["user_id"]['conversation'].append({'role': 'system', 'content': intro})
    DBconv_dict["user_id"]['conversation'].append({'question': message})
    uDict["user_id"]['conversation'].append({'role': 'user', 'content': message})
    DBconv_dict["user_id"]['conversation'].append({'question': message})
    print(message)
    classify_prompt =  open_file('n_prompt.txt').replace('<<QUESTION>', message)
    ans = gpt3_completion(classify_prompt)
    assumption_prompt =  open_file('assumption_prompt.txt').replace('<<USER_QUESTION>>', message)
    assumption_prompt = assumption_prompt.encode(encoding='ASCII',errors='ignore').decode()
    response = openai.Completion.create(
                                    model='text-davinci-003',
                                    prompt=assumption_prompt,
                                    top_p=0.1,
                                    max_tokens = 400,
                                    temperature=0.7,
                                    stop=['USER:', 'ASKUNA:'],
                                    stream=True,  # this time, we set stream=True
                                )
    final_reply = generate(response)
    return final_reply
    

def generate(response):
    text = ''
    for chunk in response:
        chunk_message = chunk['choices'][0]['text']    
        # chunk_message.get('content', '')
        text+= chunk_message.replace('\n','$$$')
        # yield f"data:  {text}\n\n"
    return text

