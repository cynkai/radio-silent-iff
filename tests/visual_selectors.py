import json
import re


def motion_data(element, kind):
    documents = [frame.proto.srcdoc for frame in element.get("iframe")]
    payloads = [json.loads(re.search(r'<script type="application/json" id="engine-data">(.*?)</script>',
                                    document, re.S).group(1)) for document in documents]
    return [payload["data"] for payload in payloads if payload["kind"] == kind]
