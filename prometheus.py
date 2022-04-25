from requests import get

PROMETHEUS_URL = "http://prometheus:9090/api/v1/query"

def query_prometheus(query):
    res = get(PROMETHEUS_URL, params={"query": query}).json()
    if res["status"] != "success":
        raise Exception(res)
    return res["data"]

def query_prometheus_first_value(query):
    res = query_prometheus(query)
    return float(res["result"][0]["value"][1])
