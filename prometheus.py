from requests import get

PROMETHEUS_URL = "http://prometheus:9090/api/v1/query"

def query_prometheus(query):
    res = get(PROMETHEUS_URL, params={"query": query}, timeout=5).json()
    if res["status"] != "success":
        raise Exception(res)
    return res["data"]

def query_prometheus_first_value(query):
    res = query_prometheus(query)
    return float(res["result"][0]["value"][1])

def query_prometheus_map_by(query, attrib="name"):
    res = query_prometheus(query)
    results = {}
    for rtt in res["result"]:
        val = float(rtt["value"][1])
        name = rtt["metric"][attrib]
        results[name] = val

    return results
