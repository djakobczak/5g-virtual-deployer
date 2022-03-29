from copy import deepcopy
from pymongo import MongoClient


# IMSI = [MCC|MNC|MSISDN]
MCC = '001'
MNC = '01'
MSISDN_LENGTH = 10
IMSI = '{MCC}{MNC}{MSISDN}'
CONNECTION_STRING = "mongodb://localhost:27017/"

SUBSCRIBER_TEMPALTE = {
    "imsi": "001010000000001",
    "subscribed_rau_tau_timer": 12,
    "network_access_mode": 0,
    "subscriber_status": 0,
    "access_restriction_data": 32,
    "slice": [
        {
            "sst": 1,
            "default_indicator": True,
            "session": [
                {
                    "name": "internet1",
                    "type": 3,
                    "pcc_rule": [],
                    "ambr": {
                        "uplink": {
                            "value": 1,
                            "unit": 3
                        },
                        "downlink": {
                            "value": 1,
                            "unit": 3
                        }
                    },
                    "qos": {
                        "index": 9,
                        "arp": {
                            "priority_level": 8,
                            "pre_emption_capability": 1,
                            "pre_emption_vulnerability": 1
                        }
                    }
                }
            ]
        }
    ],
    "ambr": {
        "uplink": {
            "value": 1,
            "unit": 3
        },
        "downlink": {
            "value": 1,
            "unit": 3
        }
    },
    "security": {
        "k": "465B5CE8B199B49FAA5F0A2EE238A6BC",
        "amf": "8000",
        "op": None,
        "opc": "E8ED289DEBA952E4283B54E88E6183CA",
        "sqn": 161
    },
    "msisdn": []
}


client = MongoClient(CONNECTION_STRING)
db = client.open5gs
subsribers_collection = db.subscribers


def delete_subscriber(imsi: str):
    query = {'imsi': imsi}
    res = subsribers_collection.delete_many(query)
    print(res.deleted_count, " documents deleted.")


def delete_all_subscribers():
    print('Delete all subscribers...')
    res = subsribers_collection.delete_many({})
    print(res.deleted_count, " documents deleted.")


def add_subscribers(n_subscribers: int):
    res = list(subsribers_collection.find({}))
    if res:
        print(f'Before adding there are subscribers: {res}, return...')
        return

    db_objects = []
    for n in range(1, n_subscribers+1):
        imsi = IMSI.format(MCC=MCC, MNC=MNC, MSISDN=str(n).zfill(MSISDN_LENGTH))
        db_obj = deepcopy(SUBSCRIBER_TEMPALTE)
        db_obj['imsi'] = imsi
        db_objects.append(db_obj)
    qres = subsribers_collection.insert_many(db_objects)
    print("inserted:", qres.inserted_ids)

delete_all_subscribers()
# delete_subscriber('001010000000001')
add_subscribers(2000)